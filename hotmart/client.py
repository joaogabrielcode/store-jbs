import logging
from urllib.parse import quote

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class HotmartError(Exception):
    pass


class HotmartClient:
    API_URL = "https://developers.hotmart.com/products/api/v1"
    AUTH_URL = "https://api-sec-vlc.hotmart.com/security/oauth/token"

    def __init__(self):
        self.access_token = None

    def _request(self, method, url, **kwargs):
        try:
            return requests.request(
                method, url, timeout=(5, 20), allow_redirects=False, **kwargs
            )
        except requests.RequestException:
            logger.warning("Hotmart: falha de conexão ou timeout")
            raise HotmartError("Não foi possível conectar à Hotmart.") from None

    def authenticate(self):
        if not all((
            settings.HOTMART_CLIENT_ID,
            settings.HOTMART_CLIENT_SECRET,
            settings.HOTMART_BASIC_AUTH,
        )):
            raise HotmartError(
                "Configure HOTMART_CLIENT_ID, HOTMART_CLIENT_SECRET e HOTMART_BASIC_AUTH."
            )
        basic = settings.HOTMART_BASIC_AUTH.removeprefix("Basic ").strip()
        response = self._request(
            "POST", self.AUTH_URL,
            params={
                "grant_type": "client_credentials",
                "client_id": settings.HOTMART_CLIENT_ID,
                "client_secret": settings.HOTMART_CLIENT_SECRET,
            },
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/json",
            },
        )
        data = self._json(response)
        token = data.get("access_token")
        if not isinstance(token, str) or not token:
            raise HotmartError("Hotmart retornou autenticação incompleta.")
        self.access_token = token

    @staticmethod
    def _json(response):
        if not 200 <= response.status_code < 300:
            logger.warning("Hotmart: resposta HTTP %s", response.status_code)
            raise HotmartError(f"Hotmart retornou HTTP {response.status_code}.")
        try:
            data = response.json()
        except ValueError:
            raise HotmartError("Hotmart retornou JSON inválido.") from None
        if not isinstance(data, dict):
            raise HotmartError("Hotmart retornou uma resposta inválida.")
        return data

    def paginate(self, path, **filters):
        if not self.access_token:
            self.authenticate()
        params = {"max_results": 50, **filters}
        seen_tokens = set()
        while True:
            response = self._request(
                "GET", f"{self.API_URL}/{path}", params=params.copy(),
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            if response.status_code == 401:
                self.authenticate()
                response = self._request(
                    "GET", f"{self.API_URL}/{path}", params=params.copy(),
                    headers={"Authorization": f"Bearer {self.access_token}"},
                )
            data = self._json(response)
            items, page_info = data.get("items"), data.get("page_info")
            if (
                not isinstance(items, list)
                or not all(isinstance(item, dict) for item in items)
                or not isinstance(page_info, dict)
            ):
                raise HotmartError("Hotmart retornou paginação inválida.")
            yield from items
            token = page_info.get("next_page_token")
            if not token:
                break
            if not isinstance(token, str) or token in seen_tokens:
                raise HotmartError("Hotmart repetiu um cursor de paginação.")
            seen_tokens.add(token)
            params["page_token"] = token

    def products(self):
        return self.paginate("products", format="ONLINE_COURSE")

    def offers(self, ucode):
        return self.paginate(f"products/{quote(str(ucode), safe='')}/offers")
