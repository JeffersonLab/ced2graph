# File containing some tests of the mya module.

from modules.mya import Sampler


# Test that Sampler correctly computes number of steps in a date range
# including those that span DST changeovers.
def test_steps_between():
    # 24 hours in a normal day
    assert Sampler.steps_between('2021-10-01', '2021-10-02', '1h') == 24
    # But 25 during "Fall Back" from DST
    assert Sampler.steps_between('2021-11-07', '2021-11-08', '1h') == 25


def test_steps_per_chunk():
    # First test is simple case with just one PV in the list
    sampler = Sampler('2021-10-01', '2021-10-02', '1h', ['IBC0R08CRCUR1'])
    sampler.throttle = 5
    assert sampler.steps_per_chunk('2021-10-01') == 5 # floor(Throttle/PVCount=1)
    assert sampler.steps_per_chunk('2021-10-01 22:00') == 2 # Limited to remaining hours

    # Now when the PV list is > 1
    sampler = Sampler('2021-10-01', '2021-10-02', '1h', ['IBC0R08CRCUR1','IBC0R08CRCUR2','IBC0R08CRCUR3'])
    sampler.throttle = 5
    assert sampler.steps_per_chunk('2021-10-01') == 1  # floor(Throttle/PVCount=3)
    assert sampler.steps_per_chunk('2021-10-01 22:00') == 1  # Limited by PV size not remaining hours