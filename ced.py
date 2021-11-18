import json
import requests
from datetime import datetime, timedelta
import pandas



# Module of classes for interacting with CED Web API to fetch data.

# The base URL for accessing CED
import mya

url = "https://ced.acc.jlab.org/"


class Inventory:
    """Class to query the CED Web API and retrieve a list of elements by zone and type"""

    # The base URL for the API
    url = url + '/inventory'

    # Instantiate the object
    #   zone is the CED zone name to query
    #   types is one or more CED Type names to retrieve
    #   properties is the property names to be retrieved default: ['S','EPICSName']
    def __init__(self, zone: str, types: list, properties: list = None):
        if properties is None:
            properties = ['S', 'EPICSName']
        self.zone = zone
        self.types = types
        self.properties = properties

    # Return a dictionary containing the query parameters to be used when making API call.
    def queryParams(self) -> dict:
        return {
            'p': self.properties,
            'z': self.zone,
            't': self.types,
            'r': 1,
            's': 'S',
            'out': 'json'
        }

    # Query CED Web API and return the resulting array of elements.
    # Throws if server response cannot be parsed as json.
    def elements(self) -> dict:
        try:
            # Set verify to False because of jlab MITM interference
            response = requests.get(self.url, self.queryParams(), verify=False)
            data_dictionary = response.json()
            if data_dictionary['stat'] == 'ok':
                return data_dictionary['Inventory']['elements']
            else:
                raise RuntimeError(data_dictionary['message'])

        except json.JSONDecodeError:
            print("Oops!  Invalid JSON response. Check request parameters and try again.")
            raise   # rethrow the error


class TypeTree:
    """Class to query the CED Web API to obtain the types hierarchy"""

    # The base URL for the API
    url = "https://ced.acc.jlab.org/api/catalog/type-tree"

    # Instantiate the object
    def __init__(self):
        self.tree = {}

    # Retrieve Type tree data from the server and store it in self.tree
    def _populate_tree(self):
        # Set verify to False because of jlab MITM interference w/SSL
        response = requests.get(self.url, verify=False)
        self.tree = response.json()

    # Receive notification of access to self.tree so that it can be populated
    # if necessary
    def _notify_access(self):
        if not self.tree:
            self._populate_tree()

    # Answer if the type2 is a descendant (or identical) type as type1 based on CED hierarchy.
    #
    # Examples:
    #   is_a('IOC','IOC')        # true
    #   is_a('IOC','PC104')      # true
    #   is_a('Magnet','IPM1L02') # false
    #
    # Return: boolean
    def is_a(self, type1, type2):
        self._notify_access()
        found, lineage = self.lineage(type2)
        if not found:
            raise RuntimeError(type2 + " Not found in CED hierarchy.")
        else:
            # Be nice and do a case-insensitive comparison
            return type1.upper() in map(lambda x:x.upper(), lineage)

    # Return the list of CED Types in the hierarchy to which the specified type belongs
    #   type_name is the name of the CED Type whose lineage is being retrieved
    #   branch is the hierarchy being searched (defaults to entire tree)
    #   parents is the type_names ancestral to the branch being searched (defaults to empty list)
    #
    # Return (boolean, list)
    def lineage(self, type_name: str, branch: dict = None, parents: list = None):
        self._notify_access()
        # The default behavior is to search the entire tree
        if parents is None:
            parents = []
        if branch is None:
            branch = self.tree

        # Search for the type_name in the current branch by iterating through each top level item
        # in the branch.  When we encounter scalar items, they are leaf nodes and we test them to see
        # if they match the type_name we seek.  When we encounter dictionary items, they are sub-branches
        # and we must descend recursively into into them to continue searching.
        found = False
        lineage = parents.copy()
        for key, value in branch.items():
            lineage.append(key)
            if key.upper() == type_name.upper():
                found = True
            elif isinstance(value, dict):
                found, lineage = self.lineage(type_name, value, lineage)
            if found:
                break
            lineage = parents.copy()  # reset for next iteration
        return found, lineage


class Node:
    """Class for merging CED element and Mya archive data to use as basis of a Neural Network Graph Node """

    # Instantiate the object
    def __init__(self, element: dict, epics_fields: list, sampler: mya.Sampler):
        self.element = element
        self.epics_fields = epics_fields
        self.sampler = sampler
        self.sampler.pv_list = self.pv_list()
        self.data = []

    # Get the name used to construct EPICS PVs.

    # The CED convention is to use the EPICSName property if it exists, otherwise
    # to use the element name.
    def epics_name(self):
        if self.element['properties'] and self.element['properties']['EPICSName']:
            return self.element['properties']['EPICSName']
        else:
            return self.element['name']

    # The list of PV names from which node attributes should be constructed
    def pv_list(self):
       pv_list = []
       for field in self.epics_fields:
           pv_list.append(f'{self.epics_name()}{field}')
       return pv_list

    # Retrieve PV values using the available data sampler
    # TODO stash the data keyed by timestamp for most efficient retrieval
    def pv_data(self):
        # If data not already retrieved, do that first
        if not self.data:
            self.sampler.pv_list = self.pv_list()
            self.data = self.sampler.data()
        # And then give it to the user
        return self.data

    # Retrieve the pv values for a specific timestamp
    def pv_data_at(self, desired_date):
        for item in self.pv_data():
            if pandas.to_datetime(item['date']) == pandas.to_datetime(desired_date):
                return item['values']
        return None

# Nodes that represent setpoints
class SetPointNode(Node): pass

# Nodes that represent readbacks
class ReadBackNode(Node): pass

