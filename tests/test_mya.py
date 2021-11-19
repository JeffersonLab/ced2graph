# File containing some tests of the mya module.

from mya import Sampler

# Test that Sampler correctly computes number of steps in a date range
# including those that span DST changeovers.
def test_steps_between():
    # 24 hours in a normal day
    assert Sampler.steps_between('2021-10-01','2021-10-02','1h') == 24
    # But 25 during "Fall Back" from DST
    assert Sampler.steps_between('2021-11-07', '2021-11-08', '1h') == 25