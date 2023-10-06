import json
import requests
from tempus_security_utils.okta_token_manager import OktaTokenManager


class HttpClient:
    def __init__(self, ssm_vars, *args, **kwargs):

        self.base_url = ssm_vars["OKTA_BASE_URL"]
        self.email = ssm_vars["OKTA_USERNAME"]
        self.password = ssm_vars["OKTA_PASSWORD"]
        self.client_id = ssm_vars["OKTA_CLIENT_ID"]
        self.client_secret = ssm_vars["OKTA_CLIENT_SECRET"]

        self.requests = requests
        self.token_manager = OktaTokenManager(
            base_url=self.base_url,
            email=self.email,
            password=self.password,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        self.token = None

    def request(self, *args, **kwargs):
        kwargs["headers"] = self.add_auth_header(kwargs.get("headers", {}))
        response = self.requests.request(*args, **kwargs)
        if response.status_code == 401:
            # Try the request again with a fresh auth token
            kwargs["headers"] = self.add_auth_header(
                kwargs.get("headers", {}), refresh=True
            )
            response = self.requests.request(*args, **kwargs)

        # if still 4xx or 5xx, raise an error
        response.raise_for_status()
        return response

    def add_auth_header(self, headers, refresh=False):
        # shallow copy
        new_headers = headers.copy()
        if refresh or not self.token:
            self.token = self.token_manager.get_access_token(refresh=refresh)
        new_headers.update({"Authorization": "Bearer {}".format(self.token)})
        return new_headers
