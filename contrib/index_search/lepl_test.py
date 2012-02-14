from lepl import *
from time import time


class Query(Node):

    __xquery = None
    Where = None

    def __init__(self, *args):
        super(Query, self).__init__(*args)

        # Create let statement
        indent = ""
        objectTypes = []
        for entry in self.Base:
            base_object, base_type, base = entry
            objectTypes.append(base_object)
            print indent + "let $%s_base := collection('objects')//%s[matches(DN/text(), '%s')]" % (base_object, base_object, base)

        if self.Where:

            # Create loop
            print indent + "for " + ", ".join(map(lambda x: "$%s in $%s_base" %(x,x) , objectTypes))
            indent = "  "
            print indent + self.Where[0].compileWhere()

            print indent + "return Attributes"

        else:
            print "return $%s_base" % (self.Base[0][0])

    def getXQuery():
        return self.__xquery

class Base(Node):
    pass

class Attribute(Node):

    def compileForMatch(self):
        return (self[0] + "." + self[1])

class Attributes(Node):
    pass

class Match(Node):

    Match = None

    def compile(self):
        if self.Match:
            return ("(%s)" % self.Match[0].compile())
        else:
            attr1 = self[0].compileForMatch()
            comp  = self[1].compileForMatch()
            attr2 = self[2].compileForMatch()

            return ("%s %s %s" % (attr1, comp, attr2))

class Collection(Node):
    def compile(self):
        left = self[0].compile()
        right = self[2].compile()
        con = self[1]
        return("(%s %s %s)" % (left, con, right))

class Operator(Node):
    def compileForMatch(self):
        return (self[0])

class Where(Node):
    def compileWhere(self):
        return ("where %s" % self[0].compile())


class StringValue(Node):
    def compileForMatch(self):
        ret = self[0].replace("(","\\(").replace(")","\\)").replace(" ","\\ ")
        return ("\"%s\"" % (ret))

# A definition for space characters including newline and tab
sp = Star(Space() | '\n' | '\t')

attributes = {}


#################
### SELECT
################

# A definition for an attribute 'Type.Attribute'
attr_type = Regexp('[a-zA-Z]+')
attr_name = attr_type

# Attribute  --  (e.g. User.cn)
attribute = ~sp & attr_type & ~Literal('.') & attr_name & ~sp >  Attribute

# Allow to have multiple attributes
attribute_list = Delayed()
attribute_list += attribute & Optional(~Literal(',') & attribute_list)

select = ~Literal('SELECT') & attribute_list > Attributes

################
### BASE
################
scope_option = Literal('SUB') | Literal('BASE') | Literal('ONE')
base_type = attr_type
base_value = String()
base = ~Literal('BASE') & ~sp & base_type & ~sp & scope_option & ~sp & base_value > Base
bases = Delayed()
bases+= base & Optional (~sp & bases)

################
### WHERE
################

statement= ~sp & (attribute | (String() > StringValue)) & ~sp
operator = ~sp & (Literal('=') | Literal('!=')) & ~sp > Operator
condition_tmp = statement & operator & statement

# Allow to have brakets in condition statements
condition = Delayed()
condition+= condition_tmp | ~Literal('(') & condition & ~Literal(')') > Match

# Allow to connect conditions (called collection below) 
collection_operator = ~sp & (Literal('AND') | Literal('OR')) & ~sp

# Create a collection which supports nested conditions
collection = Delayed()
collection+= (condition & collection_operator & (condition | collection)) > Collection

joined_collections  = Delayed()
joined_collections += collection | condition |  ~Literal('(') & joined_collections  & ~Literal(')') 

where = ~Literal('WHERE') & ~sp & joined_collections  > Where

query_parser = ~sp & select & ~sp & bases & ~sp & Optional(where & ~sp) > Query



query = """
SELECT User.sn, User.cn
BASE User SUB "dc=gonicus,dc=de"
WHERE ((((User.sn = "Wurst")) AND (User.sn = User.sn)))
"""

#WHERE User.sn = "Wurst" AND User.sn =User.cn

query_parser.parse(query)[0]



