from lepl import *
from time import time


class MyNode(Node):

    query_base = None

class Query(MyNode):

    __xquery = None
    Where = None

    _objectTypes = None
    _attributes = None

    def __populate_self(self, obj = None):
        """
        This method populates ourselves (self) to the sub elements
        passed to the constructor. This is necessary to be able to
        access property of the Query class from all Nodes.
        """
        if obj == None:
            obj = self
        for entry in obj:
            if isinstance(entry, Node):
                if len(entry):
                    self.__populate_self(entry)
                entry.query_base = self

    def __init__(self, *args):
        super(Query, self).__init__(*args)

        self._objectTypes = {}
        self._attributes = {}
        self.__populate_self()
        self.__xquery = ""

        # Check BASE statements and prepare _base variables
        indent = "\n"
        objectTypes = []
        for entry in self.Base:
            base_object, base_type, base = entry
            self._objectTypes[base_object] = "$%s_list" % base_object
            self.__xquery += indent + "let $%s_base := collection('objects')//%s[matches(DN/text(), '%s')]" % (base_object, base_object, base)

        # Create a list with the selected attributes
        for attr in self.Attributes[0]:
            objectType, name = attr
            self._register_attribute(objectType, name)

        # Create where statement
        if self.Where:

            # Create loop
            self.__xquery += indent + "for " + ", ".join(map(lambda x: "$%s in $%s_base" %(x,x) , self._objectTypes.keys()))
            indent = "\n  "
            self.__xquery += indent + self.Where[0].compileWhere()

            self.__xquery += indent + "return(concat(%s))" % ", ".join(map(lambda x: x + "/text()", self._attributes.values()))

        else:
            self.__xquery += "return $%s_base" % (self.Base[0][0])

    def _register_attribute(self, objectType, attribute):
        complete = "%s.%s" % (objectType, attribute)
        if objectType not in self._objectTypes:
            raise Exception("no BASE definition found for object type '%s' in '%s'" % (objectType, complete))
        else:
            if attribute in ['DN', 'UUID']:
                self._attributes[complete] = "$%s/%s" % (objectType, attribute)
            else:
                self._attributes[complete] = "$%s/Attributes/%s" % (objectType, attribute)

    def getXQuery_attribute(self, objectType, attribute):
        complete = "%s.%s" % (objectType, attribute)
        if complete not in self._attributes:
            self._register_attribute(objectType, attribute)
        return(self._attributes[complete])

    def getXQuery(self):
        return self.__xquery

class Attribute(MyNode):

    def compileForMatch(self):
        return self.query_base.getXQuery_attribute(self[0], self[1])+"/text()"


class Match(MyNode):

    Match = None

    def compile(self):
        if self.Match:
            return ("(%s)" % self.Match[0].compile())
        else:
            attr1 = self[0].compileForMatch()
            comp  = self[1].compileForMatch()
            attr2 = self[2].compileForMatch()

            return ("%s %s %s" % (attr1, comp, attr2))

class Collection(MyNode):
    def compile(self):
        left = self[0].compile()
        right = self[2].compile()
        con = self[1].lower()
        return("(%s %s %s)" % (left, con, right))

class Operator(MyNode):
    def compileForMatch(self):
        return (self[0])

class Where(MyNode):
    def compileWhere(self):
        return ("where %s" % self[0].compile())


class StringValue(MyNode):
    def compileForMatch(self):
        ret = self[0].replace("(","\\(").replace(")","\\)").replace(" ","\\ ")
        return ("\"%s\"" % (ret))

class Attributes(MyNode):
    pass
class Base(MyNode):
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
BASE SambaDomain SUB "dc=gonicus,dc=de"
WHERE ((((User.sn = "Wurst")) AND (User.sn = User.sn)))
"""

#WHERE User.sn = "Wurst" AND User.sn =User.cn

print query_parser.parse(query)[0].getXQuery()



