from lepl import *
from time import time


def handle_attributes(attrs):
    return attrs

def handle_base(attrs):
    return attrs

# A definition for space characters including newline and tab
spaces = Star(Space() | '\n' | '\t')

attributes = {}

# A definition for an attribute 'Type.Attribute'
attr_type = Regexp('[a-z]+') > 'type'
attr_name = Regexp('[a-z]+') > 'name'

attribute = attr_type & ~Literal('.') & attr_name > dict


# Allow a list of attributes
attribute_list = Delayed()
attribute_list += attribute & ~spaces & Optional(~Literal(',') & ~spaces & attribute_list) > handle_attributes

select = ~Literal('SELECT') & ~spaces & attribute_list > 'attributes'

scope_option = Literal('SUB') | Literal('BASE') > 'scope'
base_type = Regexp('[a-z]+') > 'object'
base_value = String() > 'base'
base = ~Literal('BASE') & ~spaces & base_type & ~spaces & base_value & ~spaces & scope_option > handle_base

statement = ~spaces & select & ~spaces & base & ~spaces


query = """SELECT asdf.asdf, herbert.tester
BASE user "dc=gonicus,dc=de" SUB
"""

print statement.parse(query)


