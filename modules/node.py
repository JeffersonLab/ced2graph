# Module of classes for generating graph nodes
import sys

import yaml
import re
import json
import pandas
import os
import logging
import datetime
from modules import ced
from modules import mya
import modules.util as util
import modules.hgb as hgb

from modules.filter import macro_substitute
from modules.filter import make as makeFilter
from modules.filter import FilterException

# A dictionary that provides an attribute name for the PV that is represented by an element's unadorned
# EPICSName.  The defaults below should be updated at runtime with config file data.
default_attributes = {
    'BCM': 'Current',
    'BPM': 'WireSum',
    'IonPump': 'Vacuum',
}

# The list of signals for the master node to be linked to all setpoints.
# An empty list signifies a master node does not exist.
master = []

def has_master():
    return len(master) > 0

class Node():
    """Class for merging CED element and Mya archive data to use as basis of a Neural Network Graph Node """

    # Instantiate the object
    def __init__(self, element: dict, epics_fields: list, sampler: mya.Sampler, modifiers: dict = None):
        self.element = element
        self.epics_fields = epics_fields
        self.epics_fields.sort()
        self.sampler = sampler
        self.sampler.pv_list = self.pv_list()
        if modifiers is None:
            modifiers = {}
        self.modifiers = modifiers
        self.data = []  # Stores array of timestamped data sets from mya
        self.links = []  # Stores links to downstream nodes to use when building graph edges
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
            pv_list.append(self.pv_name(self.epics_name(), field))
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
            if re.match(r'^VIP0L04(A|20|30|40|50|B)$', self.name()):
                return f'{epics_name}LOG'
            # An empty field means the naked EPICSName should be treated as a PVName
            return epics_name
        else:
            return f'{epics_name}{field}'

    # Retrieve PV values using the available data sampler
    # TODO stash the data keyed by timestamp for most efficient retrieval
    def pv_data(self):
        # If data not already retrieved, do that first
        if not self.data:
            self.sampler.pv_list = self.pv_list()
            # Try to optimize data fetching
            if (isinstance(self, SetPointNode)):
                self.sampler.strategy = 's'
            else:
                self.sampler.strategy = 'n'
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
    # TODO replace with TypeInfo invocation
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
    # The function will apply any applicable calculations from the modifiers
    # dictionary to the returned values
    def epics_attribute_values(self, index):
        attribute_values = []
        for field in self.epics_fields:
            for value in self.pv_data_at_index(index):
                pv_name = list(value.keys())[0]
                if pv_name == self.pv_name(self.epics_name(), field):
                    attribute_values.append(self.modified_epics_value(pv_name, value[pv_name]))
        return attribute_values

    # If necessary, apply calculations from the modifiers dictionary to the provided pv_value
    def modified_epics_value(self, pv_name, pv_value):
        if pv_name in self.modifiers.keys() and pv_value != '<undefined>':
            expr = macro_substitute(pv_name, pv_value, self.modifiers[pv_name])
            return str(eval(expr))
        else:
            return str(pv_value)

    # Return the node's attributes
    # The attributes include ced attributes which are single-valued and the
    # epics data attributes which come from an array of values at the specified index.
    def attribute_values(self, index):
        return self.ced_attribute_values() + self.epics_attribute_values(index)
    # TODO replace with TypeInfo invocation
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

# Nodes that represent readbacks
class ReadBackNode(Node): pass

# Nodes that represent setpoints
class SetPointNode(Node): pass

# The special master setpoint nodes
class MasterNode(SetPointNode):
    def __init__(self, sampler: mya.Sampler):
        # Pseudo CED element
        element = {
            "name": "",
            "type" : "MasterNode",
            "properties": [],
        }
        super().__init__(element,master,sampler)
        self.data = sampler.data()
        self.type_name = 'MasterNode'

    # The node's name
    def name(self):
        return self.type_name

    # Override Node::extended_links
    def extended_links(self, distance: int) -> list:
        # The Master Node links to all setpointnodes, so extended_links will never vary.
        # It will always be the same as links.
        return self.links

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
        tree.tree = json.loads(tree_data)  # parses file into dict
        # Read in node data
        with open(nodes_file, 'r') as nodefile:
            node_data = nodefile.read()
        elements_info = json.loads(node_data)  # parses file into dict

        # Make vanilla list of nodes first
        nodes = list()
        node_id = 0
        for item in elements_info:
            if (item['type_name'] == 'MasterNode'):
                sampler = mya.Sampler(mya.date_ranges(config), config['mya']['global'])
                sampler.set_data(item['sampler']['data'])
                node = MasterNode(sampler)
            else:
                node = List.make_node(item['element'], tree, config, mya.date_ranges(config))
            if (node):
                # By setting the node's data below, we preclude the need
                # for a call to mya to load it later.
                node.sampler.set_data(item['sampler']['data'])
                # Assign id values based on order of encounter                
                node.node_id = node_id
                nodes.append(node)
                node_id += 1

        return nodes

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

    # Builds and returns a dictionary of info about the types in node_list.
    # Dictionary is keyed by type_name and has the fields "id", "labels", and "count".
    # The id value gets assigned to each type in the order it is encountered.
    # The count tallies how many instance of each type.
    @staticmethod
    def type_map(node_list) -> dict:
        type_map = {}
        i = 0
        for item in node_list:
            if item.type_name not in type_map:
                type_map[item.type_name] = {
                    'id': i,
                    'labels': item.attribute_names(),
                    'count': 1
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
    def make_node(element: dict, tree: ced.TypeTree, config: dict, dates: list):
        # Initialize node as None which is what we'll return if the element does not match
        # a type specified in the config.  This could well happen if the element data came
        # a broad CED query like "BeamElem", but the config file only indicates interest
        # in specific sub-types (Magnet, BPM, etc.)
        node = None

        # Give the node a Sampler instance that it could use to retrieve data
        sampler = mya.Sampler(dates)

        if 'modifiers' in config['nodes']:
            modifiers = config['nodes']['modifiers']
        else:
            modifiers = {}

        # Attempt to match the type of the element to the types specified in the
        # config to determine whether to instantiate as ReadBack or SetPoint node variety
        # Important: we will only assign the fields of the first matched type.
        if 'setpoints' in config['nodes']:
            for type_name, fields in config['nodes']['setpoints'].items():
                if not node and tree.is_a(type_name, element['type']):
                    node = SetPointNode(element, fields, sampler, modifiers)
                    node.type_name = type_name  # Assign type name that matched
                    break
        if 'readbacks' in config['nodes']:
            for type_name, fields in config['nodes']['readbacks'].items():
                if not node and tree.is_a(type_name, element['type']):
                    node = ReadBackNode(element, fields, sampler, modifiers)
                    node.type_name = type_name  # Assign type name that matched
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
            # The master node is special and must be linked to all ensuing setpoint nodes
            if isinstance(current_node, MasterNode):
                current_node.links = list(filter(lambda x: isinstance(x, SetPointNode), working_list))
                current_node = working_list.pop(0)
                current_node.links = []
                continue  # Do not fall through to regular SetPointNode processing
            # For regular nodes, we need the next node as well as the current one
            next_node = working_list.pop(0)
            if isinstance(current_node, SetPointNode):
                current_node.links.append(next_node)    # Node following a set point is always linked
            if isinstance(next_node, SetPointNode):
                current_node = next_node
                current_node.links = []
            if len(working_list) < 1:
                break

    # Write out the node.dat, link.dat, meta.dat, and info.dat for each sampled timestamp
    @staticmethod
    def write_data_sets(global_data: list, node_list: list, config: dict, output_dir):
        i = 0
        valid_indexes = []
        filter = makeFilter(config['nodes']['filter'])
        # We expect that the global data was sampled at the same intervals as the node data,
        # so when we find a row we want to keep while looping through the global data, we will
        # have nodes data for the same time period at the at the identical array index.
        # for data in global_data:
        for data in util.progressBar(global_data, prefix='Write to Disk:', suffix='', length=60):
            try:
                if filter.passes(data):
                    # For compatibility with older config files which didn't have it,
                    # we must check for existance of the structure key.  If it's missing we
                    # will default to the original tree-style output.
                    if 'structure' in config['output'] and config['output']['structure'] == 'directory':
                        directory = hgb.dir_from_date(output_dir, data['date'])
                    else:
                        directory = hgb.path_from_date(output_dir, data['date'],
                                                       minutes=config['output']['minutes'],
                                                       seconds=config['output']['seconds'])
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    hgb.write_meta_dat(directory, config, node_list)
                    hgb.write_node_dat(directory, config, node_list, i)
                    hgb.write_link_dat(directory, node_list, config['edges']['connectivity'])
                    hgb.write_info_dat(directory, config, node_list)
                    List.write_global_data_values(directory, data)   # data is global_data at current date
            except FilterException as err:
                # The details of RuntimeErrors are stored in the args attribute, which is a list.
                logging.info(data['date'] + ' ' + err.args[0])
            i += 1

    # Write out a globals.json file at the specified path
    @staticmethod
    def write_global_data_values(path, global_data):

        # First we simplify the data structure
        global_dict = {}
        for item in global_data['values']:
            for key in item.keys():
                global_dict[key] = item[key]
        # Then we write simplified version to a file
        file_name = os.path.join(path, 'globals.json')
        f = open(file_name, 'w')
        json.dump(global_dict, f, indent=2)
        f.close()

class ListEncoder(json.JSONEncoder):
    """Helper class for exporting json-encoded node lists"""

    # Override of the parent method from JSONEncoder to return an encodable data structure for
    # _node_list and for the ced and mya classes that it contains
    def default(self, obj):
        if isinstance(obj, mya.Sampler):
            return {
                'dates': obj.dates,
                'pv_list': obj.pv_list,
                'data': obj._data,
            }
        if isinstance(obj, Node):
            return {
                'element': obj.element,
                'type_name': obj.type_name,
                'epics_fields': obj.epics_fields,
                'sampler': obj.sampler,
            }
        if isinstance(obj, pandas.Timestamp):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        
        if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
                
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

# Information about the types of nodes
class TypeInfo():

    # Instantiate the object
    def __init__(self, config: dict):
        self.config = config

    def has_master(self):
        return 'master' in self.config['nodes'].keys()

    def has_setpoints(self):
        return 'setpoints' in self.config['nodes'].keys()

    def has_setpoint(self, type_name):
        return self.has_setpoints() and type_name in self.config['nodes']['setpoints']

    def has_readbacks(self):
        return 'readbacks' in self.config['nodes'].keys()

    def has_readback(self, type_name):
        return self.has_readbacks() and type_name in self.config['nodes']['readbacks']

    def has_defaults(self):
        return 'default_attributes' in self.config['nodes'].keys()

    def has_default(self, type_name):
        return self.has_defaults() and type_name in self.config['nodes']['default_attributes']

    # Fetches the list of attributes for a type as written in the config file
    def config_attribute_names(self, type_name) -> list:
        if  type_name == 'MasterNode' and self.has_master():
            return self.config['nodes']['master']
        if  self.has_setpoint(type_name):
            return self.config['nodes']['setpoints'][type_name]
        if  self.has_readback(type_name):
            return self.config['nodes']['readbacks'][type_name]
        raise RuntimeError(f'No such type in config  {type_name}')



    # Fetches the attribute labels to be used for reporting
    def type_labels(self, type_name):
        # Attempt to substitute a default label for any instances where empty string
        # was used as the attribute name.  The empty string convention is used when
        # the EpicsName without field modifiers was desired.
        labels = list(map(lambda attr: self.config['nodes']['default_attributes'][type_name] \
            if attr == '' and self.has_default(type_name) \
            else attr, self.config_attribute_names(type_name)))
        if '' in labels:
            raise RuntimeError(f'No default attribute labels configured for {type_name}')
        return labels

    # Returns a dictionary of the types and their labels by the order in which
    # they are encountered in each group in the config file with the groups
    # ordered as follows:
    #    Master (if present)
    #    Set Points
    #    Readbacks (if present)

    def label_dict(self) -> dict:
        label_dict = {}      # Since python 3.6 keys preserve order of insertion
        if self.has_master():
            label_dict['MasterNode'] = self.config['nodes']['master']
        if self.has_setpoints():
            for type_name in self.config['nodes']['setpoints'].keys():
                label_dict[type_name] = self.type_labels(type_name)
        if self.has_readbacks():
            for type_name in self.config['nodes']['readbacks'].keys():
                label_dict[type_name] = self.type_labels(type_name)
        return label_dict

    # Returns a dictionary for looking up type ID values by name.
    # The ID values in the dictionary are assigned based on the order they
    # are encountered in the label dictionary.
    def type_id_map(self) -> dict:
        type_map = {}
        id = 0
        for key in self.label_dict():
            type_map[key] = {'id': id}  # for compatibility with node.List.type_map
            id = id + 1
        return type_map