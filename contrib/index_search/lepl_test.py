from lepl import *
from time import time
from clacks.agent.xmldb.handler import XMLDBHandler
from json import loads, dumps
from pprint import pprint


class MyNode(Node):
    """
    LEPL allows to link parser statements directly to classes which are
    derived from the Node class.

    This class is simply used to introduce the class member 'query_base'
    to the 'Node' class of the lepl module.
    This is required to access the 'Query' class in all derived Nodes.
    """
    query_base = None

    def _set_query_base_object(self, obj):
        self.query_base = obj


class Query(MyNode):
    """
    This is the base class for our query parser.

    It validates the incoming elements created by the parser and constructs
    an xquery statement, which can then be used to query the object-database.

    """

    # The class members mapped by the lepl parser.
    Where = None
    Base = None
    Limit = None
    Attributes = None
    OrderBy = None

    # internal mapping of used object types and attributes.
    _objectTypes = None
    _attributes = None
    _selected_attributes = None
    __xquery = None

    # This indicates whether a join between different object types are used or not.
    uses_join = False
    _joined_values = None

    _xquery_header = """

declare function local:get_attributes ($node as node(), $attrs as item()*)
as xs:string
{
    let $res := (
        for $attr in $attrs

        let $attr_res := (
            for $item in $node/*/.[name()=($attr)]
            return local:create_json_value($item))

        let $attr_res := ($attr_res , (
            for $item in $node/Extensions/*/.[name()=($attr)]
            return local:create_json_value($item)))

        let $attr_res := ($attr_res , (
            for $item in $node/Attributes/*/.[name()=($attr)]
            return local:create_json_value($item)))

        return concat(local:create_json_key(concat($node/name(),".",$attr)), ": [", string-join($attr_res, ","), "]"))

    return string-join($res, ",")
};


declare function local:get_attribute_as_json ($key as xs:string, $value as xs:string)
as xs:string
{
    concat(local:create_json_key($key),": ", local:create_json_value($value))
};

declare function local:create_json_value($x as xs:string)
as xs:string
{
    (: Replaces all occurences of " in the given string with
       an escaped quote \", this enables us to use this string in json.
    :)
    let $clean := replace($x, '"', '&#92;&#92;&#34;')
    return concat('"', $clean, '"')
};


declare function local:create_json_key($x as xs:string)
as xs:string
{
    (: Prepares a string to be used as json-dict key.
    :)
    concat('"', $x, '"')
};


"""

    def __init__(self, *args):

        # Prepare class members
        self._joined_values = []
        self._objectTypes = {}
        self._attributes = {}
        self._selected_attributes = []
        self.__xquery = ""
        self.result = []

        # Ensure that all Nodes are initialized and have access to the base-node 'Query'.
        self.__populate_self(args)
        super(Query, self).__init__(*args)

        """
        Increase the speed of joined statements by preparing a sequence containing
        all potentially joined values.

        This will then look like this:

            >>> let $join_values_0 := distinct-values ( (collection('objects')//SambaDomain/Attributes/sambaDomainName,
            >>>         collection('objects')//User/Attributes/sambaDomainName) )

        And then be used when object list are created:
            >>> let $User_base := collection('objects')//User[matches(DN/text(), 'dc=gonicus,dc=de')
            >>>     and Attributes/sambaDomainName = ($join_values_0)]
        """
        joins = {}
        result = [self._xquery_header]

        # Create a list of attributes the user was querying for.
        sel_attrs = self.Attributes[0].get_attribute_names()
        for key in sel_attrs:
            attr_list = ", ".join(map(lambda x: "'%s'"%x , sel_attrs[key]))
            result.append('let $%s_attributes := (%s)' % (key, attr_list))

        result.append('')

        if self.uses_join:

            # Create a predefined list of joined values
            cnt = 0
            for join in self._joined_values:
                cnt += 1

                # Get attributes in xquery addressed style
                #  e.g.: "User/Attributes/sambaDomainName"
                attr1 = "%s/%s" % (join[0][0], self.getXQuery_attribute(*join[0]))
                attr2 = "%s/%s" % (join[1][0], self.getXQuery_attribute(*join[1]))

                # Prepate a join list which will then include all joins per object-type.
                if not join[0][0] in joins:
                    joins[join[0][0]]  = []
                if not join[1][0] in joins:
                    joins[join[1][0]]  = []

                # The name of the join variable used in the resulting xquery
                join_name = "$join_values_%s" % cnt

                # Append the left side of the join to the join list
                if not join_name in joins[join[0][0]]:
                    joins[join[0][0]].append((join_name, self.getXQuery_attribute(*join[0])))

                # Append the right side of the join to the join list
                if not join_name in joins[join[1][0]]:
                    joins[join[1][0]].append((join_name, self.getXQuery_attribute(*join[1])))

                # Append a xquery variable to the result, which contains the joined values.
                result.append("let %s := distinct-values ( (%s//%s,\n      %s//%s) )" % ( \
                        join_name, "collection('objects')", attr1, "collection('objects')", attr2))

        result.append('')

        """
        Prepare lists of objects we've to iterate through in the xquery.

        This block will create entries like this:
            >>> let $User_base := collection('objects')//User[matches(DN/text(), 'dc=gonicus,dc=de')
            >>>     and Attributes/sambaDomainName = ($join_values_0)]

        If joins between objects were not used then entry will look like this:
            >>> let $User_base := collection('objects')//User[matches(DN/text(), 'dc=gonicus,dc=de')]
        """
        for entry in self.Base:
            base_object, base_type, base = entry

            # If joins were used for this object-type then extend the match condition in the let statement
            join_statement = ""
            if base_object in joins:
                for join in joins[base_object]:
                    join_statement += "\n\t%s = (%s) and" % (join[1], join[0])

            # Append the let statement
            result.append("let $%s_base := collection('objects')//%s[%s \n\tmatches(DN/text(), '%s')]" % ( \
                    base_object, base_object, join_statement, base))

        result.append('')

        # Create a list with the selected attributes
        # we'll use them later create the result.
        for attr in self.Attributes[0]:
            objectType, name = attr
            if name == '*':
                import sys
                print "User.* not supported yet"
                sys.exit()


            self._register_attribute(objectType, name)
            self._selected_attributes.append((objectType, name))

        """
        Create condition statement

        It may like this for conditions using joins:
        (Note the 'for' statement which is required to iterate through all potential entries)

            >>> for $User in $User_base, $SambaDomain in $SambaDomain_base
            >>>     where ($SambaDomain/Attributes/sambaDomainName/text() = $User/Attributes/sambaDomainName/text())
            >>>     oder by User.sn
            >>>     return(...)

        or like this if we do not have any conditions:

            >>> return(...)
        """

        # Create loop for each required object type
        where_result = []
        where_result.append("for " + ", ".join(map(lambda x: "$%s in $%s_base" %(x,x) , self._objectTypes.keys())))

        # Add optional where statement
        if self.Where:
            where_result.append(self.Where[0].compileWhere())

        # Add optional order by statement
        if self.OrderBy:
            where_result.append("order by " + self.OrderBy[0].compile_xquery())

        # Create a list of with all selected attributes.
        attrs = map(lambda x: "$%s/%s/text()" % (x[0], self.getXQuery_attribute(x[0], x[1])), self._selected_attributes)

        # Add the return statement for the result.
        attr_get_list = ", ".join(map(lambda x: "local:get_attributes($%s, $%s_attributes)" % (x, x), self._objectTypes.keys()))
        where_result += [
            'return(',
            '   concat("{",',
            '       string-join(',
            '           ( ',
            '               '+ attr_get_list,
            '           ), ", "',
            '       ),"}"',
            '   )',
            ')']

        """
        Process the LIMIT statement here.

        It can occure in two forms:
            >>> LIMIT 5
            >>> LIMIT 5, 10

        Where the first shows only the first five entries and the second shows
        ten entries beginning from the fifth element.

        In xquery this looks like this

            return subsequence(
                for ...
                    where...
                    order by ...
                    return
                ), 5, 10)
        """
        if self.Limit:
            where_result =  ['return subsequence('] + where_result + [",%s,%s)" % (self.Limit[0].get_range())]

        result += where_result

        self.__xquery = "\n".join(result)

    def __populate_self(self, obj):
        """
        This method populates ourselves (self) to the sub elements
        passed to the constructor. This is necessary to be able to
        access property of the Query class from all Nodes.
        """
        for entry in obj:
            if isinstance(entry, Node):
                if len(entry):
                    self.__populate_self(entry)
                entry._set_query_base_object(self)

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
                self._attributes[complete] = "%s" % (attribute)
            else:
                self._attributes[complete] = "Attributes/%s" % (attribute)

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

    def _set_query_base_object(self, obj):
        super(Match, self)._set_query_base_object(obj)

        # Check if we use a join between two different object types
        if type(self[0]) == Attribute and type(self[2]) == Attribute:

            if self[0][0] == self[2][0]:
                raise Exception("joins between the same object-type are now allowed. (%s)" % self.compile())

            self.query_base.uses_join = True
            self.query_base._joined_values.append(((self[0][0], self[0][1]), (self[2][0], self[2][1])))

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
        return "$%s/%s/text()" % (self[0], self.query_base.getXQuery_attribute(self[0], self[1]))


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
    def _set_query_base_object(self, obj):
        super(Attributes, self)._set_query_base_object(obj)

    def get_attribute_names(self):
        ret = {}
        for attribute in self:
            if not attribute[0] in ret:
                ret[attribute[0]] = []
            ret[attribute[0]].append(attribute[1])
        return(ret)


class Base(MyNode):
    """
    This node is used to represent the BASE tag.
    """

    def _set_query_base_object(self, obj):
        super(Base, self)._set_query_base_object(obj)

        # Handle object-types of the SELECT statement
        base_object, base_type, base = self
        obj._objectTypes[base_object] = "$%s_list" % base_object


class Limit(MyNode):

    def get_range(self):
        if len(self) == 2:
            start = self[0]
            stop = self[1]
        else:
            start = 1
            stop = self[0]
        return(start, stop)


class OrderBy(MyNode):
    def compile_xquery(self):
        return(", ".join(map(lambda x: x.compile_xquery(), self)))


class Direction(MyNode):
    def get_direction(self):
        return "ascending" if self[0] == 'ASC' else 'descending'


class OrderedAttribute(MyNode):

    Direction = None

    def compile_xquery(self):
        if self.Direction:
            return("%s %s" % (self.Attribute[0].compileForMatch(), self.Direction[0].get_direction()))
        else:
            return("%s" % (self.Attribute[0].compileForMatch()))



#TODO: comment this mess
#TODO: add performance improvements


# A definition for space characters including newline and tab
spaces = (~Space() | ~Literal('\n') | ~Literal('\t')) [:]

attributes = {}


#################
### SELECT
################

# A definition for an attribute 'Type.Attribute'
attr_type = Regexp('[a-zA-Z]+')
attr_name = Regexp('[a-zA-Z]+') | Literal('*')
number = UnsignedReal()
attribute = attr_type & ~Literal('.') & attr_name >  Attribute

with Separator(spaces):

    ################
    ### Select
    ################
    attribute_list = Delayed()
    attribute_list += attribute & Optional(~Literal(',') & attribute_list)
    select = ~Literal('SELECT') & attribute_list > Attributes

    ################
    ### BASE
    ################
    scope_option = Literal('SUB') | Literal('BASE') | Literal('ONE')
    base_type = attr_type
    base_value = String()
    base = ~Literal('BASE') & base_type & scope_option & base_value > Base
    bases = Delayed()
    bases+= base & Optional (~spaces & bases)

    ################
    ### WHERE
    ################


    statement= (attribute | (String() > StringValue))
    operator = (Literal('=') | Literal('!=')) > Operator
    condition_tmp = statement & operator & statement

    # Allow to have brakets in condition statements
    condition = Delayed()
    condition+= condition_tmp | ~Literal('(') & condition & ~Literal(')') > Match

    # Allow to connect conditions (called collection below)
    collection_operator = (Literal('AND') | Literal('OR'))

    # Create a collection which supports nested conditions
    collection = Delayed()
    collection+= (condition & collection_operator & (condition | collection)) > Collection

    joined_collections  = Delayed()
    joined_collections += collection | condition |  ~Literal('(') & joined_collections  & ~Literal(')')

    where = ~Literal('WHERE') & joined_collections  > Where

    ################
    ### Limit
    ################

    limit = (~Literal('LIMIT') & number & Optional(~Literal(',') & number)) > Limit

    ################
    ### Order By
    ################

    direction = Literal('ASC') | Literal('DESC') > Direction
    odered_attr = attribute & Optional(direction) > OrderedAttribute
    odered_attr_list = Delayed()
    odered_attr_list+= odered_attr & Optional(~Literal(',') & odered_attr_list)
    order_by = ~Literal('ORDER BY') & odered_attr_list > OrderBy

    query_parser = ~spaces & select & bases & Optional(where) & Optional(order_by) & Optional(limit) & ~spaces > Query


# ---------------------

xmldb = XMLDBHandler.get_instance()
xmldb.setNamespace('objects', 'xs', "http://www.w3.org/2001/XMLSchema")

query = """
SELECT User.sn, User.cn, SambaDomain.sambaDomainName
BASE SambaDomain SUB "dc=gonicus,dc=de"
BASE User SUB "dc=gonicus,dc=de"
WHERE (SambaDomain.sambaDomainName = User.sambaDomainName)
ORDER BY User.sn, User.givenName DESC
"""


xquery =  query_parser.parse(query)[0].getXQuery()
print  xquery
pprint(xmldb.xquery(xquery))
