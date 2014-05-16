import os
import roam.defaults

def test_variables_are_expanded():
    os.environ['TESTVAR'] = 'MYVAR'
    default = "1 %TESTVAR% 2"
    outdefault = roam.defaults.default_value(default, None, None)
    assert outdefault == '1 MYVAR 2'
