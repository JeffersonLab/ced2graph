
# Module of classes for interacting with CED Web API to fetch data.

import json
import requests

# The module-wide base URL for CED web API.
# It can be changed to instead query the LED, UED, etc. alternatives
url = "https://ced.acc.jlab.org"

# The core properties to fetch.
#   EPICSName: necessary to construct EPICS PVNames for many elements
#   S: necessary to calculate distances between elements
properties = ['S', 'EPICSName']

class Inventory:
    """Class to query the CED Web API and retrieve a list of elements by zone and type"""

    # The path to retrieve an inventory of elements
    url = url + '/inventory'

    # Instantiate the object
    #   zone is the CED zone name to query (Ex: Injector)
    #   types is one or more CED Type names to retrieve (Ex: ['Dipole','BPM']
    #   extra_properties is a list of property names to be retrieved
    #                     in addition to the baseline default of ['S','EPICSName']
    #   expressions is a list of CED property filter expressions (like command line -Ex)
    #                      for example ['S > 0.5']
    def __init__(self, zone: str, types: list, extra_properties: list = None, expressions: list = None):
        if extra_properties:
            # Combine base properties with extra_properties, removing duplicates
            self.properties = list(set(properties + extra_properties))
        else:
            self.properties = properties

        self.zone = zone
        self.types = types
        self.expressions = expressions

    # Return a dictionary containing the query parameters to be used when making API call.
    def queryParams(self) -> dict:
        query =  {
            'p': self.properties,
            'z': self.zone,
            't': self.types,
            'r': 1,
            's': 'S',
            'out': 'json'
        }
        if self.expressions:
            query['Ex'] = self.expressions
        return query

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
            print(response.url)
            print("Oops!  Invalid JSON response. Check request parameters and try again.")
            raise   # rethrow the error
        except RuntimeError:
            print(response.url)
            raise


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

