import math
from datetime import datetime, timedelta, timezone
import pandas
import requests
from dateutil.tz import gettz

# Module of classes for interacting with Mya Web API to fetch data.

# The base URL for accessing Mya Web
url = "https://myaweb.acc.jlab.org/"

# The archiver lives in the America/New_York timezone
tz = gettz('America/New_York')

# Custom exception class for errors encountered interacting with myaweb
class MyaException(RuntimeError): pass


class Sampler:
    """Class to query the Mya Web API and retrieve values for a list of PVs"""

    # The base URL for the API
    url = url + 'mySampler/data'

    # The mya deployment to use.
    # Most recent data in ops
    # older data in history
    deployment = "history"

    # Limit the number of data points (num pvs * steps) to be fetched at each server request.
    # This number must be larger than the number of PVs to be fetched.
    throttle = 10000

    # Instantiate the object
    #
    #  begin_date is the begin date 'yyyy-mm-dd hh:mm:ss'
    #  end_date is the end date 'yyyy-mm-dd hh:mm:ss'
    #  interval is the time interval at which to sample data points (default: '1h')
    #  pv_list is the list of PVs for which values will be fetched (default: empty list)
    #
    def __init__(self, begin_date: str, end_date: str, interval: str = None, pv_list: list = None):
        if interval is None:
            interval = '1h'
        if pv_list is None:
            pv_list = []
        self.pv_list = pv_list
        self._data = None
        self.begin_date = pandas.to_datetime(begin_date)
        self.end_date = pandas.to_datetime(end_date)
        self.interval = interval
        if begin_date > end_date:
            raise RuntimeError("End date must be after Begin date")

    # Get the number of interval-size steps between t begin and end dates
    def total_steps(self):
        return self.steps_between(self.begin_date, self.end_date, self.interval)

    # Get the number of interval-size steps between the specified begin and end dates
    @staticmethod
    def steps_between(begin_date, end_date, interval):
        # When the user has specified points in time rather than ranges,
        # begin and end will be the same and we can simply and quickly return 1
        if begin_date == end_date:
            return 1

        # To account for days without 24 hours we must create timezone
        # aware timestamps from the specified dates
        begin_datetime = pandas.Timestamp(pandas.to_datetime(begin_date), tzinfo=tz)
        end_datetime = pandas.Timestamp(pandas.to_datetime(end_date), tzinfo=tz)
        time_difference = abs( end_datetime - begin_datetime)
        time_differences_of_interval_size = time_difference / pandas.to_timedelta(interval)
        return math.floor(time_differences_of_interval_size)

    # Returns the lesser of max allowed steps or number of steps remaining
    def steps_per_chunk(self, begin_date):
        max_steps = math.floor(self.throttle / len(self.pv_list))
        remaining_steps = self.steps_between(begin_date, self.end_date, self.interval)
        return remaining_steps if remaining_steps <= max_steps else max_steps


    # Return a dictionary containing the query parameters to be used when making API call.
    def queryParams(self) -> dict:
        return {
            'b': datetime.strftime(self.begin_date, '%Y-%m-%d %X'),
            's': self.interval,
            'n': self.total_steps(),
            'm': 'ops',
            'channels': " ".join(self.pv_list)
        }

    # Query CED Web API and return the resulting array of elements.
    #
    # Example JSON response: {"data":[
    #    {"date":"2021-11-10T00:00:00","values":[{"MQB0L09.BDL":"405.921"},{"MQB0L10.BDL":"317.829"}]},
    #    {"date":"2021-11-10T01:00:00","values":[{"MQB0L09.BDL":"405.921"},{"MQB0L10.BDL":"317.829"}]}
    # ]}
    #
    # Throws if server response is not a "success" status code.
    #
    def data(self) -> list:
        # Fetch the pv_data if it hasn't already been retrieved.
        if not self._data:
            # Must have a list of pvs to fetch
            if not self.pv_list:
                raise RuntimeError("No channels to fetch")

            # If the throttle limit is less than the size of the pv list the fetch we're about to do
            # would enter an infinite loop, so we'll raise an error here instead
            if len(self.pv_list) > self.throttle:
                raise RuntimeError("PV list is too large for mya.throttle limit")

            # Accumulate data in chunks to avoid a server timeouts from requesting too much at once.
            date = self.begin_date
            self._data = []
            while date <= self.end_date:
                #print(date)
                steps = self.steps_per_chunk(date)
                self._data.extend(self.get_data_chunk(date, steps))
                date = date + pandas.to_timedelta(self.interval) * steps
        
        return self._data

    # Set the local data copy.
    # This might be done usefully during testing in order to use data from a file rather than
    # fetching it from the archiver which may not be available in the test environment.
    #@data.setter
    def set_data(self, val):
        if not isinstance(val, list):
             raise TypeError("Expected: list")
        self._data = val

    # Return a steps sized chunk of data commencing at begin_date
    def get_data_chunk(self, begin_date: datetime, steps: int):
        # The queryParams method returns by default parameters to fetch the entire data set
        # so here we override the necessary keys so that we can fetch desired subset
        params = self.queryParams()
        params['b'] = datetime.strftime(begin_date, '%Y-%m-%d %X')
        params['n'] = steps

        # Set verify to False because of jlab MITM interference
        response = requests.get(self.url, params, verify=False)

        # Example Request URL:
        #  https://myaweb.acc.jlab.org/mySampler/data?b=2021-11-10&s=1h&n=2&m=ops&channels=MQB0L09.BDL+MQB0L10.BDL
        # print(response.url)       # For debugging -- what URL actually used?

        if response.status_code != requests.codes.ok:
            print(response.url)  # Useful for debugging -- what URL actually used?
            if 'error' in response.json():
                message = response.json()['error']
            else:
                message = f'Mya web server returned error status code {response.status_code}'
            raise MyaException(message)

        # Save the data as an object property
        return response.json()['data']

# Utility function for extracting a value from a list containing key:value dictionaries,
# such as the myaweb server returns for the PV values.
# Expected data structure example:
#       [
#           {key1: value},
#           {key2: value},
#       ]
#
def get_pv_value(data: list, name):
    for value in data:
        pv_name = list(value.keys())[0]
        if pv_name == name:
            return value[pv_name]
    return None