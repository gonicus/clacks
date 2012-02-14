from lepl import *
from time import time




class MyNode(Node):
    """
    LEPL allows to link parser statements directly to classes which are
    derived from the Node class.

    This class is simply used to introduce the class member 'query_base'
    to the 'Node' class of the lepl module.
    This is required to access the 'Query' class in all derived Nodes.
    """
    query_base = None

class Query(MyNode):
    """
    This is the base class for our query parser.

    It validates the incoming elements created by the parser and constructs
    an xquery statement, which can then be used to query the object-database.

    """

    # The class members mapped by the lepl parser.
    Where = None
    Base = None
    Attributes = None

    # internal mapping of used object types and attributes.
    _objectTypes = None
    _attributes = None
    __xquery = None

    def __init__(self, *args):

        # Ensure that this Node is initialuzed.
        super(Query, self).__init__(*args)

        # Prepare class members
        self._objectTypes = {}
        self._attributes = {}
        self.__populate_self()
        self.__xquery = ""

        # Handle the incoming 'BASE' here.
        # A mapping will be created for each used object-type
        objectTypes = []
        result = []
        for entry in self.Base:
            base_object, base_type, base = entry
            self._objectTypes[base_object] = "$%s_list" % base_object
            result.append("let $%s_base := collection('objects')//%s[matches(DN/text(), '%s')]" % (base_object, base_object, base))

        # Create a list with the selected attributes
        # we'll use them later create the result.
        for attr in self.Attributes[0]:
            objectType, name = attr
            self._register_attribute(objectType, name)

        # Create where statement, which filters the result.
        if self.Where:

            # Create loop
            result.append("for " + ", ".join(map(lambda x: "$%s in $%s_base" %(x,x) , self._objectTypes.keys())))
            result.append(self.Where[0].compileWhere())
            result.append("return(concat(%s))" % ", ".join(map(lambda x: x + "/text()", self._attributes.values())))
        else:
            result.append("return $%s_base" % (self.Base[0][0]))

        #TODO: Add LIMIT statement
        #TODO: Add ORDER BY statement

        self.__xquery = "\n".join(result)

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


    def _register_attribute(self, objectType, attribute):
        """
        Registers a new attribute the the query object, by creating
        a mapping between attribute name and resulting xquery path.

        This can then be used by other linked Nodes like 'Match'
        to directly create xquery results.

        e.g.:
            The parameters:
                _register_attribute('User', 'sn')

            would create an like this in self._attributes
                'User.sn' => "$User/Attributes/sn"
        """
        complete = "%s.%s" % (objectType, attribute)
        if objectType not in self._objectTypes:
            raise Exception("no BASE definition found for object type '%s' in '%s'" % (objectType, complete))
        else:
            if attribute in ['DN', 'UUID']:
                self._attributes[complete] = "$%s/%s" % (objectType, attribute)
            else:
                self._attributes[complete] = "$%s/Attributes/%s" % (objectType, attribute)

    def getXQuery_attribute(self, objectType, attribute):
        """
        Returns the xquery-path to the given attribute.

        e.g.:   getXQuery_attribute('User', 'sn')
                '$User/Attributes/sn'
        """
        complete = "%s.%s" % (objectType, attribute)
        if complete not in self._attributes:
            self._register_attribute(objectType, attribute)
        return(self._attributes[complete])

    def getXQuery(self):
        """
        Returns the compiles xquery.
        """
        return self.__xquery

class Match(MyNode):
    """
    The Match-Node represents matches of the 'Where' tag
    e.g.:
        User.sn = "Hickert" or (User.sn = "Hickert") or (( ... ))
    """

    Match = None

    def compile(self):

        # Each brace in the match will result in a Match-Node
        # containing a sub Match-Node. Here we call the sub-node
        # to keep the originally used braces.
        if self.Match:
            return ("(%s)" % self.Match[0].compile())
        else:
            attr1 = self[0].compileForMatch()
            comp  = self[1].compileForMatch()
            attr2 = self[2].compileForMatch()

            return ("%s %s %s" % (attr1, comp, attr2))

class Operator(MyNode):
    """
    This node represents an operator used in matches.
    e.g.:
        The operator of (User.sn="test") is '='.
    """
    def compileForMatch(self):
        return (self[0])


class Attribute(MyNode):
    """
    This Node represents a simple attribute of the query
    """

    def compileForMatch(self):
        """
        Returns the value of this attribute-node so we can use it in
        xquery where statements.
        """
        return self.query_base.getXQuery_attribute(self[0], self[1])+"/text()"


class Collection(MyNode):
    """
    The collection class contains combined matches.
    e.g.:
        (User.sn = 'Hickert') AND (User.uid = 'hickert')

    """
    def compile(self):
        left = self[0].compile()
        right = self[2].compile()
        con = self[1].lower()
        return("(%s %s %s)" % (left, con, right))

class Where(MyNode):
    """
    This node represents the WHERE statement of the query.
    """
    def compileWhere(self):
        """
        Returns a compiled and ready to use xquery where statement.
        """
        return ("where %s" % self[0].compile())


class StringValue(MyNode):
    """
    String value node.
    It simply represents strings like used here:
        User.sn = "hickert"
    """
    def compileForMatch(self):
        ret = self[0].replace("(","\\(").replace(")","\\)").replace(" ","\\ ")
        return ("\"%s\"" % (ret))


class Attributes(MyNode):
    """
    This node is used to represent attributes
    """
    pass


class Base(MyNode):
    """
    This node is used to represent the BASE tag.
    """
    pass


#TODO: comment this mess
#TODO: add limit and order by statements
#TODO: add performance improvements 


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



