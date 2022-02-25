# File containing some tests of the node module.

import modules.node as node
from modules.mya import Sampler


# Data for tests of node linking
sp1 = node.SetPointNode({"name": "SP1"},[],Sampler('2021-11-01','2021-11-02'))
sp2 = node.SetPointNode({"name": "SP2"},[],Sampler('2021-11-01','2021-11-02'))
rb1 = node.ReadBackNode({"name": "RB1"},[],Sampler('2021-11-01','2021-11-02'))
sp3 = node.SetPointNode({"name": "SP3"},[],Sampler('2021-11-01','2021-11-02'))
rb2 = node.ReadBackNode({"name": "RB2"},[],Sampler('2021-11-01','2021-11-02'))
rb3 = node.ReadBackNode({"name": "RB3"},[],Sampler('2021-11-01','2021-11-02'))
sp4 = node.SetPointNode({"name": "SP4"},[],Sampler('2021-11-01','2021-11-02'))
rb4 = node.ReadBackNode({"name": "RB4"},[],Sampler('2021-11-01','2021-11-02'))

node_list = [sp1, sp2, rb1, sp3, rb2, rb3, sp4, rb4]


# Test the population of Node links property.
def test_populate_links():
    node.List.populate_links(node_list)
    assert len(sp1.links) == 1
    assert sp1.links[-1].name() == sp2.name()
    assert len(sp2.links) == 2
    assert sp2.links[-1].name() == sp3.name()
    assert len(sp3.links) == 3
    assert sp3.links[-1].name() == sp4.name()
    assert len(sp4.links) == 1
    assert sp4.links[-1].name() == rb4.name()

# Test ability to extend links
def test_extended_links():
    # Verify Distance of 1
    node.List.populate_links(node_list)
    assert len(sp1.extended_links(1)) == 1
    assert len(sp2.extended_links(1)) == 2
    assert len(sp3.extended_links(1)) == 3
    assert len(sp4.extended_links(1)) == 1
    # Verify Distance of 2
    assert len(sp1.extended_links(2)) == 3
    assert len(sp2.extended_links(2)) == 5
    assert len(sp3.extended_links(2)) == 4
    assert len(sp4.extended_links(2)) == 1
    # Verify Distance of 3
    assert len(sp1.extended_links(3)) == 6
    assert len(sp2.extended_links(3)) == 6
    assert len(sp3.extended_links(3)) == 4
    assert len(sp4.extended_links(3)) == 1

# Readback Nodes have no links at any distance
def test_extended_links_not_for_readbacks():
    node.List.populate_links(node_list)
    assert len(rb1.extended_links(1)) == 0
    assert len(rb2.extended_links(1)) == 0
    assert len(rb3.extended_links(1)) == 0
    assert len(rb4.extended_links(1)) == 0
    assert len(rb1.extended_links(2)) == 0
    assert len(rb2.extended_links(2)) == 0
    assert len(rb3.extended_links(2)) == 0
    assert len(rb4.extended_links(2)) == 0
    assert len(rb1.extended_links(3)) == 0
    assert len(rb2.extended_links(3)) == 0
    assert len(rb3.extended_links(3)) == 0
    assert len(rb4.extended_links(3)) == 0