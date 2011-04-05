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
from SpiffWorkflow.Operators import valueof
from TaskSpec                import TaskSpec

class MultiInstance(TaskSpec):
    """
    When executed, this task performs a split on the current task.
    The number of outgoing tasks depends on the runtime value of a
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
                    times -- the number of tasks to create.
        """
        assert kwargs.has_key('times')
        TaskSpec.__init__(self, parent, name, **kwargs)
        self.times = kwargs.get('times', None)


    def _find_my_task(self, task):
        for node in task.job.task_tree:
            if node.thread_id != task.thread_id:
                continue
            if node.spec == self:
                return node
        return None


    def _on_trigger(self, taskspec):
        """
        May be called after execute() was already completed to create an
        additional outbound task.
        """
        # Find a Task for this TaskSpec.
        my_task = self._find_my_task(taskspec)
        for output in self.outputs:
            if my_task._has_state(Task.COMPLETED):
                state = Task.READY | Task.TRIGGERED
            else:
                state = Task.FUTURE | Task.TRIGGERED
            node = my_task._add_child(output, state)
            output._predict(node)


    def _get_predicted_outputs(self, my_task):
        split_n = my_task._get_internal_attribute('splits', 1)

        # Predict the outputs.
        outputs = []
        for i in range(split_n):
            outputs += self.outputs
        return outputs


    def _predict_hook(self, my_task):
        split_n = valueof(my_task, self.times)
        if split_n is None:
            return
        my_task._set_internal_attribute(splits = split_n)

        # Create the outgoing nodes.
        outputs = []
        for i in range(split_n):
            outputs += self.outputs

        if my_task._has_state(Task.LIKELY):
            child_state = Task.LIKELY
        else:
            child_state = Task.FUTURE
        my_task._update_children(outputs, child_state)


    def _on_complete_hook(self, my_task):
        """
        Runs the task. Should not be called directly.
        Returns True if completed, False otherwise.
        """
        outputs = self._get_predicted_outputs(my_task)
        my_task._update_children(outputs)
        return True
