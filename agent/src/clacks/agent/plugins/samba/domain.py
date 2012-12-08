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

from clacks.common.utils import N_
from zope.interface import implements
from clacks.common.components import Plugin
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import PluginRegistry
from clacks.common.components import Command
from clacks.agent.objects.comparator import ElementComparator


class SambaGuiMethods(Plugin):
    implements(IInterfaceHandler)
    _target_ = 'gosa'
    _priority_ = 80

    @Command(__help__=N_("Returns the current samba domain policy for a given user"))
    def getSambaDomainInformation(self, target_object):

        # Use proxy if available
        _self = target_object
        try:
            _self = target_object.parent
        except:
            pass

        print type(_self);

        sambaMinPwdLength = "unset"
        sambaPwdHistoryLength = "unset"
        sambaLogonToChgPwd = "unset"
        sambaMaxPwdAge = "unset"
        sambaMinPwdAge = "unset"
        sambaLockoutDuration = "unset"
        sambaLockoutThreshold = "unset"
        sambaForceLogoff = "unset"
        sambaRefuseMachinePwdChange = "unset"
        sambaPwdLastSet = "unset"
        sambaLogonTime = "unset"
        sambaLogoffTime = "unset"
        sambaKickoffTime = "unset"
        sambaPwdCanChange = "unset"
        sambaPwdMustChange = "unset"
        sambaBadPasswordCount = "unset"
        sambaBadPasswordTime = "unset"

        # Domain attributes
        domain_attributes = ["sambaMinPwdLength","sambaPwdHistoryLength","sambaMaxPwdAge",
                "sambaMinPwdAge","sambaLockoutDuration","sambaRefuseMachinePwdChange",
                "sambaLogonToChgPwd","sambaLockoutThreshold","sambaForceLogoff"]

        # User attributes
        user_attributes = ["sambaBadPasswordTime","sambaPwdLastSet","sambaLogonTime","sambaLogoffTime",
                "sambaKickoffTime","sambaPwdCanChange","sambaPwdMustChange","sambaBadPasswordCount", "sambaSID"]

        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'SambaDomain', 'sambaDomainName': _self.sambaDomainName}, {'dn': 1})
        print res.count()
        print {'_type': 'SambaDomain', 'sambaDomainName': _self.sambaDomainName}
        if not res.count():
            print "Ne"

        for item in res:
            print item


        #$ldap = $this->config->get_ldap_link();
        #$ldap->cd($this->config->current['BASE']);
        #if(!empty($this->sambaDomainName) && isset($this->config->data['SERVERS']['SAMBA'][$this->sambaDomainName])){
        #    $attrs = $this->get_domain_info();
        #    foreach($domain_attributes as $attr){
        #        if(isset($attrs[$attr])){
        #            $$attr = $attrs[$attr][0];
        #        }
        #    }
        #}

















        return target_object.dn


class IsValidSambaDomainName(ElementComparator):
    """
    Validates a given sambaDomainName.
    """

    def __init__(self, obj):
        super(IsValidSambaDomainName, self).__init__()

    def process(self, all_props, key, value):
        domain = value[0]
        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.search({'_type': 'SambaDomain', 'sambaDomainName': domain},
            {'_uuid': 1})

        if res.count():
            return True, errors

        errors.append(dict(index=0, detail=N_("Unknown domain '%(domain)s'"), domain=value[0]))

        return False, errors
