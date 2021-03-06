import os
import shutil

import pyblish.api


class ExtractScene(pyblish.api.InstancePlugin):
    """ Extract work file to 'publish' directory next to work file
    """

    order = pyblish.api.ExtractorOrder
    families = ['scene']
    label = 'Scene'

    def process(self, instance):

        current_file = instance.data('workPath')
        publish_file = instance.data('publishPath')
        publish_dir = os.path.dirname(instance.data('publishPath'))

        # create publish directory
        if not os.path.exists(publish_dir):
            os.makedirs(publish_dir)

        # copy work file to publish
        shutil.copy(current_file, publish_file)
