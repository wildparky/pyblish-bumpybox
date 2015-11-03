import re
import os
import inspect
import subprocess
import traceback
import tempfile

import pyblish.api
import hiero
import ftrack


class ExtractFtrackShots(pyblish.api.Extractor):
    """ Creates ftrack shots by the name of the shot
    """

    families = ['ftrack.trackItem']
    label = 'Ftrack Shots'
    optional = True

    def get_path(self, shot, context):

        ftrack_data = context.data('ftrackData')

        path = [ftrack_data['Project']['root']]
        path.append('renders')
        path.append('audio')
        for p in reversed(shot.getParents()[:-1]):
            path.append(p.getName())

        path.append(shot.getName())

        # get version data
        version = 1
        if context.has_data('version'):
            version = context.data('version')
        version_string = 'v%s' % str(version).zfill(3)

        filename = [shot.getName(), version_string, 'wav']
        path.append('.'.join(filename))

        return os.path.join(*path).replace('\\', '/')

    def frames_to_timecode(self, frames, framerate):

        h = str(int(frames / (3600 * framerate))).zfill(2)
        m = str(int(frames / (60 * framerate) % 60)).zfill(2)
        s = int(float(frames) / framerate % 60)
        f = float('0.' + str((float(frames) / framerate) - s).split('.')[1])
        f = int(f / (1.0 / framerate))

        return '%s:%s:%s' % (h, m, str(s).zfill(2))

    def process(self, instance, context):

        # skipping if not launched from ftrack
        if not context.has_data('ftrackData'):
            return

        ftrack_data = context.data('ftrackData')
        parent = ftrack.Project(ftrack_data['Project']['id'])
        project = parent
        project_name = ftrack_data['Project']['code']
        item = instance[0]

        if 'Episode' in ftrack_data:
            parent = ftrack.Sequence(ftrack_data['Episode']['id'])

        if '--' in item.name():
            name_split = item.name().split('--')
            try:
                if len(name_split) == 2:
                    parent = parent.createSequence(name_split[0])
            except:
                self.log.error(traceback.format_exc())
                if parent == project or 'Sequence' in ftrack_data:
                    parent = ftrack.getSequence([project_name,
                                                name_split[0]])
                else:
                    parent = ftrack.getSequence([project_name,
                                ftrack_data['Episode']['name'], name_split[0]])

            try:
                if len(name_split) == 3:
                    try:
                        parent = project.createEpisode(name_split[0])
                    except:
                        parent = ftrack.getSequence([project_name,
                                                    name_split[0]])
                    parent = parent.createSequence(name_split[1])
            except:
                self.log.error(traceback.format_exc())
                parent = ftrack.getSequence([ftrack_data['Project']['name'],
                                            name_split[0], name_split[1]])

        # creating shot
        shot_name = item.name()
        duration = item.sourceOut() - item.sourceIn() + 1
        if '--' in item.name():
            shot_name = item.name().split('--')[-1]

        tasks = []

        try:
            shot = parent.createShot(shot_name)

            shot.set('fstart', value=1)
            shot.set('fend', value=duration)

            path = self.get_path(shot, context)

            instance.set_data('ftrackId', value=shot.getId())

            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            item.sequence().writeAudioToFile(path, item.timelineIn(),
                                                    item.timelineOut())

            msg = 'Creating new shot with name'
            msg += ' "%s"' % item.name()
            self.log.info(msg)
        except:
            path = []
            try:
                for p in reversed(parent.getParents()):
                    path.append(p.getName())
            except:
                pass
            path.append(parent.getName())
            path.append(shot_name)
            shot = ftrack.getShot(path)

            instance.set_data('ftrackId', value=shot.getId())

            shot.set('fstart', value=1)
            shot.set('fend', value=duration)

            path = self.get_path(shot, context)

            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            item.sequence().writeAudioToFile(path, item.timelineIn(),
                                                    item.timelineOut())

        d = os.path.dirname
        tools_path = d(d(d(d(d(d(inspect.getfile(inspect.currentframe())))))))
        exe = os.path.join(tools_path, 'ffmpeg', 'bin', 'ffmpeg.exe')
        input_path = item.source().mediaSource().fileinfos()[0].filename()
        ext = os.path.splitext(input_path)[1]
        output_path = os.path.splitext(input_path)[0]
        output_path += '_thumbnail.png'
        output_path = os.path.join(tempfile.gettempdir(),
                                    os.path.basename(output_path))
        input_cmd = ''
        fps = item.sequence().framerate().toFloat()

        if ext == '.mov':
            arg = ' scale=-1:108'
            input_cmd = ' -vf' + arg + ' -vframes' + ' 1'
        else:
            arg = ' scale=-1:108'
            if os.path.splitext(input_path)[1] == '.exr':
                arg += ',lutrgb=r=gammaval(0.45454545):'
                arg += 'g=gammaval(0.45454545):'
                arg += 'b=gammaval(0.45454545)'
            input_cmd = ' -vf' + arg

        tc = self.frames_to_timecode(item.sourceIn(), fps)
        cmd = exe + ' -ss '+ tc +' -i "' + input_path + '" ' + input_cmd
        cmd += ' -y "' + output_path + '"'
        subprocess.call(cmd)

        # creating thumbnails
        thumb = shot.createThumbnail(output_path)
        for t in shot.getTasks():
            t.set('thumbid', value=thumb.get('entityId'))

        if os.path.exists(output_path):
            os.remove(output_path)
