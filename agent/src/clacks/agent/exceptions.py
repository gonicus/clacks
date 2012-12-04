#!/usr/bin/env python
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
from clacks.common.error import ClacksErrorHandler as ClacksException


class ACLException(ClacksException):
    pass


class CommandInvalid(ClacksException):
    """ Exception which is raised when the command is not valid. """
    pass


class CommandNotAuthorized(ClacksException):
    """ Exception which is raised when the call was not authorized. """
    pass


class HTTPException(ClacksException):
    pass


class LDAPException(ClacksException):
    pass


class LockError(ClacksException):
    pass


class ConversationNotSupported(ClacksException):
    pass


class FilterException(ClacksException):
    pass


class IndexException(ClacksException):
    pass


class FactoryException(ClacksException):
    pass


class ProxyException(ClacksException):
    pass


class ObjectException(ClacksException):
    pass


class ElementFilterException(ClacksException):
    pass


class EntryNotUnique(ClacksException):
    pass


class EntryNotFound(ClacksException):
    pass


class DNGeneratorError(ClacksException):
    """
    Exception thrown for dn generation errors
    """
    pass


class RDNNotSpecified(ClacksException):
    """
    Exception thrown for missing rdn property in object definitions
    """
    pass


class BackendError(ClacksException):
    """
    Exception thrown for unknown objects
    """
    pass


class ProxyError(ClacksException):
    pass
