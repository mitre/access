import glob

from app.utility.base_world import BaseWorld
from plugins.access.app.access_api import AccessApi
from plugins.access.app.exploit import Exploit

name = 'Access'
description = 'A toolkit containing initial access throwing modules'
address = '/plugin/access/gui'
access = BaseWorld.Access.RED


async def enable(services):
    data_svc = services.get('data_svc')
    await data_svc.apply('exploits')
    await _load_exploits(data_svc)

    access_api = AccessApi(services=services)
    app = services.get('app_svc').application
    app.router.add_static('/access', 'plugins/access/static', append_version=True)
    app.router.add_route('GET', '/plugin/access/gui', access_api.landing)


async def _load_exploits(data_svc):
    for filename in glob.iglob('plugins/access/data/exploits/**/*.yml', recursive=True):
        for ex in BaseWorld.strip_yml(filename):
            exploit = Exploit(identifier=ex['id'], name=ex['name'], category=ex['category'], payload=ex['payload'],
                              description=ex['description'], properties=ex['properties'], access=BaseWorld.Access.RED)
            await data_svc.store(exploit)
