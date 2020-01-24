from plugins.access.app.access_api import AccessApi
from plugins.access.app.red.red_clone import RedClone

name = 'Access'
description = 'A toolkit containing a set of functional red-team tools'
address = '/plugin/access/gui'


async def enable(services):
    props = services.get('app_svc').strip_yml('plugins/access/conf/default.yml')[0]
    access_api = AccessApi(services=services, props=props)
    app = services.get('app_svc').application
    app.router.add_static('/access', 'plugins/access/static', append_version=True)
    app.router.add_route('GET', '/plugin/access/gui', access_api.landing)
    app.router.add_route('GET', props.get('clone_url'), access_api.malicious)
    app.router.add_route('POST', '/plugin/access/clone', access_api.clone)
    app.router.add_route('POST', '/plugin/access/usb', access_api.usb)

    app.router.add_route('POST', '/plugin/access/log', access_api.key_log)
    await RedClone().action(url=props.get('clone_site'), props=props)
