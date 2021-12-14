#
# Script that
#  1) reads yaml config gile
#  2) fetches CED elements defined in config file
#  3) fetches Mya data for CED elements as specified in config file
#  4) fetches global Mya data
#  5) - for each interval specified in config file that passes filters:
#  5)   - Output nodes in HBG file format
#  6)   - Build edges and output in HBG format

import yaml
import argparse
import os
import sys
from modules.ced import *
import modules.hgb as hgb
import modules.mya as mya
import modules.node as node
from modules.util import progressBar


# Suppress the warnings we know will be generated by having to
# bypass SSL verification because of the annoying JLAB MITM
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# The file names that will be used when saving the data fetched from
# CED and MYA as json and when reading that data back in lieu of
# accessing those services.  The primary purpose of these files
# is for development/testing/debugging
tree_file = 'tree.json'
nodes_file = 'nodes.json'
globals_file = 'global.json'

# the list of nodes that will be used to output graph data
node_list = []

# the global data that will be used for filtering
global_data = []

# CED Type hierarchy tree for using to match specific retrieved types
# to the possibly more generic (i.e. parent) type names encountered in the config dictionary.
# For example to determine that an element whose type is QB is also a "Quad" and a "Magnet"
tree = TypeTree()



# Define the program's command line arguments and build a parser to process them
def make_cli_parser():
    parser = argparse.ArgumentParser(description='Command Line Options')
    parser.add_argument("-c", type=str, dest='config_file', default="config.yaml",
                        help="Name of a yaml formatted config file")
    parser.add_argument("-d", type=str, dest='output_dir', default=".",
                        help="Directory where generated graph file hierarchy will be written")
    parser.add_argument("--read-json", action='store_true',
                        help = f"Read data from {tree_file}, {nodes_file}, and {globals_file} instead of CED and Mya")
    parser.add_argument("--save-json", action='store_true',
                        help = f"Save fetched data in {tree_file}, {nodes_file}, and {globals_file}")

    return parser





try:
    # Access the command line arguments
    args = make_cli_parser().parse_args()

    # Before doing any time-consuming work, verify the output dir is writable
    if not os.access(args.output_dir, os.X_OK | os.W_OK):
        sys.exit('Unable to write to output directory ' + args.output_dir)


    # Read configuration yaml file
    stream = open(args.config_file, 'r')
    config = yaml.load(stream, Loader=yaml.CLoader)

    # See if the type tree data should be read from file rather than retrieved from CED
    if args.read_json:
        with open(tree_file, 'r') as tree_file_handle:
            data = tree_file_handle.read()
        tree.tree = json.loads(data)  # pre-populate the data so no need to lazy-load later

    # Global data from file or service
    if args.read_json:
        with open(globals_file, 'r') as globals_file_handle:
            data = globals_file_handle.read()
        global_data = json.loads(data)
    else:
        # Retrieve the global PV list
        global_data = mya.Sampler(
            config['mya']['begin'],
            config['mya']['end'],
            config['mya']['interval'],
            config['mya']['global']
        ).data()

    # See if the user wants to load nodes data from file rather than hitting archiver
    if args.read_json:
        node_list = node.List.from_json(nodes_file,tree_file,args.config_file)
    else:  # Use CED and MYA to build nodes list

        # Begin by fetching the desired CED elements
        inventory = Inventory(
            config['ced']['zone'],
            config['ced']['types'],
            config['ced']['properties'],
            config['ced']['expressions']
        )
        elements = inventory.elements()

        # It's important to preserve the order of the elements in the nodeList.
        # We are going to assign each node a node_id property that corresponds to its
        # order in the list beginning at 0.
        node_id = 0
        for element in progressBar(elements, prefix = 'Fetch from mya:', suffix = '', length = 60):
            # Wrap node creating in a try-catch block so that we can simply log problematic nodes
            # without killing the entire effort.
            try:
                item = node.List.make_node(element, tree, config)

                # If no node was created, it means that there was not type match.  This could happen if
                # the CED query was something broad like "BeamElem", but the config file only indicates the
                # desired EPICS fields for specific sub-types (Magnet, BPM, etc.)
                if item:
                    # Load the data now so that we can give user a progressbar
                    item.pv_data()
                    # Assign id values based on order of encounter
                    item.node_id = node_id
                    node_list.append(item)
                    node_id += 1
            except mya.MyaException as err:
                print(err)

    # Link each SetPointNode to its downstream nodes up to and including the next SetPoint.
    node.List.populate_links(node_list)

    # At this point we've got all the data necessary to start writing out data sets
    i = 0
    valid_indexes = []
    # The global data was sampled identically to the node data, so when we find a row we want
    # to keep while looping through it, we know the nodes will have data at the corresponding
    # row index.
    for data in global_data:
    #for data in progressBar(global_data, prefix = 'Write to Disk:', suffix = '', length = 60):
        # Filter the nodeList by only outputting rows that meet our criteria
        # For the moment we're using hard-coded conditions, but eventually the goal is to
        # do some sort of eval on the filters specified in the yaml config file
        current_filter_value = mya.get_pv_value(data['values'], 'IBC0R08CRCUR1')
        if current_filter_value \
                and current_filter_value != '<undefined>' \
                and float(current_filter_value) > 0:
            directory = hgb.path_from_date(args.output_dir, data['date'])
            if not os.path.exists(directory):
                os.makedirs(directory)
            hgb.write_meta_dat(directory, node_list)
            hgb.write_node_dat(directory, node_list, i)
            hgb.write_link_dat(directory, node_list, config['edges']['connectivity'])
            hgb.write_label_dat(directory, node_list)
        i += 1

    #hgb.write_label_dat('foo', node_list)

    # Save the tree, nodes, and global data list to a file for later use?
    indent = 2
    if args.save_json:
        f = open(nodes_file, "w")
        print("[",file=f)
        i = 0
        for index, item in enumerate(progressBar(node_list, prefix = 'Write Json:', suffix = '', length = 60)):
            json.dump(item, f, cls=node.ListEncoder, indent=indent)
            if index < len(node_list) - 1:
                print(",\n", file=f)
        print("]",file=f)
        f.close()

        f = open(globals_file, "w")
        json.dump(global_data, f, indent=indent)
        f.close()

        f = open(tree_file, "w")
        json.dump(tree.tree, f, indent=indent)
        f.close()

    exit(0)

except json.JSONDecodeError as err:
    print(err)
    print("Oops!  Invalid JSON response. Check request parameters and try again.")
    exit(1)
except RuntimeError as err:
    print("Exception: ", err)
    exit(1)



