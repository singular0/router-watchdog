#!/usr/bin/env python3

"""ZTE router API."""

from copy import deepcopy
from hashlib import md5, sha256
from time import time

import requests


class ZTEAPI:
    """ZTE router API class."""

    def __init__(self, host: str, *, user: str = None, password: str, model: str = "MC888"):
        """
        ZTE API constructor.

        Parameters:
            host (str): router hostname
            user (str): router user
            password (str): router password
            model (str): router model ("MC801" or "MC888")
        """
        self._host = host
        self._user = user
        self._password = password.encode()
        self._model = model
        self._session = requests.session()
        self._base_url = f"http://{host}/"
        self._base_api_url = f"{self._base_url}goform/"
        self._headers = {
           "Referer": f"http://{host}/"
        }
        self._cr_version = None
        self._wa_inner_version = None
        self._version_digest = None

    def _get(self, params: dict[str]):
        url = f"{self._base_api_url}goform_get_cmd_process"
        _params = deepcopy(params)
        _params["isTest"] = "false"
        _params["_"] = round(time())
        response = self._session.get(url, params=_params, headers=self._headers)
        return response.json()

    def _post(self, payload: dict[str]):
        url = f"{self._base_api_url}goform_set_cmd_process"
        _payload = deepcopy(payload)
        _payload["isTest"] = "false"
        response = self._session.post(url, _payload, headers=self._headers)
        return response.json()

    def _get_cmd(self, cmd: str):
        params = {}
        if isinstance(cmd, list):
            params["cmd"] = ",".join(cmd)
            params["multi_data"] = "1"
        else:
            params["cmd"] = cmd
        return self._get(params)

    def login(self):
        """
        Authenticate to the router.

        Returns:
            router response payload
        """
        salt = self._get_cmd("LD")["LD"].encode()
        password_digest = sha256(self._password).hexdigest().upper().encode()
        salted_digest = sha256(password_digest + salt).hexdigest().upper().encode()
        version_data = self._get_cmd(["cr_version", "wa_inner_version"])
        self._cr_version = version_data["cr_version"].encode()
        self._wa_inner_version = version_data["wa_inner_version"].encode()
        version = self._wa_inner_version + self._cr_version
        if self._model == "MC888":
            self._version_digest = sha256(version).hexdigest().upper().encode()
        else:
            self._version_digest = md5(version).hexdigest().encode()
        request = {
            "goformId": "LOGIN",
            "password": salted_digest,
        }
        if self._user:
            request["user"] = self._user
        return self._post(request)

    def reboot(self):
        """
        Reboot the router.

        Returns:
            router response payload
        """
        token = self._get_cmd("RD")["RD"].encode()
        salted_token = self._version_digest + token
        if self._model == "MC888":
            token_digest = sha256(salted_token).hexdigest().upper().encode()
        else:
            token_digest = md5(salted_token).hexdigest().encode()
        return self._post({
            "goformId": "REBOOT_DEVICE",
            "AD": token_digest
        })
