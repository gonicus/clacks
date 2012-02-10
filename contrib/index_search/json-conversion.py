#!/usr/bin/env python

from pprint import pprint
from lxml import etree
from lxml import objectify
from clacks.agent.xmldb.handler import XMLDBHandler
from StringIO import StringIO

from json import loads, dumps

xmldb = XMLDBHandler.get_instance()
xmldb.setNamespace('objects', 'xs', "http://www.w3.org/2001/XMLSchema")


query = """

declare function local:get_attributes_as_json ($x as node(), $attrs as item()*)
as xs:string
{
    (: Extracts the given list of attributes from an entry
       and returns a json compatible list.
    :)
    concat("{",
            string-join(
            for $attr in $x/Attributes/*
            where (string(node-name($attr)) = $attrs)
            return concat(
                local:create_json_key(string(node-name($attr))),
                ": ",
                local:create_json_value(string($attr/text()))
            ),
        ", "),
    "}")
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

declare function local:create_json_entry($name as xs:string, $value as xs:string)
as xs:string
{
    (: Combines a key and a value pait into a useable json sequence.
        "<key>": <value>
    :)
    concat(local:create_json_key($name), ": ", $value)
};


let $objs := collection('objects')//%(type)s
for $obj in $objs

    let $attrs := (%(attributes)s)
    let $attributes := local:get_attributes_as_json($obj, $attrs)

    let $json_dn := local:create_json_entry('dn', local:create_json_value($obj/DN/string()))
    let $json_attributes := local:create_json_entry('attributes', $attributes)

    let $json_elements := ($json_dn, $json_attributes)
    let $json_result := concat("{", string-join($json_elements, ","), "}")

    (:where $obj/Attributes/cn[contains(., 'ten')]:)
    order by $obj/Attributes/cn/text()
    return $json_result

""" % { 'type': 'User',
        'attributes': ", ".join(["'sn'", "'givenName'", "'uid'", "'userPassword'"])
      }

res = xmldb.xquery(query)
pprint(res)

try:
    for entry in res:
        print "-" * 20
        pprint(loads(entry))
except Exception as e:
    print entry
    print "Nope!!", e
    raise

print len(res)
