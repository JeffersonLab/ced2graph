import math
from datetime import datetime, timedelta
import pandas
import json
import requests

# Module of classes for interacting with Mya Web API to fetch data.

# The base URL for accessing Mya Web
url = "https://myaweb.acc.jlab.org/"


class Sampler:
    """Class to query the Mya Web API and retrieve values for a list of PVs"""

    # The base URL for the API
    url = url + 'mySampler/data'

    # Instantiate the object
    #
    #  begin_date is the begin date 'yyyy-mm-dd hh:mm:ss'
    #  end_date is the end date 'yyyy-mm-dd hh:mm:ss'
    #  interval is the time inteval at which to sample data points (default: '1h')
    #  pv_list is the list of PVs for which values will be fetched (default: empty list)
    #
    def __init__(self, begin_date: str, end_date: str, interval: int = None, pv_list: list = None):
        if interval is None:
            interval = '1h'
        if pv_list is None:
            pv_list = []
        self.pv_list = pv_list
        self.begin_date = pandas.to_datetime(begin_date)
        self.end_date = pandas.to_datetime(end_date)
        self.interval = interval
        if begin_date >= end_date:
            raise RuntimeError("End date must be after Begin date")

    # Get the number of interval-size steps between our begin and end dates
    def number_of_steps(self):
        return self.steps_between(self.begin_date, self.end_date, self.interval)

    # Get the number of interval-size steps between the specified begin and end dates
    def steps_between(self, begin_date, end_date, interval):
        time_difference = abs(end_date - begin_date)
        time_difference_in_hours = time_difference / pandas.to_timedelta(interval)
        return math.floor(time_difference_in_hours)

    # Return a dictionary containing the query parameters to be used when making API call.
    def queryParams(self) -> dict:
        return {
            'b': datetime.strftime(self.begin_date, '%Y-%m-%d %X'),
            's': self.interval,
            'n': self.number_of_steps(),
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
    def data(self) -> dict:
        # Throw an error if no channels have been set
        if not self.pv_list:
            raise RuntimeError("No channels to fetch")

        # Set verify to False because of jlab MITM interference
        response = requests.get(self.url, self.queryParams(), verify=False)

        # Example Request URL:
        #  https://myaweb.acc.jlab.org/mySampler/data?b=2021-11-10&s=1h&n=2&m=ops&channels=MQB0L09.BDL+MQB0L10.BDL
        # print(response.url)       # For debugging -- what URL actually used?

        if response.status_code != requests.codes.ok:
            raise RuntimeError("Mya web server returned an error status code")


        return response.json()



