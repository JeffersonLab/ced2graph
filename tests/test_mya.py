# File containing some tests of the mya module.

import modules.mya as mya

# Test that Sampler correctly computes number of steps in a date range
# including those that span DST changeovers.
def test_read_one_column_csv():
    dates = mya.date_ranges_from_file('timestamps.csv')
    assert dates[0]['begin'] == '2022-01-09 18:43:45'
    assert dates[0]['end'] == '2022-01-09 18:43:45'
    assert dates[0]['interval'] == '1s'


def test_read_three_column_csv():
    dates = mya.date_ranges_from_file('dateranges.csv')
    assert dates[0]['begin'] == '2022-01-09'
    assert dates[0]['end'] == '2022-01-10'
    assert dates[0]['interval'] == '1h'

    assert dates[1]['begin'] == '2022-02-01'
    assert dates[1]['end'] == '2022-02-03'
    assert dates[1]['interval'] == '4h'

# Test that Sampler correctly computes number of steps in a date range
# including those that span DST changeovers.
def test_steps_between():
    # 24 hours in a normal day
    assert mya.Sampler.steps_between('2021-10-01', '2021-10-02', '1h') == 24
    # But 25 during "Fall Back" from DST
    assert mya.Sampler.steps_between('2021-11-07', '2021-11-08', '1h') == 25


def test_steps_per_chunk():
    # First test is simple case with just one PV in the list
    span = {'begin_date': '2021-10-01', 'end_date': '2021-10-02', 'interval': '1h'}
    dates = [span]
    sampler = mya.Sampler(dates, ['IBC0R08CRCUR1'])
    sampler.throttle = 5
    assert sampler.steps_per_chunk('2021-10-01', span['end_date'], span['interval']) == 5 # floor(Throttle/PVCount=1)
    assert sampler.steps_per_chunk('2021-10-01 22:00', span['end_date'], span['interval']) == 2 # Limited to remaining hours

    # Now when the PV list is > 1
    sampler = mya.Sampler(dates, ['IBC0R08CRCUR1','IBC0R08CRCUR2','IBC0R08CRCUR3'])
    sampler.throttle = 5
    assert sampler.steps_per_chunk('2021-10-01', span['end_date'], span['interval']) == 1  # floor(Throttle/PVCount=3)
    assert sampler.steps_per_chunk('2021-10-01 22:00', span['end_date'], span['interval']) == 1  # Limited by PV size not remaining hours