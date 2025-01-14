from datetime import datetime
import json
import logging
import sys
from typing import List, Optional

import aiohttp
from aiohttp import ClientSession

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from . import APIRequestException
from ..helpers.const import *
from ..managers.configuration_manager import ConfigManager
from ..models.camera_data import CameraData

REQUIREMENTS = ["aiohttp"]

_LOGGER = logging.getLogger(__name__)


class ShinobiApi:
    """The Class for handling the data retrieval."""

    is_logged_in: bool
    group_id: Optional[str]
    api_key: Optional[str]
    session: Optional[ClientSession]
    camera_list: List[CameraData]
    hass: HomeAssistant
    config_manager: ConfigManager
    base_url: Optional[str]

    def __init__(self, hass: HomeAssistant, config_manager: ConfigManager):
        try:
            self._last_update = datetime.now()
            self.hass = hass
            self.config_manager = config_manager
            self.session_id = None
            self.is_logged_in = False
            self.group_id = None
            self.api_key = None
            self.session = None
            self.is_logged_in = False
            self.base_url = None

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to load Shinobi Video API, error: {ex}, line: {line_number}"
            )

    @property
    def is_initialized(self):
        return self.session is not None and not self.session.closed

    @property
    def config_data(self):
        return self.config_manager.data

    async def initialize(self):
        _LOGGER.info("Initializing Shinobi Video")

        try:
            config_data = self.config_data

            self.base_url = (
                f"{config_data.protocol}://{config_data.host}:{config_data.port}{config_data.path}"
            )

            self.is_logged_in = False
            self.camera_list = []

            if self.hass is None:
                if self.session is not None:
                    await self.session.close()

                self.session = aiohttp.client.ClientSession()
            else:
                self.session = async_create_clientsession(hass=self.hass)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize Shinobi Video API ({self.base_url}), error: {ex}, line: {line_number}"
            )

    def build_url(self, endpoint):
        url = f"{self.base_url}/{endpoint}"

        if GROUP_ID in url:
            url = url.replace(GROUP_ID, self.group_id)

        if AUTH_TOKEN in url:
            url = url.replace(AUTH_TOKEN, self.api_key)

        return url

    async def async_post(self, endpoint, request_data=None):
        result = None
        url = self.build_url(endpoint)

        try:
            _LOGGER.debug(f"POST {url}")

            async with self.session.post(url, data=request_data, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                self._last_update = datetime.now()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to post data to {endpoint}, Error: {ex}, Line: {line_number}"
            )

        return result

    async def async_get(self, endpoint):
        result = None
        url = self.build_url(endpoint)

        try:
            _LOGGER.debug(f"GET {url}")

            async with self.session.get(url, ssl=False) as response:
                _LOGGER.debug(f"Status of {url}: {response.status}")

                response.raise_for_status()

                result = await response.json()

                self._last_update = datetime.now()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to get data from {endpoint}, Error: {ex}, Line: {line_number}"
            )

        return result

    async def async_update(self):
        _LOGGER.info(f"Updating data from Shinobi Video Server ({self.config_data.name})")

        await self.load_camera()

    async def login(self):
        _LOGGER.info("Performing login")

        try:
            self.api_key = None

            config_data = self.config_manager.data

            data = {
                LOGIN_USERNAME: config_data.username,
                LOGIN_PASSWORD: config_data.password_clear_text
            }

            login_data = await self.async_post(URL_LOGIN, data)
            user_data = login_data.get("$user")

            if user_data.get("ok", False):
                self.group_id = user_data.get("ke")
                self.api_key = user_data.get("auth_token")
                uid = user_data.get("uid")

                _LOGGER.debug(f"Auth token: {self.api_key}")

                api_keys_data = await self.async_get(URL_API_KEYS)

                if api_keys_data.get("ok", False):
                    keys = api_keys_data.get("keys", [])

                    for key in keys:
                        key_uid = key.get("uid")

                        if key_uid == uid:
                            self.api_key = key.get("code")

                            _LOGGER.debug(f"Access token: {self.api_key}")

                            break
                else:
                    self.api_key = None
                    raise APIRequestException(URL_API_KEYS, login_data)

            else:
                raise APIRequestException(URL_LOGIN, login_data)

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(f"Failed to login, Error: {ex}, Line: {line_number}")

        self.is_logged_in = self.api_key is not None

        return self.is_logged_in

    async def load_camera(self):
        _LOGGER.debug("Retrieving camera list")

        camera_list = []
        monitors = await self.async_get(URL_MONITORS)

        for monitor in monitors:
            monitor_details_str = monitor.get("details")
            details = json.loads(monitor_details_str)

            monitor["details"] = details

            camera = CameraData(monitor)
            camera_list.append(camera)

        self.camera_list = camera_list
