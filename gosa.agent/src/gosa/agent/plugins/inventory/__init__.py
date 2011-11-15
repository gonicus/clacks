from gosa.agent.plugins.inventory.consumer import InventoryConsumer
from gosa.common.components import AMQPEventConsumer
from gosa.common.components.amqp import EventConsumer
from gosa.common.components.registry import PluginRegistry


__import__('pkg_resources').declare_namespace(__name__)


# Create event consumer
c = InventoryConsumer()

amqp = PluginRegistry.getInstance('AMQPHandler')
EventConsumer(self.env,
    amqp.getConnection(),
    xquery="""
        declare namespace f='http://www.gonicus.de/Events';
        let $e := ./f:Event
        return $e/f:Inventory
    """,
    callback=c.process)
