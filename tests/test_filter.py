import modules.filter as filter

def test_macro_substitution():
    value = '10'
    pv = 'VIP2R'
    expr = '8/2 * $(VIP2R) + $(x)'
    expr = filter.macro_substitute(pv, value, expr)
    assert expr == '8/2 * 10 + $(x)'
    expr = filter.macro_substitute('x', '3', expr)
    assert expr == '8/2 * 10 + 3'
    assert eval(expr) == 43

def test_filter_does_pass():
    data = {'values': [
        { 'IBC0L02Current': '0.3' }
    ]}
    rule = "$(IBC0L02Current) > 0.1"
    f = filter.make(rule)
    assert f.passes(data) == True

def test_filter_does_not_pass():
    data = {'values': [
        { 'IBC0L02Current': '0.3' }
    ]}
    rule = "$(IBC0L02Current) < 0.1"
    f = filter.make(rule)
    assert f.passes(data) == False

def test_filter_exception():
    data = {'values': [
        { 'IBC0L02Current': '0.3' }
    ]}
    rule = "$(X) < 0.1"   # Will raise a FilterException because no value for X
    f = filter.make(rule)
    try:
        result = f.passes(data)
        assert True == False        # We should never reach this line, but generate an error if we do
    except filter.FilterException as err:
        assert True