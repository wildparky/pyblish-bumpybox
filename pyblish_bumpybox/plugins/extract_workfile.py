import os
import shutil

import pyblish.api


@pyblish.api.log
class ExtractWorkfile(pyblish.api.Extractor):
    """"""

    families = ['workFile']
    hosts = ['*']
    version = (0, 1, 0)

    def process_instance(self, instance):

        current_file = instance.data('path')
        current_dir = os.path.dirname(current_file)

        # create publish directory
        publish_dir = os.path.join(current_dir, 'publish')
        if not os.path.exists(publish_dir):
            os.makedirs(publish_dir)

        # copy work file to publish
        publish_file = os.path.join(publish_dir, os.path.basename(current_file))
        shutil.copy(current_file, publish_file)

        # deadline data
        instance.context.set_data('deadlineInput', value=publish_file)

        # ftrack data
        instance.set_data('ftrackComponent', value=current_file)

        if pyblish.api.current_host() == 'nuke':
            instance.set_data('ftrackComponentName', value='nukescript')
        else:
            instance.set_data('ftrackComponentName', value='work_file')