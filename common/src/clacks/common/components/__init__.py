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

"""
The compoments module gathers a couple of common components that are of
use for both agents and clients.
"""
__import__('pkg_resources').declare_namespace(__name__)
from clacks.common.components.amqp_proxy import AMQPServiceProxy
from clacks.common.components.amqp_proxy import AMQPEventConsumer
from clacks.common.components.amqp_proxy import AMQPStandaloneWorker
from clacks.common.components.objects import ObjectRegistry
from clacks.common.components.amqp import AMQPHandler
from clacks.common.components.amqp import AMQPWorker
from clacks.common.components.amqp import AMQPProcessor
from clacks.common.components.amqp import EventProvider
from clacks.common.components.amqp import EventConsumer
from clacks.common.components.command import Command
from clacks.common.components.command import CommandInvalid
from clacks.common.components.command import CommandNotAuthorized
from clacks.common.components.dbus_runner import DBusRunner
from clacks.common.components.jsonrpc_proxy import JSONRPCException
from clacks.common.components.jsonrpc_proxy import JSONObjectFactory
from clacks.common.components.jsonrpc_proxy import JSONServiceProxy
from clacks.common.components.plugin import Plugin
from clacks.common.components.registry import PluginRegistry
from clacks.common.components.zeroconf_client import ZeroconfClient
from clacks.common.components.zeroconf import ZeroconfService
