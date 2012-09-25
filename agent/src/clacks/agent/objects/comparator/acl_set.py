import gettext
from clacks.agent.objects.comparator import ElementComparator
from clacks.agent.acl import ACLResolver
from pkg_resources import resource_filename #@UnresolvedImport


# Include locales
t = gettext.translation('messages', resource_filename("clacks.agent", "locale"), fallback=True)
_ = t.ugettext


class IsAclSet(ElementComparator):
    """
    Checks whether the given value is a valid AclSet.
    """

    def __init__(self, obj):
        super(IsAclSet, self).__init__()

    def process(self, all_props, key, value):

        # Check each property value
        entry_cnt = 0
        errors = []

        ares = ACLResolver.get_instance()
        rolenames = [n["name"] for n in ares.getACLRoles(None) if "name" in n]

        for entry in value:
            entry_cnt += 1

            if not "priority" in entry:
                errors.append(_("missing attribute 'priority' for acl-entry %s!" % (str(entry_cnt,))))
                return False, errors

            if not "members" in entry:
                errors.append(_("missing attribute 'members'! for acl-entry %s!" % (str(entry_cnt,))))
                return False, errors

            if "rolename" in entry:

                if "actions" in entry and entry["actions"]:
                    errors.append(_("you can either use a rolename or actions but not both!"))
                    return False, errors

                # If a 'rolename' is we do not allow other dict, keys
                if type(entry["rolename"]) not in [str, unicode]:
                    errors.append(_("expected attribute '%s' to be of type '%s' but found '%s!'" % ("rolename", str, type(entry["rolename"]))))
                    return False, errors

                # Ensure that the given role exists....
                if not entry["rolename"] in rolenames:
                    print rolenames
                    errors.append(_("unknown role %s used!" % entry["rolename"]))
                    return False, errors

            else:

                if not "scope" in entry:
                    errors.append(_("missing attribute 'scope' for acl-entry %s!" % (str(entry_cnt,))))
                    return False, errors

                if not "actions" in entry:
                    errors.append(_("missing attribute 'actions'! for acl-entry %s!" % (str(entry_cnt,))))
                    return False, errors

                for item in entry['actions']:

                    # Check  if the required keys 'topic' and 'acl' are present
                    if not "topic" in item:
                        errors.append(_("missing attribute 'topic'!"))
                        return False, errors
                    if not "acl" in item:
                        errors.append(_("missing attribute 'acl'!"))
                        return False, errors

                    # Check for the correct attribute types
                    if not type(item["topic"]) in [str, unicode]:
                        errors.append(_("expected attribute '%s' to be of type '%s' but found '%s!'" % ("topic", str, type(item["topic"]))))
                        return False, errors
                    if not type(item["acl"]) in [str, unicode]:
                        errors.append(_("expected attribute '%s' to be of type '%s' but found '%s!'" % ("topic", str, type(item["topic"]))))
                        return False, errors

                    # Check for a correct value for acls
                    if not all(map(lambda x: x in 'crowdsexm', item['acl'])):
                        errors.append(_("invalid acl attribute given, allowed is a combination of 'crowdsexm'!'"))
                        return False, errors

                    # Check if there are unsupported keys given
                    keys = item.keys()
                    keys.remove("topic")
                    keys.remove("acl")
                    if "options" in item:
                        keys.remove("options")
                    if len(keys):
                        errors.append(_("invalid attributes given '%s', allowed are 'rolename, topic, acl, options'!" % (', '.join(keys))))
                        return False, errors

                    if "options" in item and not type(item["options"]) in [dict]:
                        errors.append(_("expected attribute '%s' to be of type '%s' but found '%s!'" % ("options", dict, type(item["options"]))))
                        return False, errors

        return True, errors
