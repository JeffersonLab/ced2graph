# Module of classes for generating graph nodes

import json
import yaml
from mya import Sampler
from ced import *

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
        tree = TypeTree()
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


    # Make a ced.SetPointNode or ced.ReadBackNode from the provided element
    #  element - dictionary containing ced element information
    #  tree - dictionary containing ced hierarchy
    #  config - dictionary containing info for classifying nodes as setpoints or readbacks 
    @staticmethod
    def make_node(element: dict, tree: TypeTree, config: dict):
        # Initialize node as None which is what we'll return if the element does not match
        # a type specified in the config.  This could well happen if the element data came
        # a broad CED query like "BeamElem", but the config file only indicates interest
        # in specific sub-types (Magnet, BPM, etc.)
        node = None

        # Give the node a Sampler instance that it could use to retrieve data
        sampler = Sampler(
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


class ListEncoder(json.JSONEncoder):
    """Helper class for exporting json-encoded node lists""" 

    # Override of the parent method from JSONEncoder to return an encodable data structure for
    # _node_list and for the ced and mya classes that it contains
    def default(self, obj):
        if isinstance(obj, mya.Sampler):
            struct = obj.__dict__
            struct['data'] = obj.data()
            return struct
        if isinstance(obj, ced.Node):
            return obj.__dict__
        if isinstance(obj, ced.SetPointNode):
            return obj.__dict__
        if isinstance(obj, ced.ReadBackNode):
            return obj.__dict__
        if isinstance(obj, pandas.Timestamp):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


