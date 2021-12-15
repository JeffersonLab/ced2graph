# Module with classes and functions for outputting of graph data sets in the HBG format.
# See https://www.biendata.xyz/hgb/#/about

import os
import pandas
import modules.node as node

# Write out an info.dat file at the specified path
# Per https://www.biendata.xyz/hgb/#/about:
#   label.dat: The information of node labels. Each line has (node_id, node_type_id, node_label).
#   For multi-label setting, node_labels are split by comma.
def write_info_dat(path, node_list):
    file_name = os.path.join(path, 'info.dat')
    f = open(file_name, 'w')
    print("\t".join(['TYPE', 'NAME', 'LABELS']), file=f)
    for key, item in node.List.type_map(node_list).items():
        print(item['id'], "\t", key, ','.join(item['labels']), file=f)
    f.close()    


# Write out a node.dat file at the specified path using data from the specified array index
# Per https://www.biendata.xyz/hgb/#/about:
#   node.dat:The information of nodes. Each line has (node_id, node_name, node_type_id, node_feature).
#   Node features are vectors split by comma.
def write_node_dat(path, node_list, index):
    type_map = node.List.type_map(node_list)
    file_name = os.path.join(path, 'node.dat')
    f = open(file_name, 'w')
    print("\t".join(['NODE','NAME','TYPE','VALUES']), file=f)
    for item in node_list:
        print(item, "\t", type_map[item.type_name]['id'], "\t", ','.join(item.attribute_values(index)), file=f)
    f.close()    

# Write out a link.dat file at the specified path using data from the specified array index
# Per https://www.biendata.xyz/hgb/#/about:
#   link.dat: The information of edges. Each line has (node_id_source, node_id_target, edge_type_id, edge_weight).
# TODO implement node weighting
def write_link_dat(path, node_list, distance = 1):
    file_name = os.path.join(path, 'link.dat')
    f = open(file_name, 'w')
    print("\t".join(['START', 'END', 'LINK_TYPE', 'LINK_WEIGHT']), file=f)
    for item in node_list:
        if (isinstance(item, node.SetPointNode)):
            for target in item.extended_links(distance):
                # Hard-code type and weight for now
                print(item.node_id, '\t', target.node_id, '\t','0\t1', file=f)
    f.close()

# Write out a meta.dat file at the specified path
# The file contains summary data such as the number of each type of node
def write_meta_dat(path, node_list):
    type_map = node.List.type_map(node_list)
    file_name = os.path.join(path, 'meta.dat')
    f = open(file_name, 'w')
    print('Total Nodes:', "\t", len(node_list), file=f)
    for type_name, data in type_map.items():
        print(f"Node_Type_{data['id']}:", "\t", data['count'], file=f)
    f.close()

# Return a path tree of Base/Year/Month/Day/Hour using the correct path separator for the current OS
def path_from_date(base_path, target_date):
    date = pandas.to_datetime(target_date)
    return os.path.join(base_path, date.strftime("%Y"), date.strftime("%m"), date.strftime("%d"), date.strftime("%H"))
