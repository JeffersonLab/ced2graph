# File containing some tests of the ced module.

from ced import TypeTree
import json

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