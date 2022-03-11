import re

# Custom exception class for errors encountered while evaluating filter expressions
class FilterException(RuntimeError): pass

#  replace instances of pv with value in an expression string that uses EPICS macro variable syntax
#  $(pv) to specify pv placeholders that will be replaced.
#
#  ex:  macro_substitute('VIP2R', 10, '8/2 * $(VIP2R)') -> '8/2 * 10'
#
def macro_substitute(pv: str, value: str, expr: str) -> str:
    """
    Parameters
    ----------
    pv    : the PV name to be replaced
    value : the value which will replace PV
    expr  : the string
    """
    pattern = r"\$\({}\)"
    prepared = pattern.format(pv)
    return re.sub(prepared, value, expr)

# Factory method to return a Filter object
def make(rule: str):
    return Filter(rule)

class Filter():
    """Class for evaluating string filter expressions """
    def __init__(self, rule: str):
        self.rule = rule

    def make_expression(self, data:dict):
        expr = self.rule
        for item in data['values']:
            for key in item.keys():
                expr = macro_substitute(key, item[key], expr)
        return expr

    def passes(self, data: dict):
        expr = self.make_expression(data)
        try:
            result = eval(expr)
            return result
        except SyntaxError as err:
            raise FilterException("The filter expression could not be evaluated: {}".format(expr))