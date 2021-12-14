# File containing some tests of the hgb module.

import modules.hgb as hgb

def test_it_returns_path_from_date():
    assert hgb.path_from_date('.', '2001-11-01') == './2001/11/01/00'
    assert hgb.path_from_date('.', '2001-11-1') == './2001/11/01/00'
    assert hgb.path_from_date('.', '2001-11-01 23:00') == './2001/11/01/23'
