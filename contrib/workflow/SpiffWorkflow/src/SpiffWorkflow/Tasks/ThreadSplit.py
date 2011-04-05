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
from SpiffWorkflow.Task      import Task
from SpiffWorkflow.Exception import WorkflowException
from TaskSpec                import TaskSpec
from ThreadStart             import ThreadStart

class ThreadSplit(TaskSpec):
    """
    When executed, this task performs a split on the current my_task.
    The number of outgoing my_tasks depends on the runtime value of a
    specified attribute.
    If more than one input is connected, the task performs an implicit
    multi merge.

    This task has one or more inputs and may have any number of outputs.
    """

    def __init__(self, parent, name, **kwargs):
        """
        Constructor.
        
        parent -- a reference to the parent (TaskSpec)
        name -- a name for the pattern (string)
        kwargs -- must contain one of the following:
                    times -- the number of my_tasks to create.
                    times-attribute -- the name of the attribute that
                                       specifies the number of outgoing
                                       my_tasks.
        """
        assert kwargs.has_key('times_attribute') or kwargs.has_key('times')
        TaskSpec.__init__(self, parent, name, **kwargs)
        self.times_attribute = kwargs.get('times_attribute', None)
        self.times           = kwargs.get('times',           None)
        self.thread_starter  = ThreadStart(parent, **kwargs)
        self.outputs.append(self.thread_starter)
        self.thread_starter._connect_notify(self)


    def connect(self, taskspec):
        """
        Connect the *following* task to this one. In other words, the
        given task is added as an output task.

        task -- the task to connect to.
        """
        self.thread_starter.outputs.append(taskspec)
        taskspec._connect_notify(self.thread_starter)


    def _find_my_task(self, job):
        for task in job.branch_tree:
            if task.thread_id != my_task.thread_id:
                continue
            if task.task == self:
                return task
        return None


    def _get_activated_tasks(self, my_task, destination):
        """
        Returns the list of tasks that were activated in the previous 
        call of execute(). Only returns tasks that point towards the
        destination task, i.e. those which have destination as a 
        descendant.

        my_task -- the task of this TaskSpec
        destination -- the child task
        """
        task = destination._find_ancestor(self.thread_starter)
        return self.thread_starter._get_activated_tasks(task, destination)


    def _get_activated_threads(self, my_task):
        """
        Returns the list of threads that were activated in the previous 
        call of execute().

        my_task -- the task of this TaskSpec
        """
        return my_task.children


    def _on_trigger(self, my_task):
        """
        May be called after execute() was already completed to create an
        additional outbound task.
        """
        # Find a Task for this task.
        my_task = self._find_my_task(my_task.job)
        for output in self.outputs:
            state    = Task.READY | Task.TRIGGERED
            new_task = my_task.add_child(output, state)


    def _predict_hook(self, my_task):
        split_n = my_task.get_attribute('split_n', self.times)
        if split_n is None:
            split_n = my_task.get_attribute(self.times_attribute, 1)

        # Predict the outputs.
        outputs = []
        for i in range(split_n):
            outputs.append(self.thread_starter)
        if my_task._is_definite():
            child_state = Task.FUTURE
        else:
            child_state = Task.LIKELY
        my_task._update_children(outputs, child_state)


    def _on_complete_hook(self, my_task):
        """
        Runs the task. Should not be called directly.
        Returns True if completed, False otherwise.
        """
        # Split, and remember the number of splits in the context data.
        split_n = self.times
        if split_n is None:
            split_n = my_task.get_attribute(self.times_attribute)

        # Create the outgoing tasks.
        outputs = []
        for i in range(split_n):
            outputs.append(self.thread_starter)
        my_task._update_children(outputs)
        return True
