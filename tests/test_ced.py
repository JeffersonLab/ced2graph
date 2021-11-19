# File containing some tests of the ced module.

from ced import *
from mya import Sampler
import json

# Test ability to identify whether an element type is a sub-type of another
def test_is_a():
    # We load hierarchy expected from CED web server from a json file instead
    # and then make our assertions based on it.
    # read file
    with open('type-tree.json', 'r') as treefile:
        data = treefile.read()
    tree = TypeTree()
    tree.tree = json.loads(data)   # parses file into dict

    assert tree.is_a('Magnet','Quad')
    assert not tree.is_a('IOC', 'Dipole')

# Test Node ability to extract correct data for a timestamp
def test_pv_data_at():
    # Even though it won't use it in this test, we need a sampler object
    # in order to construct the Node object we do intend to test
    sampler = Sampler('2021-10-01','2021-10-02')

    # We also need some pretend CED element data
    element = {'type': 'QD', 'name': 'MQD0R05', 'properties': {'S': '80.43605953277998', 'EPICSName': 'MQD0R05'}}

    # And some pretend archiver data
    with open('MQD0R05.json', 'r') as datafile:
        data = json.loads(datafile.read())

    node = Node(element, ['.BDL','.S'], sampler)
    node.data = data

    assert node.pv_data_at('2021-10-01 07:00') == [{"MQD0R05.BDL": "1133.00"}, {"MQD0R05.S": "3.49325"}]


# Verify the inventory constructor properly incorporates extra_properties parameter
def test_inventory():
    inventory = Inventory('Injector', ['Quad'],['Housed_by','S'])
    # Our extra property should be present
    assert 'Housed_by' in inventory.properties
    # As should the base properties
    assert 'S' in inventory.properties
    assert 'EPICSName' in inventory.properties
    # And 3 properties total (i.e. no duplicates from redundant S in constructor)
    assert len(inventory.properties) == 3
