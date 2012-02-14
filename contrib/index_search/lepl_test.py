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
    pass

class Attributes(Node):
    pass

class Match(Node):
    pass


class Condition(Node):
    def compile(self):
        return("")

class Collection(Node):
    def compile(self):
       
        l = self[0]
        r = self[2]
        print type(l),type(r)
        print type(self[2])
        left = self[0].compile()
        #con = ""#self[1]
        #right = self[2].compile()
        #return("(%s %s %s)" % (left, con, right))
        return("")

    pass

class Operator(Node):
    pass

class Where(Node):
    def compileWhere(self):
        print self
        return("")
        return ("where %s" % self[0].compile())


class StringValue(Node):
    pass

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



