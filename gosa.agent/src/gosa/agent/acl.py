# -*- coding: utf-8 -*-
import re
import os
import json
import ldap

from zope.interface import implements
from gosa.common.handler import IInterfaceHandler
from gosa.common import Environment
from gosa.agent.ldap_utils import LDAPHandler
from gosa.common.components import Command, PluginRegistry


#TODO: Think about ldap relations, how to store and load objects.
#TODO: What about object groups, to be able to inlcude clients?
#TODO: Groups are not supported yet


"""
This is a collection of classes that can manage Access control lists.


ACLSet
======
The base class of all ACL assignments is the 'ACLSet' class which
combines a list of 'ACL' entries into a set of effective ACLs.

The ACLSet has a location property which specifies the location, this set of
acls, is valid for. E.g. dc=example,dc=net


ACL
===
The ACL class contains information about the acl definition, like
    |-> the scope
    |-> the users this acl is valid for
    |-> the actions described by
      |-> target    e.g. com.gonicus.objectFactory.Person.*
      |-> acls      e.g. rwxd
      |-> options   e.g. uid=hickert
    OR
      |-> role      The role to use instead of a direct acls


ACLRole
=======
This class equals the 'ACLSet' but in details it does not have a location, it
has just a name. This name can be used later in 'ACL' classes to refer to
this acl role.

And instead of ACL-objects it uses ACLRoleEntry-objects to assemble a set of acls.
(ACLRoleEntry objects have no members)


ACLRoleEntry
============
ACLRoleEntries are used in 'ACLRole' objects to combine several allowed
actions.


==========
ACLResoler

The ACLResolver is responsible for loading, saving and resolving permissions.


How an ACL assigment look could look like
=========================================

ACLRole (test1)
 |-> ACLRoleEntry
 |-> ACLRoleEntry

ACLSet
 |-> ACL
 |-> ACL
 |-> ACLRole (test1)
 |-> ACL

"""


class ACLSet(list):
    """
    This is a container for ACL entries.
    """
    location = None

    def __init__(self, location):
        self.location = location

    def get_location(self):
        """
        Returns the location for this ACLSet.
        """
        return(self.location)

    def remove_acls_for_user(self, user):
        """
        Removes all permissions for the given user form this aclset.
        """
        for acl in self:
            if user in acl.members:
                acl.members.remove(user)

    def remove_acl(self, acl):
        """
        Removes an acl entry fromt this ACLSet.
        """
        for cur_acl in self:
            if cur_acl == acl:
                self.remove(acl)
                return True
        return False

    def add(self, item):
        """
        Adds a new acl object to this aclSet.
        """
        if type(item) != ACL:
            raise TypeError('item is not of type %s' % ACL)

        if item.priority == None:
            item.priority = len(self)

        self.append(item)

        # Sort Acl items by id
        self.sort(key=lambda item: (item.priority * -1))

    def __repr__(self):
        return(self.repr_self(self))

    def repr_self(self, entry, indent = 0):
        rstr = ""
        if type(entry) == ACLSet:
            rstr += "%s<ACLSet: %s>" % (" " * indent, entry.location)
            for sub_entry in entry:
                rstr += self.repr_self(sub_entry, indent)

        if type(entry) == ACL:
            rstr += entry.repr_self(indent + 1)

        return rstr


class ACLRole(list):
    """
    This is a container for ACL entries that should act like an acl role.
    """
    name = None
    priority = None

    def __init__(self, name):
        self.name = name

    def add(self, item):
        """
        Adds a new acl object to this aclSet.
        """
        if type(item) != Acl:
            raise TypeError('item is not of type %s' % Acl)

        if item.priority == None:
            item.priority = len(self)

        self.append(item)

        # Sort Acl items by id
        self.sort(key=lambda item: (item.priority * -1))

    def get_name(self):
        """
        Returns the name of the role.
        """
        return self.name

    def add(self, item):
        """
        Adds a new acl object to this aclSet.
        """
        if type(item) != ACLRoleEntry:
            raise TypeError('item is not of type %s' % ACLRoleEntry)

        if item.priority == None:
            item.priority = len(self)

        self.append(item)

        # Sort ACL items by id
        sorted(self, key=lambda item: item.priority)

    def __repr__(self):
        return(self.repr_self(self))

    def repr_self(self, entry, indent = 0):
        rstr = ""
        if type(entry) == ACLRole:
            rstr += "%s<ACLRole: %s>" % (" " * indent, entry.name)
            for sub_entry in entry:
                rstr += self.repr_self(sub_entry, indent)

        if type(entry) == ACLRoleEntry:
            rstr += entry.repr_self(indent + 1)

        return rstr


class ACL(object):
    """
    The ACL class contains list of action for a set of members.
    These ACL classes can then be bundled and attached to a ldap base using
    the ACLSet class.
    """
    priority = None

    ONE = 1
    SUB = 2
    PSUB = 3
    RESET = 4

    members = None
    actions = None
    scope = None

    uses_role = False
    role = None

    def __init__(self, scope=None, role=None):
        self.env = Environment.getInstance()

        if scope == None:
            scope = ACL.SUB

        if scope not in (ACL.ONE, ACL.SUB, ACL.PSUB, ACL.RESET):
            raise(Exception("Invalid ACL type given"))

        self.scope = scope
        self.actions = []
        self.locations = []
        self.members = []

        if role:
            self.use_role(role)

    def use_role(self, role):
        """
        Mark this ACL to use a role instead of direkt permission settings.
        """
        self.uses_role = True
        self.role = role.name

    def set_priority(self, priority):
        self.priority = priority

    def add_member(self, member):
        """
        Adds a new member to this acl.
        """
        if type(member) != unicode:
            raise(Exception("Member should be of type str!"))
        self.members.append(member)

    def add_members(self, members):
        """
        Adds a list of new members to this acl.
        """
        if type(members) != list:
            raise(Exception("Requires a list of members!"))

        for member in members:
            self.add_member(member)

    def add_action(self, target, acls, options):
        """
        Adds a new action to this acl.
        """
        if self.uses_role:
            raise Exception("ACL classes that use a role cannot define"
                   " additional costum acls!")

        acl = {
                'target': target,
                'acls': acls,
                'options': options}
        self.actions.append(acl)

    def get_members(self):
        """
        Returns the list of members this ACL is valid for.
        """
        return(self.member)

    def repr_self(self, indent = 0):
        """
        Generates a human readable representation of the acl-object.
        """
        if self.uses_role:
            r = ACLResolver.instance
            rstr = "\n%s<ACL> %s" % (" " * indent, str(self.members))
            rstr += "\n%s:" %  r.acl_roles[self.role].repr_self(r.acl_roles[self.role], indent + 1)

        else:
            rstr = "\n%s<ACL scope(%s)> %s: " % ((" " * indent), self.scope, str(self.members))
            for entry in self.actions:
                rstr += "\n%s%s:%s %s" % ((" " * (indent+1)), entry['target'], str(entry['acls']), str(entry['options']))
        return rstr

    def match(self, user, action, acls, options={}, skip_user_check=False):
        """
        Check of the requested user, action and the action options match this
        acl-object.
        """
        if user in self.members or skip_user_check:

            if self.uses_role:
                r = ACLResolver.instance
                self.env.log.debug("checking ACL role entries for role: %s" % self.role)
                for acl in r.acl_roles[self.role]:
                    if acl.match(user, action, acls, options, skip_user_check=True):
                        self.env.log.debug("ACL role entry matched for role '%s'" % self.role)
                        return True
            else:
                for act in self.actions:

                    # check for # and * placeholders
                    test_act = re.escape(act['target'])
                    test_act = re.sub(r'(^|\\.)(\\\*)(\\.|$)', '\\1.*\\3', test_act)
                    test_act = re.sub(r'(^|\\.)(\\#)(\\.|$)', '\\1[^\.]*\\3', test_act)

                    # Check if the requested-action matches the acl-action.
                    if not re.match(test_act, action):
                        continue

                    # Check if the required permissions are allowed.
                    if (set(acls) & set(act['acls'])) != set(acls):
                        continue

                    # Check if all required options are given
                    for entry in act['options']:

                        # Check for missing options
                        if entry not in options:
                            self.env.log.debug("ACL option '%s' is missing" % entry)
                            continue

                        # Simply match string options.
                        if type(act['options'][entry]) == str and not re.match(act['options'][entry], options[entry]):
                            self.env.log.debug("ACL option '%s' with value '%s' does not match with '%s'" % (entry,
                                        act['options'][entry], options[entry]))
                            continue

                        # Simply match string options.
                        elif act['options'][entry] != options[entry]:
                            self.env.log.debug("ACL option '%s' with value '%s' does not match with '%s'" % (entry,
                                        act['options'][entry], options[entry]))
                            continue

                    # The acl rule matched!
                    return(True)

        # Nothing matched!
        return False

    def get_type(self):
        """
        Returns the type of an ACL.
        SUB, PSUB, RESET, ...
        """
        return(self.scope)


class ACLRoleEntry(ACL):

    def __init__(self, scope=None, role=None):
        super(ACLRoleEntry, self).__init__(scope=scope, role=role)

    def add_member(self, member):
        """
        Adds a new member to this acl.
        """
        raise Exception("Role ACLs do not support direct members")


class ACLResolver(object):
    implements(IInterfaceHandler)
    instance = None
    acl_sets = None
    acl_roles = None

    _priority_ = 0

    def __init__(self):
        self.env = Environment.getInstance()

        self.acl_sets = []
        self.acl_roles = {}

        # from config later on:
        lh = LDAPHandler.get_instance()
        self.base = lh.get_base()
        self.acl_file = os.path.join(self.env.config.getBaseDir(), "agent.acl")

        self.env.log.debug("initializing ACL resolver")
        self.load_from_file()
        ACLResolver.instance = self

    def add_acl_set(self, acl):
        """
        Adds an ACLSet object to the list of active-acl rules.
        """
        if not self.aclset_exists_by_location(acl.location):
            self.acl_sets.append(acl)
        else:
            raise Exception("An acl definition for location '%s' already exists!", acl.location)

    def add_acl_to_set(self, location, acl):
        """
        Add an acl rule to an existing acl set.
        """
        if not self.aclset_exists_by_location(location):
            raise Exception("No acl definition found for location '%s' cannot add acl!", location)
        else:
            aclset = self.get_aclset_by_location(location)
            aclset.add(acl)

        return(True)

    def add_acl_role(self, acl):
        """
        Adds an ACLRole object to the list of active-acl roles.
        """
        self.acl_roles[acl.name] = acl

    def load_from_file(self):
        """
        Load acl definitions from a file
        """
        self.acl_sets = []

        acl_scope_map = {}
        acl_scope_map['one'] = ACL.ONE
        acl_scope_map['sub'] = ACL.SUB
        acl_scope_map['psub'] = ACL.PSUB
        acl_scope_map['reset'] = ACL.RESET

        try:
            data = json.loads(open(self.acl_file).read())

            # Add ACLRoles
            roles = {}
            unresolved = []
            for name in data['roles']:

                # Create a new role object on demand.
                if name not in roles:
                    roles[name] = ACLRole(name)

                # Check if this role was referenced before but not initialized
                if name in unresolved:
                    unresolved.remove(name)

                # Append the role acls to the ACLRole object
                acls = data['roles'][name]
                for acl_entry in acls:

                    # The acl entry refers to another role ebtry.
                    if 'role' in acl_entry:

                        # If the role was'nt loaded yet, the create and attach requested role
                        #  to the list of roles, but mark it as unresolved
                        rn = str(acl_entry['role'])
                        if rn not in roles:
                            unresolved.append(rn)
                            roles[rn] = ACLRole(rn)
                            self.add_acl_role(roles[rn])

                        # Add the acl entry entry which refers to the role.
                        acl = ACLRoleEntry(role=roles[rn])
                        acl.use_role(roles[rn])
                        acl.set_priority(acl_entry['priority'])
                        roles[name].add(acl)
                        self.add_acl_role(roles[name])
                    else:

                        # Add a normal (non-role) base acl entry
                        acl = ACLRoleEntry(acl_scope_map[acl_entry['scope']])
                        for action in acl_entry['actions']:
                            acl.add_action(action['target'], action['acls'], action['options'])
                        roles[name].add(acl)

            # Check if we've got unresolved roles!
            if len(unresolved):
                raise Exception("Loading ACls failed, we've got unresolved roles references: '%s'!" % (str(unresolved), ))

            # Add the recently created roles.
            for role_name in roles:
                self.add_acl_role(roles[role_name])

            # Add ACLSets
            for location in data['acl']:

                # The ACL defintion is based on an acl role.
                for acls_data in data['acl'][location]:

                    acls = ACLSet(location)
                    for acl_entry in acls_data['acls']:

                        if 'role' in acl_entry:
                            acl_rule_set = self.acl_roles[acl_entry['role']]
                            acl = ACL(role=acl_rule_set)
                            acl.add_members(acl_entry['members'])
                            acl.set_priority(acl_entry['priority'])
                            acls.add(acl)
                        else:
                            acl = ACL(acl_scope_map[acl_entry['scope']])
                            acl.add_members(acl_entry['members'])
                            acl.set_priority(acl_entry['priority'])

                            for action in acl_entry['actions']:
                                acl.add_action(action['target'], action['acls'], action['options'])

                            acls.add(acl)
                    self.add_acl_set(acls)

        except IOError:
            return {}

    def save_to_file(self):
        """
        Save acl definition into a file
        """
        ret = {'acl': {}, 'roles':  {}}

        acl_scope_map = {}
        acl_scope_map[ACL.ONE] = 'one'
        acl_scope_map[ACL.SUB] = 'sub'
        acl_scope_map[ACL.PSUB] = 'psub'
        acl_scope_map[ACL.RESET] = 'reset'

        # Save ACLSets
        for acl_set in self.acl_sets:

            # Prepare lists
            if acl_set.location not in ret['acl']:
                ret['acl'][acl_set.location] = []

            acls = []
            for acl in acl_set:
                if acl.uses_role:
                    entry = {'priority': acl.priority,
                            'role': acl.role,
                            'members': acl.members}
                else:
                    entry = {'actions': acl.actions,
                            'members': acl.members,
                            'priority': acl.priority,
                            'scope': acl_scope_map[acl.scope]}
                acls.append(entry)
            ret['acl'][acl_set.location].append({'acls': acls})

        # Save ACLRoles
        for role_name in self.acl_roles:
            ret['roles'][role_name] = []
            for acl in self.acl_roles[role_name]:
                if acl.uses_role:
                    entry = {'role': acl.role,
                             'priority': acl.priority}
                else:
                    entry = {'actions': acl.actions,
                             'priority': acl.priority,
                             'scope': acl_scope_map[acl.scope]}
                ret['roles'][role_name].append(entry)

        # Store json data into a file
        with open(self.acl_file, 'w') as f:
            import json
            json.dump(ret, f, indent=2)

    def get_permissions(self, user, location, action, acls, options={}):
        """
        Check permissions for a given user and a location.
        """

        # Collect all acls matching the where statement
        allowed = False
        reset = False

        self.env.log.debug("checkint ACL for %s/%s/%s" % (user, location,
            str(action)))

        # Remove the first part of the dn, until we reach the ldap base.
        while self.base in location:

            # Check acls for each acl set.
            for acl_set in self.acl_sets:

                # Skip acls that do not match the current ldap location.
                if location != acl_set.location:
                    continue

                # Check ACls
                for acl in acl_set:
                    if acl.match(user, action, acls, options):
                        self.env.log.debug("found matching ACL in '%s'" % location)
                        if acl.get_type() == ACL.RESET:
                            self.env.log.debug("found ACL reset for action '%s'" % action)
                            reset = True
                        elif acl.get_type() == ACL.PSUB:
                            self.env.log.debug("found permanent ACL for action '%s'" % action)
                            return True
                        elif acl.get_type() in (ACL.SUB, ) and not reset:
                            self.env.log.debug("found ACL for action '%s'" % action)
                            return True

            # Remove the first part of the dn
            location = ','.join(ldap.dn.explode_dn(location)[1::])

        return(allowed)

    def list_acls(self):
        """
        Returns all ACLSets attached to the resolver
        """
        return(self.acl_sets)

    def list_acl_locations(self):
        """
        Returns all locations wie acls attached to
        """
        loc = []
        for entry in self.acl_sets:
            loc.append(entry.location)
        return(loc)

    def list_role_names(self):
        return(self.acl_roles.keys())

    def list_roles(self):
        """
        Returns all ACLRoles attached to the resolver
        """
        return(self.acl_roles)

    def is_role_used(self, role):

        for aclset in self.acl_sets:
            if self.__is_role_used(aclset, role):
                return(True)
        return(False)

    def __is_role_used(self, aclset, role):
        for acl in aclset:
            if acl.uses_role:
                if acl.role == role.name:
                    return(True)
                else:
                    role_acl_sets = self.acl_roles[acl.role]
                    if(self.__is_role_used(role_acl_sets, role)):
                        return(True)

        return(False)

    def get_aclset_by_location(self, location):
        """
        Returns an acl set by location.
        """
        if self.aclset_exists_by_location(location):
            for aclset in self.acl_sets:
                if aclset.location == location:
                    return aclset
        else:
            raise Exception("No acl definition found for location '%s'!" % (location,))

    def aclset_exists_by_location(self, location):
        """
        Checks if a ACLSet for the given location exists or not.
        """
        for aclset in self.acl_sets:
            if aclset.location == location:
                return True
        return False

    def remove_aclset_by_location(self, location):
        """
        Removes a given acl rule.
        """
        if type(location) not in [str, unicode]:
            raise Exception("ACLSets can only be removed by location name, '%s' is an invalid parameter" % location)

        # Remove all aclsets for the given location
        found = 0
        for aclset in self.acl_sets:
            if aclset.location == location:
                self.acl_sets.remove(aclset)
                found += 1

        # Send a message if there were no ACLSets for the given location
        if  not found:
            raise Exception("No acl definitions for location '%s' were found, removal aborted!")

        pass

    def remove_role(self, name):
        """
        Removes an acl role.
        """

        # Allow to remove roles by passing ACLRole-objects.
        if type(name) == ACLRole:
            name = name.name

        # Check if we've got a valid name type.
        if type(name) not in [str, unicode]:
            raise Exception("Roles can only be removed by name, '%s' is an invalid parameter" % name)

        # Check if such a role-name exists and then try to remove it.
        if name in self.acl_roles:
            if self.is_role_used(self.acl_roles[name]):
                raise Exception("The role '%s' cannot be removed, it is still in use!" % name)
            else:
                del(self.acl_roles[name])
                return True
        else:
            raise Exception("No such role '%s', removal aborted!" % name)
        return False