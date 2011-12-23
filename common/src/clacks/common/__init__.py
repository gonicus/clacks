# -*- coding: utf-8 -*-
"""
The *common* library bundles a couple of shared resources that are needed
by more than one component. It also includes base XML data which is required
for over all schema checking.

Here is an example on how to use the common module::

    >>> from clacks.common import Environment
    >>> env = Environment.getInstance()

This loads the clacks environment information using the Environment singleton.

.. note::

    Using the environment requires the presence of the clacks configuration
    file - commonly ``~/.clacks/config`` or ``/etc/clacks/config`` in this
    order
"""

__version__ = __import__('pkg_resources').get_distribution('clacks.common').version
__import__('pkg_resources').declare_namespace(__name__)

from clacks.common.env import Environment
