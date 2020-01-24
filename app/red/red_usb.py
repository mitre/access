import subprocess

from app.utility.base_world import BaseWorld


class RedUsb(BaseWorld):

    async def action(self, server, drive, platform):
        location = 'plugins/access/conf/usb'
        await self._replace_server(f='%s/sandcat_%s' % (location, platform), platform=platform, server=server)
        command = 'java -jar %s/encoder.jar -i %s/sandcat_%s -o %s/inject.bin' % (location, location, platform, drive)
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output, _ = process.communicate()
        return output.decode('utf-8')

    """ PRIVATE """

    async def _replace_server(self, f, platform, server):
        with open(f, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(f, 'w') as fout:
            fout.writelines(data[1:])
        if platform == 'windows':
            self.prepend_to_file(f, 'STRING $server="%s"' % server)
        else:
            self.prepend_to_file(f, 'STRING server="%s"' % server)
