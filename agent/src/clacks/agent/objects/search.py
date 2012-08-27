""""

This class is a search wrapper, which hides the xquery syntax from the user but allows
to use a SQL like query syntax.

Writing this search-wrapper was necessary to avoid that users send their own xqueries to
the object database and thus can read everything without any permissions been checked.
So we decided to create a wrapper which allows us to take care what is queried and what is
returned to the user.

Additionally we've introduced a SQL like query syntax.

E.g. a query for:

>>> SELECT User.sn, User.cn, SambaDomain.sambaDomainName
... BASE SambaDomain SUB "dc=gonicus,dc=de"
... BASE User SUB "dc=gonicus,dc=de"
... WHERE (SambaDomain.sambaDomainName = User.sambaDomainName)
... ORDER BY User.sn, User.givenName DESC

will internally send the following xquery to the obejct database:
(The result may change in the future, its just here to give an idea
about whats done here)

>>> let $SambaDomain_attributes := ('sambaDomainName', 'DN')
... let $join_values_1 := distinct-values ( (collection('objects')/SambaDomain/Attributes/sambaDomainName,
...       collection('objects')/User/Attributes/sambaDomainName) )
...
... let $SambaDomain_base := collection('objects')/SambaDomain[
...     Attributes/sambaDomainName = ($join_values_1) and
...     ends-with(DN, 'dc=gonicus,dc=de')]
... let $User_base := collection('objects')/User[
...     Attributes/sambaDomainName = ($join_values_1) and
...     ends-with(DN, 'dc=gonicus,dc=de')]
...
... for $SambaDomain in $SambaDomain_base, $User in $User_base
... where ($SambaDomain/Attributes/sambaDomainName/text() = $User/Attributes/sambaDomainName/text())
... order by $User/Attributes/sn/text(), $User/Attributes/givenName/text() descending
... return( $SambaDomain, $User )

"""
import re
from lxml import etree
from time import time
from clacks.common import Environment
from zope.interface import implements
from clacks.agent.xmldb.handler import XMLDBHandler
from clacks.agent.objects.factory import ObjectFactory
from clacks.agent.acl import ACLResolver
from lepl import Literal, Node, Regexp, UnsignedReal, Space, Separator, Delayed, Optional, String, Star
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import Plugin
from clacks.common.components import PluginRegistry

class MyNode(Node):
    """
    LEPL allows to link parser statements directly to classes which are
    derived from the Node class.

    This class is simply used to introduce the class member attribute 'query_base'
    to the 'Node' class of the lepl module.
    This is required to access the 'Query' class in all derived Nodes.
    """
    query_base = None

    def set_query_base_object(self, obj):
        """
        Introduce the 'base' node to the current node.
        """
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

    _collection = 'objects'

    __acl_resolver = None
    __env = None

    def __init__(self, *args):

        # Prepare class members
        self.joined_values = []
        self.object_types = {}
        self._attributes = {}
        self._selected_attributes = []
        self._xquery = ""
        self.result = []
        self.__acl_resolver = ACLResolver.get_instance()
        self.__env = Environment.getInstance()

        # Ensure that all Nodes are initialized and have access to the base-node 'Query'.
        self.__populate_self(args)
        super(Query, self).__init__(*args)

        # Append the query header containg usefull functions.
        result = [self._xquery_header]

        """
        Prepare lists of objects we've to iterate through in the xquery.

        This block will create entries like this:
            >>> let $User_base := collection('objects')/User[ParentDN =  'dc=gonicus,dc=de')]
        """
        for entry in self.Base:
            base_object, base_type, base = entry

            # Append the let statement
            if base_type == "SUB":
                match = "ends-with(o:ParentDN , '%s')" % (base)
            elif base_type == "ONE":
                match = "o:ParentDN = '%s'" % base
            elif base_type == "BASE":
                match = "o:DN = '%s'" % base
            else:
                raise Exception("Unknown scope value '%s'" % (base_type))

            result.append("let $%s_base := collection('%s')/o:%s[%s]" % (base_object, self._collection, base_object, match))

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
            >>>     where ($SambaDomain/Attributes/sambaDomainName = $User/Attributes/sambaDomainName)
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
        attrs_get_list = [str(len(self.object_types.keys()))]
        for item in self.object_types.keys():
            attrs_get_list.append("$%s" % (item))
        attr_get_list = ", ".join(attrs_get_list)

        where_result += ['return(' + attr_get_list + ')']

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

        #TODO: We limit the results in python after we've applied ACLs...
        #if self.Limit:
        #    where_result =  ['return subsequence('] + where_result + [",%s,%s)" % (self.Limit[0].get_range())]

        result += where_result
        self._xquery = "\n".join(result)

    def execute(self, user=None):
        """
        Execute the created xquery and return only selected and accessible attributes.
        """
        start = time()

        # get the attribute mapping to be able to check the results
        # against the currently active aclsets.
        object_factory = ObjectFactory.getInstance()
        attrmap = {}
        for object_type in self.object_types:
            attrmap[object_type] = object_factory.getAttributeTypeMap(object_type)

        # Start the given query
        s_index = PluginRegistry.getInstance("ObjectIndex")
        xquery =  self.get_xquery()
        self.__env.log.debug("xquery statement:", xquery)

        q_res = s_index.xquery(xquery)

        # The list we return later
        result = []
        while(len(q_res)):

            # The first item tells us how many items are part of one result.
            # e.g.     2, User, Group, 2, User, Group
            length = int(q_res[0])
            items_data = q_res[1:1+length]
            q_res = q_res[1+length::]

            tmp = {}
            res = {}

            # Convert the resulting string into XML and then into a dict
            for item_data in items_data:
                item = self.recursive_dict(etree.XML(item_data), True)
                tmp[item['Type'][0]] = item

            # Check if all required objects were returned
            for otype in self.object_types.keys():
                if not otype in tmp:
                    raise Exception("Missing object in result")
                else:
                    res[otype] = {}

            # Extract the requested attributes out of the result.
            for suffix, name in self._selected_attributes:

                object_dn = tmp[suffix]['DN'][0]

                # Return all attributes
                if name == "*":

                    # Append all attributes of the object
                    if "Attributes" in tmp[suffix]:
                        for name in tmp[suffix]['Attributes'][0]:
                            if self.__has_access_to(user, object_dn, suffix, name):
                                res[suffix][name] = tmp[suffix]['Attributes'][0][name]

                    # Append special attributes like the DN etc.
                    for name in ('UUID', 'Type', 'DN', 'ParentDN'):
                        if name in tmp[suffix] and self.__has_access_to(user, object_dn, suffix, name):
                            res[suffix][name] = (tmp[suffix][name])

                    # Append extension if they exists
                    if 'Extensions' in tmp[suffix] and self.__has_access_to(user, object_dn, suffix, 'Extension'):
                        res[suffix]['Extension'] = map(lambda x: x, tmp[suffix]['Extensions'][0]['Extension'])
                else:

                    # Only append a selected list of attributes
                    path = self._get_attribute_location(name, False)
                    if path:
                        if path in tmp[suffix]:
                            if self.__has_access_to(user, object_dn, suffix, name):
                                if name in tmp[suffix][path][0]:
                                    res[suffix][name] = (tmp[suffix][path][0][name])
                                else:
                                    res[suffix][name] = []
                    elif self.__has_access_to(user, object_dn, suffix, name):
                        res[suffix][name] = (tmp[suffix][name])

            # Append the created item to the result.
            result.append(res)
        self.time = time() - start

        # Limitate resulting entries manually, due to the fact that we cannot filter by acls in the xquery
        if self.Limit:
            start, stop = self.Limit[0].get_range()
            result =  result[start:stop]
        return result

    def __has_access_to(self, user, object_dn, object_type, attr):
        """
        Checks whether the given user has access to the given object/attribute or not.
        """
        if user:
            topic = "%s.objects.%s.attributes.%s" % (self.__env.domain, object_type, attr)
            res = self.__acl_resolver.check(user, topic, "r", base=object_dn)
            return res
        else:
            return True

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
                self._attributes[complete] =  "%s/o:%s" % (path, attribute)
            else:
                self._attributes[complete] =  "o:%s" % (attribute)

    def _get_attribute_location(self, attribute, use_ns_prefix=True):
        """
        Returns the location for a given attribute

        e.g. the attribute 'Extension' would return 'Extensions'
        """
        if attribute in ['DN', 'UUID', 'Type', 'ParentDN']:
            return("")
        elif attribute in ['Extension']:
            return("o:Extensions" if use_ns_prefix else "Extensions")
        else:
            return("o:Attributes" if use_ns_prefix else "Attributes")

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
        Returns the compiled xquery.
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

            if(comp == "like"):
                match = ("contains(%s, %s)" % (attr1, attr2))
            elif(comp == "in"):
                match = ("(%s = %s)" % (attr1, attr2))
            else:
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
        """
        Returns the operator.
        """
        return (self[0])


class AttributeList(MyNode):
    """
    This node represents an attribute-list.

    e.g.

        User.uid in ("admin", "peter", "herman")
    """
    def compile_for_match(self):
        """
        Returns the value of this attribute-list.node so we can use it in
        xquery where statements.
        """
        items = ['"%s"' % x for x in self]
        return '(%s)' % (", ".join(items))


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
        """
        Returns the compiled xquery for collection-match.
        """
        if len(self) == 1:
            return self[0].compile()
        else:
            left = self[0].compile()
            right = self[2].compile()
            con = self[1].lower()
        return("(%s %s %s)" % (left, con, right))


class And(MyNode):
    def compile(self):
        """
        Returns the compiled xquery for collection-match.
        """
        left = self[0].compile()
        right = self[1].compile()
        return("(%s and %s)" % (left, right))


class Or(MyNode):
    def compile(self):
        """
        Returns the compiled xquery for collection-match.
        """
        left = self[0].compile()
        right = self[1].compile()
        return("(%s or %s)" % (left, right))


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
        """
        Return a xquery valid string
        """
        ret = str(self[0]).replace("(", "\\(").replace(")", "\\)").replace(" ", "\\ ")

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
            start = int(self[0])
            stop = int(self[1])
        else:
            start = 1
            stop = int(self[0])
        return(start, stop)


class OrderBy(MyNode):
    """
    Represents the ORDER BY statement
    """
    def compile_xquery(self):
        """
        Generate the resulting xquery for the 'order' statement

        ORDER BY <User.sn DESC, User.uid ASC>
        """
        return(", ".join(map(lambda x: x.compile_xquery(), self)))


class OrderedAttribute(MyNode):
    """
    This node represents the attributes that have to be ordered by the 'ORDER BY' statement
    """

    Direction = None
    Attribute = None

    def compile_xquery(self):
        """
        Compiles the xquery for an ordered-attribute

        ORDER BY <User.sn DESC>, <User.uid ASC>
        """
        if self.Direction:
            return("%s %s" % (self.Attribute[0].compile_for_match(), self.Direction[0].get_direction()))
        else:
            return("%s" % (self.Attribute[0].compile_for_match()))


class Direction(MyNode):
    """
    This node represents the order direction of the 'ORDER BY' attribute list.
    """
    def get_direction(self):
        """
        Returns the sort-direction.
        """
        return "ascending" if self[0] == 'ASC' else 'descending'


class SearchWrapper(Plugin):
    """
    This class is a search wrapper, which hides the xquery syntax from the user but allows
    to use a SQL like query syntax.

    E.g. a query for:

    >>> SELECT User.sn, User.cn, SambaDomain.sambaDomainName
    ... BASE SambaDomain SUB "dc=gonicus,dc=de"
    ... BASE User SUB "dc=gonicus,dc=de"
    ... WHERE (SambaDomain.sambaDomainName = User.sambaDomainName)
    ... ORDER BY User.sn, User.givenName DESC
    """
    instance = None
    query_parser = None

    implements(IInterfaceHandler)

    _priority_ = 21
    _target_ = 'core'

    def __init__(self):
        self._construct_parser()
        self.env = Environment.getInstance()

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

            string_list = Delayed()
            string_list+= String() & Optional(~Literal(',') & string_list)
            in_list = (~Literal("(") & string_list & ~Literal(")")) > AttributeList

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

            statement = (attribute | in_list | (String() > StringValue))
            operator = (Literal('=') | Literal('!=') | Literal('like') | Literal('in')) > Operator
            condition_tmp = statement & operator & statement

            # Allow to have brakets in condition statements
            condition = Delayed()
            negator = Literal('NOT')
            condition += condition_tmp | Optional(negator) & ~Literal('(') & condition & ~Literal(')') > Match

            # Allow to have joined condition in any possible variation
            group2, group3 = Delayed(), Delayed()
            parens = ~Literal('(') & group3 & ~Literal(')') > Collection
            group1 = parens | condition

            or_ = group1 & ~Literal('OR') & group2 > Or
            and_ = group1 & ~Literal('AND') & group2 > And
            group2 += or_ | and_ | group1

            add = group2 & ~Literal('OR') & group3 > Or
            sub = group2 & ~Literal('AND') & group3 > And
            group3 += add | sub | group2

            where = ~Literal('WHERE') & group3 > Where

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

    def execute(self, query, user=None):
        """
        Parses the given query and executes the resulting xquery statement.
        """
        self.env.log.debug("about to execute query '%s'" % query)
        q_o = self.query_parser.parse(query)[0]
        res = q_o.execute(user)
        self.env.log.debug("query took %ds" % q_o.time)
        return res

    def simple_search(self, base, scope, query, fltr=None, user=None):
        """
        Performs a query based on a simple search string consisting of keywords.
        """
        squery = 'SELECT User.* BASE User SUB "%s" WHERE User.uid like "%s" ORDER BY User.sn' % (base, query)
        return self.execute(squery)

    @staticmethod
    def get_instance():
        """
        Returns an instance of this class. This avoids instantiating this class everytime.
        """
        if not SearchWrapper.instance:
            SearchWrapper.instance = SearchWrapper()
        return SearchWrapper.instance

