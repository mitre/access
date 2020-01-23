from plugins.access.app.access_svc import AccessService

name = 'Access'
description = 'A toolkit containing a set of functional red-team tools'
address = '/plugin/access/gui'


async def enable(services):
    props = services.get('app_svc').strip_yml('plugins/access/conf/default.yml')[0]
    access_svc = AccessService(services=services, props=props)
    app = services.get('app_svc').application
    app.router.add_static('/access', 'plugins/access/static', append_version=True)
    app.router.add_route('GET', '/plugin/access/gui', access_svc.landing)
    app.router.add_route('GET', props.get('clone_url'), access_svc.malicious)
    app.router.add_route('POST', '/plugin/access/props', access_svc.update_props)
    app.router.add_route('POST', '/plugin/access/log', access_svc.key_log)
    await access_svc.clone_new_site(url=props.get('clone_site'))
