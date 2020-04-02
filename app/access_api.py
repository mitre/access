from aiohttp_jinja2 import template

from app.service.auth_svc import check_authorization


class AccessApi:

    def __init__(self, services):
        self.data_svc = services.get('data_svc')
        self.auth_svc = services.get('auth_svc')

    @check_authorization
    @template('access.html')
    async def landing(self, request):
        return dict(exploits=[ex.display for ex in await self.data_svc.locate('exploits')])
