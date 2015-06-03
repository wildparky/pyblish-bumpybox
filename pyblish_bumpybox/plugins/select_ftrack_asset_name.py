import os

import pyblish.api
import ftrack


@pyblish.api.log
class SelectFtrackAssetName(pyblish.api.Selector):
    """ """

    hosts = ['*']
    version = (0, 1, 0)

    def process_context(self, context):

        task = ftrack.Task(id=os.environ['FTRACK_TASKID'])

        # skipping the call up project
        project = task.getParents()[-1]
        if not project.getName() == 'the_call_up':
            self.log.info('setting ftrackAssetName')
            context.set_data('ftrackAssetName', value=task.getName())