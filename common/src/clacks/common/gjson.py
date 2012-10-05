# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import json


def dumps(obj, encoding='utf-8'):
    return json.dumps(obj, encoding=encoding, cls=PObjectEncoder)


def loads(json_string, encoding='utf-8'):
    return json.loads(json_string, encoding=encoding, object_hook=PObjectDecoder)


from clacks.common.components.jsonrpc_utils import PObjectEncoder, PObjectDecoder
