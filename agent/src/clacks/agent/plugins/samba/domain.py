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

from datetime import date, datetime
from time import mktime
import smbpasswd #@UnresolvedImport
from clacks.common.utils import N_
from zope.interface import implements
from clacks.common.components import Plugin
from clacks.common.handler import IInterfaceHandler
from clacks.common import Environment
from clacks.common.components import PluginRegistry
from clacks.common.components import Command
from clacks.agent.objects.proxy import ObjectProxy
from clacks.agent.objects.comparator import ElementComparator


class SambaGuiMethods(Plugin):
    implements(IInterfaceHandler)
    _target_ = 'gosa'
    _priority_ = 80


    @Command(needsUser=True, __help__=N_("Sets a new samba-password for a user"))
    def setSambaPassword(self, user, object_dn, password):
        """
        Set a new samba-password for a user
        """

        # Do we have read permissions for the requested attribute
        env = Environment.getInstance()
        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "sambaNTPassword")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "w", base=object_dn):
            self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                user, "isLocked", object_dn, topic, "w"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        topic = "%s.objects.%s.attributes.%s" % (env.domain, "User", "sambaLMPassword")
        aclresolver = PluginRegistry.getInstance("ACLResolver")
        if not aclresolver.check(user, topic, "w", base=object_dn):
            self.__log.debug("user '%s' has insufficient permissions to write %s on %s, required is %s:%s" % (
                user, "isLocked", object_dn, topic, "w"))
            raise ACLException(C.make_error('PERMISSION_ACCESS', topic, target=object_dn))

        # Set the password and commit the changes
        lm, nt = smbpasswd.hash(password)
        user = ObjectProxy(object_dn)
        user.sambaNTPassword = nt
        user.sambaLMPassword = lm
        user.commit()

    @Command(needsUser=True, __help__=N_("Returns the current samba domain policy for a given user"))
    def getSambaDomainInformation(self, user, target_object):

        print "-------> ACL check for user", user

        # Use proxy if available
        _self = target_object

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
        res = index.search({'_type': 'SambaDomain', 'sambaDomainName': _self.sambaDomainName}, dict(zip(domain_attributes, [1 for n in domain_attributes])))
        if not res.count():
            return("invalid domain selected")

        attrs = {}
        for item in domain_attributes:
            if item in res[0]:
                try:
                    attrs[item] = int(res[0][item][0])
                except:
                    attrs[item] = "unset"
            else:
                attrs[item] = "unset"

        for item in user_attributes:
            if getattr(_self, item):
                try:
                    if type(getattr(_self, item)) == datetime:
                        attrs[item] =  mktime(getattr(_self, item).timetuple())
                    else:
                        attrs[item] = int(getattr(_self, item))
                except Exception as e:
                    attrs[item] = "unset"
            else:
                attrs[item] = "unset"

        if attrs['sambaPwdMustChange'] and attrs['sambaPwdMustChange'] != "unset":
            attrs['sambaPwdMustChange'] = date.fromtimestamp(attrs['sambaPwdMustChange']).strftime("%d.%m.%Y")
        if attrs['sambaKickoffTime'] and attrs['sambaKickoffTime'] != "unset":
            attrs['sambaKickoffTime'] = date.fromtimestamp(attrs['sambaKickoffTime']).strftime("%d.%m.%Y")

        # sambaMinPwdLength: Password length has a default of 5
        if attrs['sambaMinPwdLength'] == "unset" or attrs['sambaMinPwdLength'] == 5:
            attrs['sambaMinPwdLength'] = "5 <i>(" + _("default") + ")</i>"

        # sambaPwdHistoryLength: Length of Password History Entries (default: 0 => off)
        if attrs['sambaPwdHistoryLength'] == "unset" or attrs['sambaPwdHistoryLength'] == 0:
            attrs['sambaPwdHistoryLength'] = _("Off") + " <i>(" + _("default") + ")</i>"

        # sambaLogonToChgPwd: Force Users to logon for password change (default: 0 => off, 2 => on)
        if attrs['sambaLogonToChgPwd'] == "unset" or attrs['sambaLogonToChgPwd'] == 0:
            attrs['sambaLogonToChgPwd'] = _("Off") + " <i>(" + _("default") + ")</i>"
        else:
            attrs['sambaLogonToChgPwd'] = _("On")

        # sambaMaxPwdAge: Maximum password age, in seconds (default: -1 => never expire passwords)'
        if attrs['sambaMaxPwdAge'] == "unset" or attrs['sambaMaxPwdAge'] <= 0:
            attrs['sambaMaxPwdAge'] = _("disabled") + " <i>(" + _("default") + ")</i>"
        else:
            attrs['sambaMaxPwdAge'] += " " + _("seconds")

        # sambaMinPwdAge: Minimum password age, in seconds (default: 0 => allow immediate password change
        if attrs['sambaMinPwdAge'] == "unset" or attrs['sambaMinPwdAge'] <= 0:
            attrs['sambaMinPwdAge'] = _("disabled") + " <i>(" + _("default") + ")</i>"
        else:
            attrs['sambaMinPwdAge'] += " " + _("seconds")

        # sambaLockoutDuration: Lockout duration in minutes (default: 30, -1 => forever)
        if attrs['sambaLockoutDuration'] == "unset" or attrs['sambaLockoutDuration'] == 30:
            attrs['sambaLockoutDuration'] = "30 " + _("minutes") + " <i>(" + _("default") + ")</i>"
        elif attrs['sambaLockoutDuration'] == -1:
            attrs['sambaLockoutDuration'] = _("forever")
        else:
            attrs['sambaLockoutDuration'] += " " + _("minutes")

        # sambaLockoutThreshold: Lockout users after bad logon attempts (default: 0 => off
        if attrs['sambaLockoutThreshold'] == "unset" or attrs['sambaLockoutThreshold'] == 0:
            attrs['sambaLockoutThreshold'] = _("disabled") + " <i>(" + _("default") + ")</i>"

        # sambaForceLogoff: Disconnect Users outside logon hours (default: -1 => off, 0 => on
        if attrs['sambaForceLogoff'] == "unset" or attrs['sambaForceLogoff'] == -1:
            attrs['sambaForceLogoff'] = _("off") + " <i>(" + _("default") + ")</i>"
        else:
            attrs['sambaForceLogoff'] = _("on")

        # sambaRefuseMachinePwdChange: Allow Machine Password changes (default: 0 => off
        if attrs['sambaRefuseMachinePwdChange'] == "unset" or attrs['sambaRefuseMachinePwdChange'] == 0:
            attrs['sambaRefuseMachinePwdChange'] = _("off") + " <i>(" + _("default") + ")</i>"
        else:
            attrs['sambaRefuseMachinePwdChange'] = _("on")

        # sambaBadPasswordTime: Time of the last bad password attempt
        if attrs['sambaBadPasswordTime'] == "unset" or not attrs['sambaBadPasswordTime']:
            attrs['sambaBadPasswordTime'] = "<i>(" + _("unset") + ")</i>"
        else:
            attrs['sambaRefuseMachinePwdChange'] = date.fromtimestamp(attrs['sambaBadPasswordTime']).strftime("%d.%m.%Y")

        # sambaBadPasswordCount: Bad password attempt count
        if attrs['sambaBadPasswordCount'] == "unset" or not attrs['sambaBadPasswordCount']:
            attrs['sambaBadPasswordCount'] = "<i>(" + _("unset") + ")</i>"
        else:
            attrs['sambaBadPasswordCount'] = date.fromtimestamp(attrs['sambaBadPasswordCount']).strftime("%d.%m.%Y")

        # sambaPwdLastSet: Timestamp of the last password update
        if attrs['sambaPwdLastSet'] == "unset" or not attrs['sambaPwdLastSet']:
            attrs['sambaPwdLastSet'] = "<i>(" + _("unset") + ")</i>"
        else:
            attrs['sambaPwdLastSet'] = date.fromtimestamp(attrs['sambaPwdLastSet']).strftime("%d.%m.%Y")

        # sambaLogonTime: Timestamp of last logon
        if attrs['sambaLogonTime'] == "unset" or not attrs['sambaLogonTime']:
            attrs['sambaLogonTime'] = "<i>(" + _("unset") + ")</i>"
        else:
            attrs['sambaLogonTime'] = date.fromtimestamp(attrs['sambaLogonTime']).strftime("%d.%m.%Y")

        # sambaLogoffTime: Timestamp of last logoff
        if attrs['sambaLogoffTime'] == "unset" or not attrs['sambaLogoffTime']:
            attrs['sambaLogoffTime'] = "<i>(" + _("unset") + ")</i>"
        else:
            attrs['sambaLogoffTime'] = date.fromtimestamp(attrs['sambaLogoffTime']).strftime("%d.%m.%Y")

        # sambaKickoffTime: Timestamp of when the user will be logged off automatically
        if attrs['sambaKickoffTime'] == "unset" or not attrs['sambaKickoffTime']:
            attrs['sambaKickoffTime'] = "<i>(" + _("unset") + ")</i>"

        # sambaPwdMustChange: Timestamp of when the password will expire
        if attrs['sambaPwdMustChange'] == "unset" or not attrs['sambaPwdMustChange']:
            attrs['sambaPwdMustChange'] = "<i>(" + _("unset") + ")</i>"

        # sambaPwdCanChange: Timestamp of when the user is allowed to update the password
        time_now = mktime(datetime.now().timetuple())
        if attrs['sambaPwdCanChange'] == "unset" or not attrs['sambaPwdCanChange']:
            attrs['sambaPwdCanChange'] = "<i>(" + _("unset") + ")</i>"
        elif attrs['sambaPwdCanChange'] != "unset" and time_now > attrs['sambaPwdCanChange']:
            attrs['sambaPwdCanChange'] = _("immediately")
        else:
            days = int((attrs['sambaPwdCanChange'] - time_now) / (60*60*24))
            hours = int(((attrs['sambaPwdCanChange'] - time_now) / (60*60)) % 24)
            minutes = int(((attrs['sambaPwdCanChange'] - time_now) / (60)) % 60)
            attrs['sambaPwdCanChange'] = " " + days    + " " + _("days")
            attrs['sambaPwdCanChange']+= " " + hours   + " " + _("hours")
            attrs['sambaPwdCanChange']+= " " + minutes + " " + _("minutes")


        res = "\n<div style='height:200px; overflow: auto;'>" + \
            "\n<table style='width:100%;'>" + \
            "\n<tr><td><b>" + _("Domain attributes") + "</b></td></tr>" + \
            "\n<tr><td>" + _("Min password length") + ":           </td><td>" + attrs['sambaMinPwdLength'] + "</td></tr>" + \
            "\n<tr><td>" + _("Min password length") + ":           </td><td>" + attrs['sambaMinPwdLength'] + "</td></tr>" + \
            "\n<tr><td>" + _("Password history") + ":              </td><td>" + attrs['sambaPwdHistoryLength'] + "</td></tr>" + \
            "\n<tr><td>" + _("Force password change") + ":         </td><td>" + attrs['sambaLogonToChgPwd'] + "</td></tr>" + \
            "\n<tr><td>" + _("Maximum password age") + ":          </td><td>" + attrs['sambaMaxPwdAge'] + "</td></tr>" + \
            "\n<tr><td>" + _("Minimum password age") + ":          </td><td>" + attrs['sambaMinPwdAge'] + "</td></tr>" + \
            "\n<tr><td>" + _("Lockout duration") + ":              </td><td>" + attrs['sambaLockoutDuration'] + "</td></tr>" + \
            "\n<tr><td>" + _("Bad lockout attempt") + ":           </td><td>" + attrs['sambaLockoutThreshold'] + "</td></tr>" + \
            "\n<tr><td>" + _("Disconnect time") + ":               </td><td>" + attrs['sambaForceLogoff'] + "</td></tr>" + \
            "\n<tr><td>" + _("Refuse machine password change") + ":</td><td>" + attrs['sambaRefuseMachinePwdChange'] + "</td></tr>" + \
            "\n<tr><td>&nbsp;</td></tr>" + \
            "\n<tr><td><b>" + _("User attributes") + "</b></td></tr>" + \
            "\n<tr><td>" + _("SID") + ":                           </td><td>" + attrs['sambaSID'] + "</td></tr>" + \
            "\n<tr><td>" + _("Last failed login") + ":             </td><td>" + attrs['sambaBadPasswordTime'] + "</td></tr>" + \
            "\n<tr><td>" + _("Log on attempts") + ":                </td><td>"+ attrs['sambaBadPasswordCount'] + "</td></tr>" + \
            "\n<tr><td>" + _("Last password update") + ":          </td><td>" + attrs['sambaPwdLastSet'] + "</td></tr>" + \
            "\n<tr><td>" + _("Last log on") + ":                    </td><td>"+ attrs['sambaLogonTime'] + "</td></tr>" + \
            "\n<tr><td>" + _("Last log off") + ":                   </td><td>"+ attrs['sambaLogoffTime'] + "</td></tr>" + \
            "\n<tr><td>" + _("Automatic log off") + ":              </td><td>"+ attrs['sambaKickoffTime'] + "</td></tr>";

        return res


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
