# Module with classes and functions for outputting of graph data sets in the HBG format.
# See https://www.biendata.xyz/hgb/#/about

# Write out a label.dat file at the specified path
# Per https://www.biendata.xyz/hgb/#/about:
#   label.dat: The information of node labels. Each line has (node_id, node_type_id, node_label).
#   For multi-label setting, node_labels are split by comma.
def write_label_dat(path, node_list):
    for item in node_list:
        print(item.node_id, "\t", item.type_name, ','.join(item.attribute_names()))


# Write out a node.dat file at the specified path using data from the specified array index
# Per https://www.biendata.xyz/hgb/#/about:
#   node.dat:The information of nodes. Each line has (node_id, node_name, node_type_id, node_feature).
#   Node features are vectors split by comma.
def write_node_dat(path, node_list, index):
    for item in node_list:
        print(path, "\t", item, "\t", ','.join(item.attribute_values(index)))