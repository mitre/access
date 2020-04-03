from collections import defaultdict

from aiohttp_jinja2 import template

from app.service.auth_svc import check_authorization


class AccessApi:

    def __init__(self, services):
        self.data_svc = services.get('data_svc')
        self.auth_svc = services.get('auth_svc')

    @check_authorization
    @template('access.html')
    async def landing(self, request):
        trimmed = defaultdict(list)
        for ex in await self.data_svc.locate('abilities', match=dict(tactic='initial-access', technique_name=('aux', 'exploit'))):
            trimmed[ex.ability_id] = ex.name
        return dict(exploits=dict(trimmed))
