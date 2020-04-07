from collections import defaultdict

from aiohttp import web
from aiohttp_jinja2 import template

from app.service.auth_svc import check_authorization


class AccessApi:

    def __init__(self, services):
        self.data_svc = services.get('data_svc')
        self.rest_svc = services.get('rest_svc')
        self.auth_svc = services.get('auth_svc')

    @check_authorization
    @template('access.html')
    async def landing(self, request):
        exploits = defaultdict(list)
        for i in await self.data_svc.locate('abilities', dict(tactic='initial-access')):
            exploits[i.ability_id] = i.name
        return dict(exploits=dict(exploits), agents=[a.display for a in await self.data_svc.locate('agents')])

    @check_authorization
    async def exploit(self, request):
        data = dict(await request.json())
        await self.rest_svc.task_agent_with_ability(data['paw'], data['ability_id'])
        return web.json_response('complete')
