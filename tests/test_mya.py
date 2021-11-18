# File containing some tests of the mya module.

from mya import Sampler


def test_steps_between():
    assert Sampler.steps_between('2021-10-01','2021-10-02','1h') == 24
