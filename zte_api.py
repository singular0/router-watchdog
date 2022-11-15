#!/usr/bin/env python3

import requests

from copy import deepcopy
from hashlib import md5, sha256
from time import time

class ZTEAPI:

    def __init__(self, host, password):
        self._host = host
        self._password = password.encode()
        self._session = requests.session()
        self._base_url = f"http://{host}/"
        self._base_api_url = f"{self._base_url}goform/"
        self._headers = {
           "Referer": f"http://{host}/"
        }

    def _get(self, params):
        url = f"{self._base_api_url}goform_get_cmd_process"
        _params = deepcopy(params)
        _params["isTest"] = "false"
        _params["_"] = round(time())
        response = self._session.get(url, params=_params, headers=self._headers)
        return response.json()

    def _post(self, payload):
        url = f"{self._base_api_url}goform_set_cmd_process"
        _payload = deepcopy(payload)
        _payload["isTest"] = "false"
        response = self._session.post(url, _payload, headers=self._headers)
        return response.json()

    def _get_cmd(self, cmd):
        params = {}
        if type(cmd) == list:
            params["cmd"] = ",".join(cmd)
            params["multi_data"] = "1"
        else:
            params["cmd"] = cmd
        return self._get(params)

    def login(self):
        salt = self._get_cmd("LD")["LD"].encode()
        password_digest = sha256(self._password).hexdigest().upper().encode()
        salted_digest = sha256(password_digest + salt).hexdigest().upper().encode()
        version_data = self._get_cmd([ "cr_version", "wa_inner_version" ])
        self._cr_version = version_data["cr_version"].encode()
        self._wa_inner_version = version_data["wa_inner_version"].encode()
        self._version_digest = md5(self._wa_inner_version + self._cr_version).hexdigest().encode()
        return self._post({
            "goformId": "LOGIN",
            "password": salted_digest,
        })

    def reboot(self):
        token = self._get_cmd("RD")["RD"].encode()
        token_digest = md5(self._version_digest + token).hexdigest().encode()
        return self._post({
            "goformId": "REBOOT_DEVICE",
            "AD": token_digest
        })
