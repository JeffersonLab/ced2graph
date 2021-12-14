# Module of classes for generating graph nodes

import yaml
import re
import json
import pandas
from modules import ced
from modules import mya

# A dictionary that provides an attribute name for the PV that is represented by an element's unadorned
# EPICSName.  The defaults below should be updated at runtime with config file data.
default_attributes = {
    'BCM': 'Current',
    'BPM': 'WireSum',
    'IonPump': 'Vacuum',
}

class Node():
    """Class for merging CED element and Mya archive data to use as basis of a Neural Network Graph Node """

    # Instantiate the object
    def __init__(self, element: dict, epics_fields: list, sampler: mya.Sampler):
        self.element = element
        self.epics_fields = epics_fields
        self.epics_fields.sort()
        self.sampler = sampler
        self.sampler.pv_list = self.pv_list()
        self.data = []      # Stores array of timestamped data sets from mya
        self.links = []     # Stores links to downstream nodes to use when building graph edges
        self.node_id = None
        self.type_name = None


    # Get the name used to construct EPICS PVs.
    def epics_name(self):
        # The CED convention is to use the EPICSName property if it exists, otherwise
        # to use the element name.
        if 'properties' in self.element and 'EPICSName' in self.element['properties']:
            return self.element['properties']['EPICSName']
        else:
            return self.element['name']

    # The node's name
    def name(self):
        return self.element['name']

    # The list of PV names from which node attributes should be constructed
    def pv_list(self):
       pv_list = []
       for field in self.epics_fields:
           pv_list.append(self.pv_name(self.epics_name(),field))
       pv_list.sort()
       return pv_list

    # Return a PV name formed from the given base epics name field
    # Handle special cases such as XPSET8, BCMs, certain IonPumps
    def pv_name(self, epics_name, field):
        if field == 'XPSET8':
            # belongs to zone, so remove final char that designates cavity
            return f"{epics_name[:-1]}{field}"
        elif field == "":
            # BCMs are case-by-case inconsistent
            if self.name() == 'IBC0L02':
                return 'IBC0L02Current'
            if self.name() == 'IBC0R08':
                return 'IBC0R08CRCUR1'
            if re.match(r'^VIP0L04(A|20|30|40|50|B)$',self.name()):
                print(f"re match {self.name()}")
                return f'{epics_name}LOG'
            # An empty field means the naked EPICSNAme should be treated as a PVName
            return epics_name
        else:
            return f'{epics_name}{field}'


    # Retrieve PV values using the available data sampler
    # TODO stash the data keyed by timestamp for most efficient retrieval
    def pv_data(self):
        # If data not already retrieved, do that first
        if not self.data:
            self.sampler.pv_list = self.pv_list()
            self.data = self.sampler.data()
        # And then give it to the user
        return self.data

    # Retrieve the pv values for a given date and time
    # Note that this method has a problem in that the MyaWeb server sends back string dates
    # which means that during DST "fall back" the 01:00 timestamp is ambiguous.
    def pv_data_at_datetime(self, desired_date):
        for item in self.pv_data():
            if pandas.to_datetime(item['date']) == pandas.to_datetime(desired_date):
                return item['values']
        return None

    # Retrieve the pv values for the specified index position in the data array
    def pv_data_at_index(self, index):
       data = self.pv_data()
       return data[index]['values']

    # Define the string representation of the Node
    #   tab-delimited node_id, node_name, node_type, ced_attributes
    #   where ced_attributes is comma-delimited
    def __str__(self):
        return f"{self.node_id}\t{self.name()}"

    # Return a sorted list of the CED properties usable as attributes.
    # In practice it is all properties requested except EPICSName which is excluded
    def ced_attribute_names(self):
        attribute_names = []
        for attribute in filter(lambda x: x != 'EPICSName', self.element['properties']):
            attribute_names.append(attribute)
        attribute_names.sort()
        return attribute_names

    # Return a sorted list of the CED properties usable as attributes.
    # In practice it is all properties requested except EPICSName which is excluded
    def ced_attribute_values(self):
        attribute_values = []
        for attribute_name in self.ced_attribute_names():
                attribute_values.append(self.element['properties'][attribute_name])
        return attribute_values

    # Return epics-based node attributes for the specified array index
    def epics_attribute_values(self, index):
        attribute_values = []
        for field in self.epics_fields:
            for value in self.pv_data_at_index(index):
                pv_name = list(value.keys())[0]
                if pv_name == self.pv_name(self.epics_name(),field):
                    attribute_values.append(value[pv_name])
        return attribute_values

    # Return the node's attributes
    # The attributes include ced attributes which are single-valued and the
    # epics data attributes which come from an array of values at the specified index.
    def attribute_values(self, index):
        return self.ced_attribute_values() + self.epics_attribute_values(index)

    def attribute_names(self):
        attribute_names = self.ced_attribute_names()
        for field in self.epics_fields:
            if (field != ""):
                attribute_names.append(field)
            elif self.type_name in default_attributes:
                attribute_names.append(default_attributes[self.type_name])
            else:
                raise RuntimeError(f'No default attribute name for {self.type_name}')
        return attribute_names

    # Return a list of ReadBack and SetPoint nodes up to the specified number of SetpointNodes distance away
    def extended_links(self, distance: int) -> list:
        # The links property stores the list of ReadBack and SetPoint nodes up to and including the next
        # SetPointNode, so we just have to append that terminal SetPointNode's links to our own, and those
        # that belong to it, and so on up to the desired distance.
        links = self.links.copy()
        extensions = 1
        while extensions < distance:
            if links:
                # Add links of final Node in current links
                links.extend(links[-1].links)
                extensions += 1
            else:
                break

        return links

# Nodes that represent setpoints
class SetPointNode(Node):pass

# Nodes that represent readbacks
class ReadBackNode(Node):pass


class List():
    """Methods for making and working with lists of ced.Node (and subclasses thereof) objects"""

    # Return a list of nodes read from json files
    #  nodes_file - name of file containing json-encoded ced.Node objects
    #  tree_file - name of file containing json-encoded ced.Tree object
    #  config_file - name of yaml config file 
    @staticmethod
    def from_json(nodes_file: str, tree_file: str, config_file: str):        
        # Read configuration yaml file
        stream = open(config_file, 'r')
        config = yaml.load(stream, Loader=yaml.CLoader)
        # Read in types hierarcy
        with open(tree_file, 'r') as treefile:
            tree_data = treefile.read()
        tree = ced.TypeTree()
        tree.tree = json.loads(tree_data)   # parses file into dict
        # Read in node data
        with open(nodes_file, 'r') as nodefile:
            node_data = nodefile.read()
        elements_info = json.loads(node_data)   # parses file into dict

        # Make vanilla list of nodes first
        nodes = list()
        node_id = 0
        for item in elements_info:
            node = List.make_node(item['element'], tree, config)
            if (node):
                # By setting the node's data below, we preclude the need
                # for a call to mya to load it later.
                node.sampler.set_data(item['sampler']['data'])
                # Assign id values based on order of encounter                
                node.node_id = node_id
                nodes.append(node)
                node_id += 1

        return nodes

    # Returns the list of nodes that remain after applying filter logic
    # TODO use dynamic rather than hard-coded filter logic
    # TODO investigate using @yield
    @staticmethod
    def filter(node_list, global_data):
        filtered = []
        for i,data in enumerate(global_data):
            current_filter_value = mya.get_pv_value(data['values'], 'IBC0R08CRCUR1')
            if current_filter_value and float(current_filter_value) > 0:
                filtered.append(node_list[i])
        return filtered

    # Returns a dictionary with information about how many instances of each type
    # of node were encountered in node_list
    @staticmethod
    def type_count(node_list) -> dict:
        type_dict = {}
        for item in node_list:
            if item.type_name in type_dict:
                type_dict[item.type_name] += 1
            else:
                type_dict[item.type_name] = 1
        return type_dict

    # Builds and returns a dictionary of info about the each types in node_list.
    # Dictionary is keyed by type_name and has the fields "id" and "labels".
    # The id value gets assigned to each type in the order it is encountered.
    @staticmethod
    def type_map(node_list) -> dict:
        type_map = {}
        i=0
        for item in node_list:
            if item.type_name not in type_map:
                type_map[item.type_name] = {
                    'id' : i,
                    'labels' : item.attribute_names(),
                    'count' : 1
                }
                i += 1
            else:
                type_map[item.type_name]['count'] += 1

        return type_map

    # Make a ced.SetPointNode or ced.ReadBackNode from the provided element
    #  element - dictionary containing ced element information
    #  tree - dictionary containing ced hierarchy
    #  config - dictionary containing info for classifying nodes as setpoints or readbacks 
    @staticmethod
    def make_node(element: dict, tree: ced.TypeTree, config: dict):
        # Initialize node as None which is what we'll return if the element does not match
        # a type specified in the config.  This could well happen if the element data came
        # a broad CED query like "BeamElem", but the config file only indicates interest
        # in specific sub-types (Magnet, BPM, etc.)
        node = None

        # Give the node a Sampler instance that it could use to retrieve data
        sampler = mya.Sampler(
            config['mya']['begin'],
            config['mya']['end'],
            config['mya']['interval'],
        )

        # Attempt to match the type of the element to the types specified in the
        # config to determine whether to instantiate as ReadBack or SetPoint node variety
        # Important: we will only assign the fields of the first matched type.
        for type_name, fields in config['nodes']['setpoints'].items():
            if not node and tree.is_a(type_name, element['type']):
                node = SetPointNode(element, fields, sampler)
                node.type_name = type_name      # Assign type name that matched
                break
        for type_name, fields in config['nodes']['readbacks'].items():
            if not node and tree.is_a(type_name, element['type']):
                node = ReadBackNode(element, fields, sampler)
                node.type_name = type_name      # Assign type name that matched
                break

        return node        

    # Link downstream nodes to each ReadbackNode within node_list.
    # The connectivity built here is just up to and including the next ReadBackNode.
    # Later when writing out edge files, the connectivity can be extended by simply
    # appending the links of terminal ReadBackNode elements to those of the initial
    # ReadbackNode to any desired extent.
    @staticmethod
    def populate_links(node_list):
        # Begin with a copy of the original list whose elements we can pop fron the front
        working_list = node_list.copy()
        current_node = working_list.pop(0)
        current_node.links = []
        # The while loop below fills the links list of every SetPoint node with references
        # to all the ensuing nodes up to and including the next SetPoint Node.
        while current_node:
            next_node = working_list.pop(0)
            if isinstance(current_node, SetPointNode):
                # print(f"append {next_node.name()} to {current_node.name()}")
                current_node.links.append(next_node)
            if isinstance(next_node, SetPointNode):
                current_node = next_node
                current_node.links = []
            if len(working_list) < 1:
                break

class ListEncoder(json.JSONEncoder):
    """Helper class for exporting json-encoded node lists""" 

    # Override of the parent method from JSONEncoder to return an encodable data structure for
    # _node_list and for the ced and mya classes that it contains
    def default(self, obj):
        if isinstance(obj, mya.Sampler):
            return {
                'interval'   : obj.interval,
                'pv_list'    : obj.pv_list,
                'data'       : obj._data,
                'begin_date' : obj.begin_date,   
                'end_date'   : obj.end_date
            }
        if isinstance(obj, Node):
            return {
                'element': obj.element,
                'type_name' : obj.type_name,
                'epics_fields' : obj.epics_fields,
                'sampler' : obj.sampler,
            }
        if isinstance(obj, pandas.Timestamp):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)
