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


class Plugin(object):
    """
    The Plugin object is just a marker in the moment: it lacks special
    code. While being a marker, there's a mandatory class member that must
    be maintained by users: ``_target_``

    The ``_target_`` class member determines what queue the plugin will be
    registered on. The target queue is assembled by the clacks *domain* and
    the *_target_*. Plugins that do not offer common functionality should
    register on something else than *core*.

    In this example, we create a sample plugin which is listening on
    ``<domain>.sample`` (domain is *org.clacks* if you didn't change the
    configuration), which makes it possible that only agents having this
    module installed get related messages::

        >>> from clacks.common import Environment
        >>> from clacks.common.components import Command, Plugin
        >>>
        >>> class SampleModule(Plugin):
        ...     _target_ = 'sample'
        ...
        ...     @Command(__help__=N_("Return a pre-defined message to the caller"))
        ...     def hello(self, name="unknown"):
        ...         return _("Hello %s!") % name

    """
    _target_ = None
    _locale_module_ = 'clacks.common'

    def get_target(self):
        return self._target_

    def get_locale_module(self):
        return self._locale_module_
