""""


#TODO: Queries are not performaning very good.
#      Even not joined queries take up to 0.5 seconds

#TODO: Do not return the complete object that matches the query.
#      At the moment we return the complete object (e.g. User) that
#      matches the query, due to the fact that selecting only the
#      required attributes leads to drastically increased executioni
#      time of the query.
#      But returning the complete object, will return all sub-objects
#      to... think of querying all 'OrganizationalUnit's, in that case
#      ALL sub objects will be returned to, which may result in returning
#      the complete database!!!
#
#      We've to find a solution here...


# -----------------


This class is a search wrapper, which hides the xquery syntax from the user but allows
to use a SQL like query syntax.

Writing this search-wrapper was necessary to avoid that users send their own xqueries to
the object database and thus can read everything without any permissions been checked.
So we decided to create a wrapper which allows us to take care what is queried and what is
returned to the user.

Additionally we've introduced a SQL like query syntax.

E.g. a query for:

>>> SELECT User.sn, User.cn, SambaDomain.sambaDomainName
>>> BASE SambaDomain SUB "dc=gonicus,dc=de"
>>> BASE User SUB "dc=gonicus,dc=de"
>>> WHERE (SambaDomain.sambaDomainName = User.sambaDomainName)
>>> ORDER BY User.sn, User.givenName DESC

will internally send the following xquery to the obejct database:
(The result may change in the future, its just here to give an idea
about whats done here)

>>> let $SambaDomain_attributes := ('sambaDomainName', 'DN')
>>> let $User_attributes := ('sn', 'cn', 'DN')
>>>
>>> let $join_values_1 := distinct-values ( (collection('objects')//SambaDomain/Attributes/sambaDomainName,
>>>       collection('objects')//User/Attributes/sambaDomainName) )
>>>
>>> let $SambaDomain_base := collection('objects')//SambaDomain[
>>>     Attributes/sambaDomainName = ($join_values_1) and
>>>     matches(DN/text(), 'dc=gonicus,dc=de')]
>>> let $User_base := collection('objects')//User[
>>>     Attributes/sambaDomainName = ($join_values_1) and
>>>     matches(DN/text(), 'dc=gonicus,dc=de')]
>>>
>>> for $SambaDomain in $SambaDomain_base, $User in $User_base
>>> where ($SambaDomain/Attributes/sambaDomainName/text() = $User/Attributes/sambaDomainName/text())
>>> order by $User/Attributes/sn/text(), $User/Attributes/givenName/text() descending
>>> return(
>>>    concat("{",
>>>        string-join(
>>>            (
>>>                local:get_attributes($SambaDomain, $SambaDomain_attributes), local:get_attributes($User, $User_attributes)
>>>            ), ", "
>>>        ),"}"
>>>    )

"""


import re
from lxml import etree
from time import time
from clacks.agent.xmldb.handler import XMLDBHandler
from lepl import Literal, Node, Regexp, UnsignedReal, Space, Separator, Delayed, Optional, String


class MyNode(Node):
    """
    LEPL allows to link parser statements directly to classes which are
    derived from the Node class.

    This class is simply used to introduce the class member 'query_base'
    to the 'Node' class of the lepl module.
    This is required to access the 'Query' class in all derived Nodes.
    """
    query_base = None

    def set_query_base_object(self, obj):
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
    object_types = None
    _attributes = None
    _selected_attributes = None
    _xquery = None

    # The time executing this query took
    time = None

    # This indicates whether a join between different object types are used or not.
    uses_join = False
    joined_values = None

    _xquery_header = ""

    def __init__(self, *args):

        # Prepare class members
        self.joined_values = []
        self.object_types = {}
        self._attributes = {}
        self._selected_attributes = []
        self._xquery = ""
        self.result = []

        # Ensure that all Nodes are initialized and have access to the base-node 'Query'.
        self.__populate_self(args)
        super(Query, self).__init__(*args)

        # Append the query header containg usefull functions.
        result = [self._xquery_header]

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
        if self.uses_join:

            # Create a predefined list of joined values
            cnt = 0
            for join in self.joined_values:
                cnt += 1

                # Get attributes in xquery addressed style
                #  e.g.: "User/Attributes/sambaDomainName"
                attr1 = "%s/%s" % (join[0][0], self.get_xquery_attribute(*join[0]))
                attr2 = "%s/%s" % (join[1][0], self.get_xquery_attribute(*join[1]))

                # Prepate a join list which will then include all joins per object-type.
                if not join[0][0] in joins:
                    joins[join[0][0]]  = []
                if not join[1][0] in joins:
                    joins[join[1][0]]  = []

                # The name of the join variable used in the resulting xquery
                join_name = "$join_values_%s" % cnt

                # Append the left side of the join to the join list
                if not join_name in joins[join[0][0]]:
                    joins[join[0][0]].append((join_name, self.get_xquery_attribute(*join[0])))

                # Append the right side of the join to the join list
                if not join_name in joins[join[1][0]]:
                    joins[join[1][0]].append((join_name, self.get_xquery_attribute(*join[1])))

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
            if base_type == "SUB":
                base_regex = re.escape(base) + "$"
            elif base_type == "ONE":
                base_regex = "^[^,]*," + re.escape(base) + "$"
            elif base_type == "BASE":
                base_regex = "^" + re.escape(base) + "$"
            else:
                raise Exception("Unknown scope value '%s'" % (base_type))

            # Do not escape ', ='
            base_regex = base_regex.replace("\=", "=")
            base_regex = base_regex.replace("\,", ",")
            base_regex = base_regex.replace("\ ", " ")

            result.append("let $%s_base := collection('objects')//%s[%s\n\tmatches(DN, '%s')]" % ( \
                    base_object, base_object, join_statement, base_regex))

        result.append('')

        # Create a list with the selected attributes
        # we'll use them later create the result.
        for attr in self.Attributes[0]:
            object_type, name = attr
            self._register_attribute(object_type, name)
            self._selected_attributes.append((object_type, name))

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
        where_result.append("for " + ", ".join(map(lambda x: "$%s in $%s_base" %(x, x) , self.object_types.keys())))

        # Add optional where statement
        if self.Where:
            where_result.append(self.Where[0].compile_where())

        # Add optional order by statement
        if self.OrderBy:
            where_result.append("order by " + self.OrderBy[0].compile_xquery())

        # Add the return statement for the result.
        attr_get_list = [", ".join(map(lambda x: "$%s" % (x), self.object_types.keys()))]
        attr_get_list = ", ".join(attr_get_list)

        where_result += ['return( <res> {' + attr_get_list + ' } </res>)']

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

        where_result =  ["let $res := ("] + where_result + [")"]
        where_result +=  ["return $res"]

        result += where_result

        self._xquery = "\n".join(result)

    def execute(self):
        """
        Executes the created xquery and return only interessting attributes.
        """
        xmldb = XMLDBHandler.get_instance()
        xmldb.setNamespace('objects', 'xs', "http://www.w3.org/2001/XMLSchema")
        start = time()
        xquery =  self.get_xquery()
        result = []
        for res in xmldb.xquery(xquery):
            obj = (self.recursive_dict(etree.XML(res), True))
            res = {}
            for suffix, name in self._selected_attributes:

                if not suffix in res:
                    res[suffix] = {}

                # Return all attributes
                if name == "*":
                    res[suffix] = obj[suffix][0]['Attributes'][0]
                    for name in ('UUID', 'Type', 'DN'):
                        res[suffix][name] = (obj[suffix][0][name])
                    if 'Extensions' in obj[suffix][0]:
                        for name in ('Extension'):
                            res[suffix][name] = (obj[suffix][0]['Extensions'][0][name])

                else:
                    path = self._get_attribute_location(name)
                    if path:
                        if path in obj[suffix][0]:
                            res[suffix][name] = (obj[suffix][0][path][0][name])
                    else:
                        res[suffix][name] = (obj[suffix][0][name])
            result.append(res)
        self.time = time() - start
        return result

    def recursive_dict(self, element, strip_namespaces=False):
        """
        Resursivly creates a dictionary out of the given etree.XML object.
        """
        res = {}
        for item in element:
            tag = re.sub('^\{([^\}]*)\}', '', item.tag) if strip_namespaces else item.tag
            if not tag in res:
                res[tag] = []
            if len(item):
                res[tag].append(self.recursive_dict(item, strip_namespaces))
            else:
                res[tag].append(item.text)
        return res

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
                entry.set_query_base_object(self)

    def _register_attribute(self, object_type, attribute):
        """
        Registers a new attribute for the query object, by creating
        a mapping between attribute name and resulting xquery path.

        This can then be used by other linked Nodes like 'Match'
        to directly create xquery results.

        e.g.:
            The parameters:
                _register_attribute('User', 'sn')

            would create an like this in self._attributes
                'User.sn' => "Attributes/sn"
        """
        complete = "%s.%s" % (object_type, attribute)
        if object_type not in self.object_types:
            raise Exception("no BASE definition found for object type '%s' in '%s'" % (object_type, complete))
        else:
            path = self._get_attribute_location(attribute)
            if path:
                self._attributes[complete] =  "%s/%s" % (path, attribute)
            else:
                self._attributes[complete] =  "%s" % (attribute)

    def _get_attribute_location(self, attribute):
        """
        Returns the location for a given attribute

        e.g. the attribute 'Extension' would return 'Extensions'
        """
        if attribute in ['DN', 'UUID', 'Type']:
            return("")
        elif attribute in ['Extension']:
            return("Extensions")
        else:
            return("Attributes")

    def get_xquery_attribute(self, object_type, attribute):
        """
        Returns the xquery-path to the given attribute.

        e.g.:   get_xquery_attribute('User', 'sn')
                '$User/Attributes/sn'
        """
        complete = "%s.%s" % (object_type, attribute)
        if complete not in self._attributes:
            self._register_attribute(object_type, attribute)
        return(self._attributes[complete])

    def get_xquery(self):
        """
        Returns the compiles xquery.
        """
        return self._xquery


class Match(MyNode):
    """
    The Match-Node represents matches of the 'Where' tag
    e.g.:
        User.sn = "Hickert" or (User.sn = "Hickert") or (( ... ))
    """

    Match = None

    def set_query_base_object(self, obj):
        super(Match, self).set_query_base_object(obj)

        # Check if we use a join between two different object types
        if type(self[0]) == Attribute and type(self[2]) == Attribute:

            if self[0][0] == self[2][0]:
                raise Exception("joins between the same object-type are now allowed. (%s)" % self.compile())

            self.query_base.uses_join = True
            self.query_base.joined_values.append(((self[0][0], self[0][1]), (self[2][0], self[2][1])))

    def compile(self):
        """
        Compiles a xquery statement out of the result.
        """

        # Each brace in the match will result in a Match-Node
        # containing a sub Match-Node. Here we call the sub-node
        # to keep the originally used braces.
        match = ""
        if self.Match:
            match = ("(%s)" % self.Match[0].compile())
        else:
            attr1 = self[0].compile_for_match()
            comp  = self[1].compile_for_match()
            attr2 = self[2].compile_for_match()
            match = ("(%s %s %s)" % (attr1, comp, attr2))

        # Negate the match if a 'NOT' was placed in from of it.
        if 'NOT' in self:
            match = 'not%s' % match
        return match


class Operator(MyNode):
    """
    This node represents an operator used in matches.
    e.g.:
        The operator of (User.sn="test") is '='.
    """
    def compile_for_match(self):
        return (self[0])


class Attribute(MyNode):
    """
    This Node represents a simple attribute of the query
    """

    def compile_for_match(self):
        """
        Returns the value of this attribute-node so we can use it in
        xquery where statements.
        """
        return "$%s/%s" % (self[0], self.query_base.get_xquery_attribute(self[0], self[1]))


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
    def compile_where(self):
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
    def compile_for_match(self):
        ret = self[0].replace("(", "\\(").replace(")", "\\)").replace(" ", "\\ ")
        return ("\"%s\"" % (ret))


class Attributes(MyNode):
    """
    This node is used to represent attributes
    """
    def set_query_base_object(self, obj):
        super(Attributes, self).set_query_base_object(obj)

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

    def set_query_base_object(self, obj):
        super(Base, self).set_query_base_object(obj)

        # Handle object-types of the SELECT statement
        base_object = self[0]
        obj.object_types[base_object] = "$%s_list" % base_object


class Limit(MyNode):
    """
    This node represents the LIMIT statement
    """

    def get_range(self):
        if len(self) == 2:
            start = self[0]
            stop = self[1]
        else:
            start = 1
            stop = self[0]
        return(start, stop)


class OrderBy(MyNode):
    """
    Represents the ORDER BY statement
    """
    def compile_xquery(self):
        return(", ".join(map(lambda x: x.compile_xquery(), self)))


class OrderedAttribute(MyNode):
    """
    This node represents the attributes that have to be ordered by the 'ORDER BY' statement
    """

    Direction = None
    Attribute = None

    def compile_xquery(self):
        if self.Direction:
            return("%s %s" % (self.Attribute[0].compile_for_match(), self.Direction[0].get_direction()))
        else:
            return("%s" % (self.Attribute[0].compile_for_match()))


class Direction(MyNode):
    """
    This node represents the order direction of the 'ORDER BY' attribute list.
    """
    def get_direction(self):
        return "ascending" if self[0] == 'ASC' else 'descending'


class SearchWrapper(object):
    """
    This class is a search wrapper, which hides the xquery syntax from the user but allows
    to use a SQL like query syntax.

    E.g. a query for:

    >>> SELECT User.sn, User.cn, SambaDomain.sambaDomainName
    >>> BASE SambaDomain SUB "dc=gonicus,dc=de"
    >>> BASE User SUB "dc=gonicus,dc=de"
    >>> WHERE (SambaDomain.sambaDomainName = User.sambaDomainName)
    >>> ORDER BY User.sn, User.givenName DESC
    """
    instance = None
    query_parser = None

    def __init__(self):
        self._construct_parser()

    def _construct_parser(self):
        """
        Constructs the query parser that is required to trsnaform the SQL like
        query syntax to a xquery useable.
        """

        #################
        ### SELECT
        ################

        # A definition for an attribute 'Type.Attribute'
        attr_type = Regexp('[a-zA-Z]+')
        attr_name = Regexp('[a-zA-Z]+') | Literal('*')
        number = UnsignedReal()
        attribute = attr_type & ~Literal('.') & attr_name >  Attribute

        # A definition for space characters including newline and tab
        spaces = (~Space() | ~Literal('\n') | ~Literal('\t')) [:]

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
            bases += base & Optional (~spaces & bases)

            ################
            ### WHERE
            ################

            statement = (attribute | (String() > StringValue))
            operator = (Literal('=') | Literal('!=')) > Operator
            condition_tmp = statement & operator & statement

            # Allow to have brakets in condition statements
            condition = Delayed()
            negator = Literal('NOT')
            condition += condition_tmp | Optional(negator) & ~Literal('(') & condition & ~Literal(')') > Match

            # Allow to connect conditions (called collection below)
            collection_operator = (Literal('AND') | Literal('OR'))

            # Create a collection which supports nested conditions
            collection = Delayed()
            collection += (condition & collection_operator & (condition | collection)) > Collection

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
            odered_attr_list += odered_attr & Optional(~Literal(',') & odered_attr_list)
            order_by = ~Literal('ORDER BY') & odered_attr_list > OrderBy

            self.query_parser = ~spaces & select & bases & Optional(where) & Optional(order_by) & Optional(limit) & ~spaces > Query

    def execute(self, query):
        """
        Parses the given query and executes the resulting xquery statement.
        """
        q_o = self.query_parser.parse(query)[0]
        res = q_o.execute()
        print "Query took:", q_o.time, "seconds"
        return res

    @staticmethod
    def get_instance():
        """
        Returns an instance of this class. This avoids instantiating this class everytime.
        """
        if not SearchWrapper.instance:
            SearchWrapper.instance = SearchWrapper()
        return SearchWrapper.instance

