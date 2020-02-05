import subprocess

from app.utility.base_world import BaseWorld


class RedUsb(BaseWorld):

    async def action(self, server, drive, platform):
        location = 'plugins/access/conf/usb'
        command = 'java -jar %s/encoder.jar -i %s/sandcat_%s -o %s/inject.bin' % (location, location, platform, drive)
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output, _ = process.communicate()
        return output.decode('utf-8')
