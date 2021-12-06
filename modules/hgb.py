# Module with classes and functions for outputting of graph data sets in the HBG format.
# See https://www.biendata.xyz/hgb/#/about

import os
import pandas
import modules.node as node

# Write out a label.dat file at the specified path
# Per https://www.biendata.xyz/hgb/#/about:
#   label.dat: The information of node labels. Each line has (node_id, node_type_id, node_label).
#   For multi-label setting, node_labels are split by comma.
def write_label_dat(path, node_list):
    file_name = os.path.join(path, 'label.dat')
    f = open(file_name, 'w')
    for item in node_list:
        print(item.node_id, "\t", item.type_name, ','.join(item.attribute_names()), file=f)
    f.close()    


# Write out a node.dat file at the specified path using data from the specified array index
# Per https://www.biendata.xyz/hgb/#/about:
#   node.dat:The information of nodes. Each line has (node_id, node_name, node_type_id, node_feature).
#   Node features are vectors split by comma.
def write_node_dat(path, node_list, index):
    file_name = os.path.join(path, 'node.dat')
    f = open(file_name, 'w')
    for item in node_list:
        print(item, "\t", ','.join(item.attribute_values(index)), file=f)
    f.close()    

# Write out a link.dat file at the specified path using data from the specified array index
# Per https://www.biendata.xyz/hgb/#/about:
#   link.dat: The information of edges. Each line has (node_id_source, node_id_target, edge_type_id, edge_weight).
# TODO Use appropriate type and weight
def write_link_dat(path, node_list):
    file_name = os.path.join(path, 'link.dat')
    f = open(file_name, 'w')
    for item in node_list:
        if (isinstance(item, node.SetPointNode)):
            for target in item.links:
                print(item.node_id, '\t', target.node_id, '\t','0\t1', file=f)  # Hard-code type and weight for now
    f.close()            


# Return a path tree of Base/Year/Month/Day/Hour using the correct path separator for the current OS
def path_from_date(base_path, target_date):
    date = pandas.to_datetime(target_date)
    return os.path.join(base_path, date.strftime("%Y"), date.strftime("%m"), date.strftime("%d"), date.strftime("%H"))

