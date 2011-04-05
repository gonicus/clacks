# Copyright (C) 2007 Samuel Abels
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
import time
from Exception import WorkflowException

class Task(object):
    """
    A node used internally for composing a tree that represents the path that
    is taken (or predicted) within the workflow.
    """
    FUTURE    =   1
    LIKELY    =   2
    MAYBE     =   4
    WAITING   =   8
    READY     =  16
    CANCELLED =  32
    COMPLETED =  64
    TRIGGERED = 128

    FINISHED_MASK      = CANCELLED | COMPLETED
    DEFINITE_MASK      = FUTURE | WAITING | READY | FINISHED_MASK
    PREDICTED_MASK     = FUTURE | LIKELY | MAYBE
    NOT_FINISHED_MASK  = PREDICTED_MASK | WAITING | READY
    ANY_MASK           = FINISHED_MASK | NOT_FINISHED_MASK

    state_names = {FUTURE:    'FUTURE',
                   WAITING:   'WAITING',
                   READY:     'READY',
                   CANCELLED: 'CANCELLED',
                   COMPLETED: 'COMPLETED',
                   LIKELY:    'LIKELY',
                   MAYBE:     'MAYBE',
                   TRIGGERED: 'TRIGGERED'}

    class Iterator(object):
        """
        This is a tree iterator that supports filtering such that a client
        may walk through all tasks that have a specific state.
        """
        def __init__(self, current, filter = None):
            """
            Constructor.
            """
            self.filter = filter
            self.path   = [current]


        def __iter__(self):
            return self


        def _next(self):
            # Make sure that the end is not yet reached.
            if len(self.path) == 0:
                raise StopIteration()

            # If the current task has children, the first child is the next item.
            # If the current task is LIKELY, and predicted tasks are not
            # specificly searched, we can ignore the children, because predicted
            # tasks should only have predicted children.
            current     = self.path[-1]
            ignore_task = False
            if self.filter is not None:
                search_predicted = self.filter   & Task.LIKELY != 0
                is_predicted     = current.state & Task.LIKELY != 0
                ignore_task      = is_predicted and not search_predicted
            if len(current.children) > 0 and not ignore_task:
                self.path.append(current.children[0])
                if self.filter is not None and current.state & self.filter == 0:
                    return None
                return current

            # Ending up here, this task has no children. Crop the path until we
            # reach a task that has unvisited children, or until we hit the end.
            while True:
                old_child = self.path.pop(-1)
                if len(self.path) == 0:
                    break

                # If this task has a sibling, choose it.
                parent = self.path[-1]
                pos    = parent.children.index(old_child)
                if len(parent.children) > pos + 1:
                    self.path.append(parent.children[pos + 1])
                    break
            if self.filter is not None and current.state & self.filter == 0:
                return None
            return current


        def next(self):
            # By using this loop we avoid an (expensive) recursive call.
            while True:
                next = self._next()
                if next is not None:
                    return next


    # Pool for assigning a unique id to every new Task.
    id_pool        = 0
    thread_id_pool = 0

    def __init__(self, job, spec, parent = None):
        """
        Constructor.
        """
        assert job      is not None
        assert spec is not None
        self.__class__.id_pool  += 1
        self.job                 = job
        self.parent              = parent
        self.children            = []
        self.state               = Task.FUTURE
        self.spec            = spec
        self.id                  = self.__class__.id_pool
        self.thread_id           = self.__class__.thread_id_pool
        self.last_state_change   = time.time()
        self.attributes          = {}
        self.internal_attributes = {}
        if parent is not None:
            self.parent._child_added_notify(self)


    def __iter__(self):
        return Task.Iterator(self)


    def __setstate__(self, dict):
        self.__dict__.update(dict)
        # If unpickled in the same Python process in which a workflow
        # (Task) is built through the API, we need to make sure
        # that there will not be any ID collisions.
        if dict['id'] >= self.__class__.id_pool:
            self.__class__.id_pool = dict['id']
        if dict['thread_id'] >= self.__class__.thread_id_pool:
            self.__class__.thread_id_pool = dict['thread_id']


    def _get_root(self):
        """
        Returns the top level parent.
        """
        if self.parent is None:
            return self
        return self.parent._get_root()


    def _get_depth(self):
        depth = 0
        task  = self.parent
        while task is not None:
            depth += 1
            task = task.parent
        return depth


    def _child_added_notify(self, child):
        """
        Called by another Task to let us know that a child was added.
        """
        assert child is not None
        self.children.append(child)


    def _drop_children(self):
        drop = []
        for child in self.children:
            if not child._is_finished():
                drop.append(child)
            else:
                child._drop_children()
        for task in drop:
            self.children.remove(task)


    def _set_state(self, state):
        self.state             = state
        self.last_state_change = time.time()


    def _has_state(self, state):
        """
        Returns True if the Task has the given state flag set.
        """
        return (self.state & state) != 0


    def _is_finished(self):
        return self.state & self.FINISHED_MASK != 0


    def _is_predicted(self):
        return self.state & self.PREDICTED_MASK != 0


    def _is_definite(self):
        return self.state & self.DEFINITE_MASK != 0


    def _add_child(self, spec, state = FUTURE):
        """
        Adds a new child and assigns the given TaskSpec to it.

        @type  spec: TaskSpec
        @param spec: The TaskSpec that is assigned to the new child.
        @type  state: integer
        @param state: The bitmask of states for the new child.
        @rtype:  Task
        @return: The new child task.
        """
        if spec is None:
            raise WorkflowException(self, '_add_child() requires a TaskSpec')
        if self._is_predicted() and state & self.PREDICTED_MASK == 0:
            msg = 'Attempt to add non-predicted child to predicted task'
            raise WorkflowException(self, msg)
        task           = Task(self.job, spec, self)
        task.thread_id = self.thread_id
        if state == self.READY:
            task._ready()
        else:
            task.state = state
        return task


    def _assign_new_thread_id(self, recursive = True):
        """
        Assigns a new thread id to the task.

        @type  recursive: boolean
        @param recursive: Whether to assign the id to children recursively.
        @rtype:  boolean
        @return: The new thread id.
        """
        self.__class__.thread_id_pool += 1
        self.thread_id = self.__class__.thread_id_pool
        if not recursive:
            return self.thread_id
        for child in self:
            child.thread_id = self.thread_id
        return self.thread_id


    def _update_children(self, taskspecs, state = None):
        """
        This method adds one child for each given TaskSpec, unless that
        child already exists.
        The state of COMPLETED tasks is never changed.

        If this method is passed a state:
          - The state of TRIGGERED tasks is not changed.
          - The state for all children is set to the given value.

        If this method is not passed a state:
          - The state for all children is updated by calling the child's
          _update_state() method.
          
        If the task currently has a child that is not given in the TaskSpecs, 
        the child is removed.
        It is an error if the task has a non-LIKELY child that is 
        not given in the TaskSpecs.

        @type  taskspecs: list[TaskSpec]
        @param taskspecs: The list of TaskSpecs that may become children.
        @type  state: integer
        @param state: The bitmask of states for newly added children.
        """
        if taskspecs is None:
            raise WorkflowException(self, '"taskspecs" argument is None')
        if type(taskspecs) != type([]):
            taskspecs = [taskspecs]

        # Create a list of all children that are no longer needed, and
        # set the state of all others.
        add    = taskspecs[:]
        remove = []
        for child in self.children:
            # Must not be TRIGGERED or COMPLETED.
            if child._has_state(Task.TRIGGERED):
                if state is None:
                    child.spec._update_state(child)
                continue
            if child._is_finished():
                add.remove(child.spec)
                continue

            # Check whether the item needs to be added or removed.
            if child.spec not in add:
                if not self._is_definite():
                    msg = 'Attempt to remove non-predicted %s' % child.get_name()
                    raise WorkflowException(self, msg)
                remove.append(child)
                continue
            add.remove(child.spec)

            # Update the state.
            if state is not None:
                child.state = state
            else:
                child.spec._update_state(child)

        # Remove all children that are no longer specified.
        for child in remove:
            self.children.remove(child)

        # Add a new child for each of the remaining tasks.
        for spec in add:
            if spec.cancelled:
                continue
            if state is not None:
                self._add_child(spec, state)
            else:
                child = self._add_child(spec, self.LIKELY)
                spec._update_state(child)


    def _set_likely_task(self, taskspecs):
        if type(taskspecs) != type([]):
            taskspecs = [taskspecs]
        for spec in taskspecs:
            for child in self.children:
                if child.spec != spec:
                    continue
                if child._is_definite():
                    continue
                child._set_state(self.LIKELY)
                return


    def _is_descendant_of(self, parent):
        """
        Returns True if parent is in the list of ancestors, returns False
        otherwise.

        @type  parent: Task
        @param parent: The parent that is searched in the ancestors.
        @rtype:  boolean
        @return: Whether the parent was found.
        """
        if self.parent is None:
            return False
        if self.parent == parent:
            return True
        return self.parent._is_descendant_of(parent)


    def _find_child_of(self, parent_taskspec):
        """
        Returns the ancestor that has a task with the given TaskSpec
        as a parent.
        If no such ancestor was found, the root node is returned.

        @type  parent_taskspec: TaskSpec
        @param parent_taskspec: The wanted ancestor.
        @rtype:  Task
        @return: The child of the given ancestor.
        """
        if self.parent is None:
            return self
        if self.parent.spec == parent_taskspec:
            return self
        return self.parent._find_child_of(parent_taskspec)


    def _find_any(self, taskspec):
        """
        Returns any descendants that have the given TaskSpec assigned.

        @type  taskspec: TaskSpec
        @param taskspec: The wanted task.
        @rtype:  list[Task]
        @return: The Task objects that are attached to the given TaskSpec.
        """
        tasks = []
        if self.spec == taskspec:
            tasks.append(self)
        for child in self:
            if child.spec != taskspec:
                continue
            tasks.append(child)
        return tasks


    def _find_ancestor(self, taskspec):
        """
        Returns the ancestor that has the given TaskSpec assigned.
        If no such ancestor was found, the root node is returned.

        @type  taskspec: TaskSpec
        @param taskspec: The wanted task.
        @rtype:  Task
        @return: The ancestor.
        """
        if self.parent is None:
            return self
        if self.parent.spec == taskspec:
            return self.parent
        return self.parent._find_ancestor(taskspec)


    def _find_ancestor_from_name(self, name):
        """
        Returns the ancestor that has a task with the given name assigned.
        Returns None if no such ancestor was found.

        @type  name: string
        @param name: The name of the wanted task.
        @rtype:  Task
        @return: The ancestor.
        """
        if self.parent is None:
            return None
        if self.parent.get_name() == name:
            return self.parent
        return self.parent._find_ancestor_from_name(name)


    def _ready(self):
        """
        Marks the task as ready for execution.
        """
        if self.state & self.COMPLETED != 0:
            return
        if self.state & self.CANCELLED != 0:
            return
        self._set_state(self.READY | (self.state & self.TRIGGERED))
        return self.spec._on_ready(self)


    def get_name(self):
        return str(self.spec.name)


    def get_description(self):
        return str(self.spec.description)


    def get_state(self):
        """
        Returns this Task's state.
        """
        return self.state


    def get_state_name(self):
        """
        Returns a textual representation of this Task's state.
        """
        state_name = []
        for key, name in self.state_names.iteritems():
            if self.state & key != 0:
                state_name.append(name)
        return '|'.join(state_name)


    def get_property(self, name, default = None):
        """
        Returns the value of the property with the given name, or the given
        default value if the property does not exist.

        @type  name: string
        @param name: A property name.
        @type  default: obj
        @param default: Return this value if the property does not exist.
        @rtype:  obj
        @return: The value of the property.
        """
        return self.spec.get_property(name, default)


    def get_properties(self):
        """
        Returns a dictionary containing all properties.

        @rtype:  dict
        @return: Maps property names to values.
        """
        return self.spec.properties


    def _set_internal_attribute(self, **kwargs):
        """
        Defines the given attribute/value pairs.
        """
        self.internal_attributes.update(kwargs)


    def _get_internal_attribute(self, name, default = None):
        return self.internal_attributes.get(name, default)


    def set_attribute(self, **kwargs):
        """
        Defines the given attribute/value pairs.
        """
        self.attributes.update(kwargs)


    def _inherit_attributes(self):
        """
        Inherits the attributes from the parent.
        """
        self.set_attribute(**self.parent.attributes)


    def get_attribute(self, name, default = None):
        """
        Returns the value of the attribute with the given name, or the given
        default value if the attribute does not exist.

        @type  name: string
        @param name: An attribute name.
        @type  default: obj
        @param default: Return this value if the attribute does not exist.
        @rtype:  obj
        @return: The value of the attribute.
        """
        return self.attributes.get(name, default)


    def get_attributes(self):
        return self.attributes


    def cancel(self):
        """
        Cancels the item if it was not yet completed, and removes
        any children that are LIKELY.
        """
        if self._is_finished():
            for child in self.children:
                child.cancel()
            return
        self._set_state(self.CANCELLED | (self.state & self.TRIGGERED))
        self._drop_children()
        return self.spec._on_cancel(self)


    def complete(self):
        """
        Called by the associated task to let us know that its state
        has changed (e.g. from FUTURE to COMPLETED.)
        """
        self._set_state(self.COMPLETED | (self.state & self.TRIGGERED))
        return self.spec._on_complete(self)


    def trigger(self, *args):
        """
        If recursive is True, the state is applied to the tree recursively.
        """
        self.spec._on_trigger(self, *args)


    def get_dump(self, indent = 0, recursive = True):
        """
        Returns the subtree as a string for debugging.

        @rtype:  string
        @return: The debug information.
        """
        dbg  = (' ' * indent * 2)
        dbg += '%s/'           % self.id
        dbg += '%s:'           % self.thread_id
        dbg += ' Task of %s'   % self.get_name()
        dbg += ' State: %s'    % self.get_state_name()
        dbg += ' Children: %s' % len(self.children)
        if recursive:
            for child in self.children:
                dbg += '\n' + child.get_dump(indent + 1)
        return dbg


    def dump(self, indent = 0):
        """
        Prints the subtree as a string for debugging.
        """
        print self.get_dump()
