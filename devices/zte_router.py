"""ZTE router API."""

import logging
import os
from copy import deepcopy
from enum import Enum
from hashlib import md5, sha256
from time import time

import requests

from .base_device import DeviceConfigError, RebootableDevice


class ZTERouterModel(Enum):
    """ZTE router model."""

    MC801 = 'MC801'
    MC888 = 'MC888'

    def __str__(self) -> str:
        """
        Return string representation of enum value.

        Returns:
            (str): string representation of enum value
        """
        return self.value


DEFAULT_MODEL = ZTERouterModel.MC888.value
DEFAULT_USER = 'user'


class ZTERouter(RebootableDevice):
    """ZTE router device class."""

    def __init__(self):
        """
        ZTE router class constructor.

        Raises:
            DeviceConfigError: in case of configuration error
        """
        self._model = ZTERouterModel[os.getenv('ROUTER_MODEL', DEFAULT_MODEL)]

        self._host = os.getenv('ZTE_ROUTER_HOST')
        if not self._host:
            raise DeviceConfigError('ZTE_ROUTER_HOST env variable must be set')

        self._user = os.getenv('ZTE_ROUTER_USER')
        if self._model == ZTERouterModel.MC888 and not self._user:
            self._user = DEFAULT_USER

        self._password = os.getenv('ZTE_ROUTER_PASSWORD')
        if not self._password:
            raise DeviceConfigError('ZTE_ROUTER_PASSWORD env variable must be set')

        self._session = requests.session()
        self._base_url = f'http://{self._host}'
        self._base_api_url = f'{self._base_url}/goform'
        self._headers = {
           'Referer': self._base_url
        }

        logging.debug(f'ZTE router: model [{self._model}], host [{self._host}], '
                      f'user [{self._user}], password [{self._password}]')

        self._cr_version = None
        self._wa_inner_version = None
        self._version_digest = None

    def _get(self, params: dict[str]) -> dict[str]:
        url = f'{self._base_api_url}/goform_get_cmd_process'
        _params = deepcopy(params)
        _params['isTest'] = 'false'
        _params['_'] = round(time())
        response = self._session.get(url, params=_params, headers=self._headers)
        return response.json()

    def _post(self, payload: dict[str]) -> dict[str]:
        url = f'{self._base_api_url}/goform_set_cmd_process'
        _payload = deepcopy(payload)
        _payload['isTest'] = 'false'
        response = self._session.post(url, _payload, headers=self._headers)
        return response.json()

    def _get_cmd(self, cmd: str) -> dict[str]:
        params = {}
        if isinstance(cmd, list):
            params['cmd'] = ','.join(cmd)
            params['multi_data'] = '1'
        else:
            params["cmd"] = cmd
        return self._get(params)

    def _login(self) -> dict[str]:
        salt = self._get_cmd('LD')['LD'].encode()
        password_digest = sha256(self._password).hexdigest().upper().encode()
        salted_digest = sha256(password_digest + salt).hexdigest().upper().encode()
        version_data = self._get_cmd(['cr_version', 'wa_inner_version'])
        self._cr_version = version_data['cr_version'].encode()
        self._wa_inner_version = version_data['wa_inner_version'].encode()
        version = self._wa_inner_version + self._cr_version
        if self._model == ZTERouterModel.MC888:
            self._version_digest = sha256(version).hexdigest().upper().encode()
        else:
            self._version_digest = md5(version).hexdigest().encode()
        request = {
            'goformId': 'LOGIN',
            'password': salted_digest,
        }
        if self._user:
            request['user'] = self._user
        return self._post(request)

    def reboot(self):
        """
        Reboot the router. Will perform login as needed.

        Returns:
            router response payload
        """
        if not self._version_digest:
            self._login()
        token = self._get_cmd('RD')['RD'].encode()
        salted_token = self._version_digest + token
        if self._model == ZTERouterModel.MC888:
            token_digest = sha256(salted_token).hexdigest().upper().encode()
        else:
            token_digest = md5(salted_token).hexdigest().encode()
        return self._post({
            'goformId': 'REBOOT_DEVICE',
            'AD': token_digest
        })
