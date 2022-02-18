# File containing some tests of the util module.

import modules.util as util

# Test that Sampler correctly computes number of steps in a date range
# including those that span DST changeovers.
def test_read_one_column_csv():
    dates = util.date_ranges_from_file('timestamps.csv')
    assert dates[0]['begin'] == '2022-01-09 18:43:45'
    assert dates[0]['end'] == '2022-01-09 18:43:45'
    assert dates[0]['interval'] == '1s'


def test_read_three_column_csv():
    dates = util.date_ranges_from_file('dateranges.csv')
    assert dates[0]['begin'] == '2022-01-09'
    assert dates[0]['end'] == '2022-01-10'
    assert dates[0]['interval'] == '1h'

    assert dates[1]['begin'] == '2022-02-01'
    assert dates[1]['end'] == '2022-02-03'
    assert dates[1]['interval'] == '4h'