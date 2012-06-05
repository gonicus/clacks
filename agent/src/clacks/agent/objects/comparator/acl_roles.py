import gettext
from clacks.agent.objects.comparator import ElementComparator
from clacks.agent.acl import ACLResolver
from pkg_resources import resource_filename


# Include locales
t = gettext.translation('messages', resource_filename("clacks.agent", "locale"), fallback=True)
_ = t.ugettext


class IsAclRole(ElementComparator):
    """
    Checks whether the given value is a valid AclRole.
    """

    def __init__(self, obj):
        super(IsAclRole, self).__init__()

    def process(self, key, value, errors=[]):

        # Check each property value
        entry_cnt = 0

        ares = ACLResolver.get_instance()
        rolenames = [n["name"] for n in ares.getACLRoles(None) if "name" in n]

        for entry in value:
            entry_cnt += 1

            if not "priority" in entry:
                errors.append(_("missing attribute 'priority' for acl-entry %s!" % (str(entry_cnt,))))
                return False

            if "rolename" in entry:

                if "actions" in entry and entry["actions"]:
                    errors.append(_("you can either use a rolename or actions but not both!"))
                    return False

                # If a 'rolename' is we do not allow other dict, keys
                if type(entry["rolename"]) not in [str, unicode]:
                    errors.append(_("expected attribute '%s' to be of type '%s' but found '%s!'" % ("rolename", str, type(entry["rolename"]))))
                    return False

                # Ensure that the given role exists....
                if not entry["rolename"] in rolenames:
                    errors.append(_("unknown role %s used!" % entry["rolename"]))
                    return False

            else:

                if not "scope" in entry:
                    errors.append(_("missing attribute 'scope' for acl-entry %s!" % (str(entry_cnt,))))
                    return False

                if not "actions" in entry:
                    errors.append(_("missing attribute 'actions'! for acl-entry %s!" % (str(entry_cnt,))))
                    return False

                for item in entry['actions']:

                    # Check  if the required keys 'topic' and 'acl' are present
                    if not "topic" in item:
                        errors.append(_("missing attribute 'topic'!"))
                        return False
                    if not "acl" in item:
                        errors.append(_("missing attribute 'acl'!"))
                        return False

                    # Check for the correct attribute types
                    if not type(item["topic"]) in [str, unicode]:
                        errors.append(_("expected attribute '%s' to be of type '%s' but found '%s!'" % ("topic", str, type(item["topic"]))))
                        return False
                    if not type(item["acl"]) in [str, unicode]:
                        errors.append(_("expected attribute '%s' to be of type '%s' but found '%s!'" % ("topic", str, type(item["topic"]))))
                        return False

                    # Check for a correct value for acls
                    if not all(map(lambda x: x in 'rwcdsex', item['acl'])):
                        errors.append(_("invalid acl attribute given, allowed is a combination of 'rwcdsex'!'"))
                        return False

                    # Check if there are unsupported keys given
                    keys = item.keys()
                    keys.remove("topic")
                    keys.remove("acl")
                    if "options" in item:
                        keys.remove("options")
                    if len(keys):
                        errors.append(_("invalid attributes given '%s', allowed are 'rolename, topic, acl, options'!" % (', '.join(keys))))
                        return False

                    if "options" in item and not type(item["options"]) in [dict]:
                        errors.append(_("expected attribute '%s' to be of type '%s' but found '%s!'" % ("options", dict, type(item["options"]))))
                        return False

        return True

