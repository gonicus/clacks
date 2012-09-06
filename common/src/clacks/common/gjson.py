# -*- coding: utf-8 -*-
import json


def dumps(obj, encoding='utf-8'):
    return json.dumps(obj, encoding=encoding, cls=PObjectEncoder)


def loads(json_string, encoding='utf-8'):
    return json.loads(json_string, encoding=encoding, object_hook=PObjectDecoder)


from clacks.common.components.jsonrpc_utils import PObjectEncoder, PObjectDecoder
