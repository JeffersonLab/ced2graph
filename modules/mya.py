import math
from datetime import datetime, timedelta, timezone
import pandas
import requests
import os
import csv
from dateutil.tz import gettz
from types import SimpleNamespace

# Module of classes for interacting with Mya Web API to fetch data.

# The base URL for accessing Mya Web
url = "https://myaweb.acc.jlab.org/"

# The archiver lives in the America/New_York timezone
tz = gettz('America/New_York')

# Custom exception class for errors encountered interacting with myaweb
class MyaException(RuntimeError): pass

# Custom exception class for errors related to date spans
class DateSpanException(RuntimeError): pass

# Obtain a list of date ranges from a file that contains either a single
# timestamp or comma-separated begin, end, interval triplet per line.
def date_ranges_from_file(file):
    # verify the file is readable
    if not os.access(file, os.R_OK):
        raise RuntimeError("Unable to read dates from file ", file)

    dates = []
    with open(file, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            # Single timestamp per line
            if len(row) == 1:
                dates.append({'begin': row[0].strip(), 'end': row[0].strip(), 'interval': '1s'})
            # Date range per line
            if len(row) == 3:
                dates.append({'begin': row[0].strip(), 'end': row[1].strip(), 'interval': row[2].strip()})
    return dates


# Return the a list of date ranges from the various different
# options whereby dates ranges can be specified in the configuration
# dictionary
def date_ranges(config: dict) -> list:
    # A list of date ranges right in the config file.
    if  isinstance(config['mya']['dates'], list):
        return config['mya']['dates']
    # Single date range in the config file that we
    # just wrap as a single item list
    if  isinstance(config['mya']['dates'], dict):
        return [config['mya']['dates']]
    # Dates or date ranges from a file.
    if  isinstance(config['mya']['dates'], str):
        return date_ranges_from_file(config['mya']['dates'])
    return []



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
    throttle = 2500

    # List of date range objects
    dates = []

    # Instantiate the object
    #
    #  dates: a list of date range objects with the fields
    #  {
    #    begin_date is the begin date 'yyyy-mm-dd hh:mm:ss'
    #    end_date is the end date 'yyyy-mm-dd hh:mm:ss'
    #    interval is the time interval at which to sample data points (default: '1h')
    #  }
    #  pv_list is the list of PVs for which values will be fetched (default: empty list)
    #
    def __init__(self, dates: list, pv_list: list = None):
        self.dates = dates
        if pv_list is None:
            pv_list = []
        self.pv_list = pv_list
        self._data = None
        # self.begin_date = pandas.to_datetime(begin_date)
        # self.end_date = pandas.to_datetime(end_date)
        # self.interval = interval
        # if begin_date > end_date:
        #     raise RuntimeError("End date must be after Begin date")

    # Raise a DateException if span is not valid otherwise return true.
    def assert_span_is_valid(self, span):
        if not span.begin_date and span.end_date and span.interval:
            raise DateSpanException("Date ranges must include begin, end, and interval fields")
        if span.begin_date > span.end_date:
            raise DateSpanException("End date must be after Begin date")
        return True

    # Get the number of interval-size steps between begin and end dates of the span
    def total_steps(self, span):
        return self.steps_between(span.begin_date, span.end_date, span.interval)

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
    def steps_per_chunk(self, begin_date, end_date, interval):
        max_steps = math.floor(self.throttle / len(self.pv_list))
        remaining_steps = self.steps_between(begin_date, end_date, interval)
        return remaining_steps if remaining_steps <= max_steps else max_steps


    # Return a dictionary containing the query parameters to be used when making API call.
    def queryParams(self, span) -> dict:
        return {
            'b': datetime.strftime(span.begin_date, '%Y-%m-%d %X'),
            's': span.interval,
            'n': self.total_steps(span),
            'm': self.deployment,
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
            self._data = []
            for date_range in self.dates:
                span = self.date_span(date_range)
                current_date = span.begin_date
                while current_date <= span.end_date:
                    steps = self.steps_per_chunk(current_date, span.end_date, span.interval)
                    self._data.extend(self.get_data_chunk(current_date, steps, span))
                    current_date = current_date + pandas.to_timedelta(span.interval) * steps
        
        return self._data

    # Make a SimpleNamespace object that contains begin_date, end_date, interval
    # from a dictionary containing begin, end, interval where begin_date and end_date
    # are datetime objects constructed from the begin and end strings.
    def date_span(self, date_range: dict):
        span = SimpleNamespace(**date_range)
        span.begin_date = pandas.to_datetime(span.begin)
        span.end_date = pandas.to_datetime(span.end)
        return span

    # Set the local data copy.
    # This might be done usefully during testing in order to use data from a file rather than
    # fetching it from the archiver which may not be available in the test environment.
    #@data.setter
    def set_data(self, val):
        if not isinstance(val, list):
             raise TypeError("Expected: list")
        self._data = val

    # Return a steps sized chunk of data commencing at begin_date
    def get_data_chunk(self, begin_date: datetime, steps: int, span):
        # The queryParams method returns by default parameters to fetch the entire data set
        # so here we override the necessary keys so that we can fetch desired subset
        params = self.queryParams(span)
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
