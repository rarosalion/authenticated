"""A platform to get successful login information from Home Assistant.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/authenticated
"""

import json
import logging
import os
import socket
from contextlib import suppress
from datetime import datetime, timedelta
from ipaddress import ip_address as ValidateIP
from ipaddress import ip_network

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import yaml
from homeassistant.components import persistent_notification
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

from .const import (
    CONF_EXCLUDE,
    CONF_EXCLUDE_CLIENTS,
    CONF_LOG_LOCATION,
    CONF_NOTIFY,
    CONF_NOTIFY_ECLUDE_ASN,
    CONF_NOTIFY_ECLUDE_HOSTNAMES,
    CONF_PROVIDER,
    OUTFILE,
    STARTUP,
)
from .providers import PROVIDERS

_LOGGER = logging.getLogger(__name__)

ATTR_HOSTNAME = "hostname"
ATTR_COUNTRY = "country"
ATTR_REGION = "region"
ATTR_CITY = "city"
ATTR_ASN = "asn"
ATTR_ORG = "org"
ATTR_NEW_IP = "new_ip"
ATTR_LAST_AUTHENTICATE_TIME = "last_authenticated_time"
ATTR_PREVIOUS_AUTHENTICATE_TIME = "previous_authenticated_time"
ATTR_USER = "username"

SCAN_INTERVAL = timedelta(minutes=1)

PLATFORM_NAME = "authenticated"
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_PROVIDER, default="ipapi"): vol.In(list(PROVIDERS.keys())),
        vol.Optional(CONF_LOG_LOCATION, default=""): cv.string,
        vol.Optional(CONF_NOTIFY, default=True): cv.boolean,
        vol.Optional(CONF_NOTIFY_ECLUDE_ASN, default=[]): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Optional(CONF_NOTIFY_ECLUDE_HOSTNAMES, default=[]): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Optional(CONF_EXCLUDE, default=[]): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_EXCLUDE_CLIENTS, default=[]): vol.All(
            cv.ensure_list, [cv.string]
        ),
    }
)


def humanize_time(timestring):
    """Convert time."""
    return datetime.strptime(timestring[:19], "%Y-%m-%dT%H:%M:%S")


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Print startup message."""
    _LOGGER.info(STARTUP)

    """ Create the sensor. """
    notify = config.get(CONF_NOTIFY)
    notify_exclude_asn = config.get(CONF_NOTIFY_ECLUDE_ASN)
    notify_exclude_hostnames = config.get(CONF_NOTIFY_ECLUDE_HOSTNAMES)
    exclude = config.get(CONF_EXCLUDE)
    exclude_clients = config.get(CONF_EXCLUDE_CLIENTS)
    hass.data[PLATFORM_NAME] = {}

    if not load_authentications(
        hass.config.path(".storage/auth"), exclude, exclude_clients
    ):
        return False

    out = str(hass.config.path(OUTFILE))

    sensor = AuthenticatedSensor(
        hass,
        notify,
        out,
        exclude,
        exclude_clients,
        notify_exclude_asn,
        notify_exclude_hostnames,
        config[CONF_PROVIDER],
    )
    sensor.initial_run()

    add_devices([sensor], True)


class AuthenticatedSensor(Entity):
    """Representation of a Sensor."""

    def __init__(
        self,
        hass,
        notify,
        out,
        exclude,
        exclude_clients,
        notify_exclude_asn,
        notify_exclude_hostnames,
        provider,
    ):
        """Initialize the sensor."""
        self.hass = hass
        self._state = None
        self.provider = provider
        self.stored = {}
        self.last_ip = None
        self.exclude = exclude
        self.exclude_clients = exclude_clients
        self.notify = notify
        self.notify_exclude_asn = notify_exclude_asn
        self.notify_exclude_hostnames = notify_exclude_hostnames
        self.out = out

    def initial_run(self):
        """Run this at startup to initialize the platform data."""
        users, tokens = load_authentications(
            self.hass.config.path(".storage/auth"), self.exclude, self.exclude_clients
        )

        if os.path.isfile(self.out):
            self.stored = get_outfile_content(self.out)
        else:
            _LOGGER.debug("File has not been created, no data pressent.")

        for access in tokens:
            try:
                ValidateIP(access)
            except ValueError:
                continue

            accessdata = AuthenticatedData(access, tokens[access])

            if accessdata.ipaddr in self.stored:
                store = AuthenticatedData(accessdata.ipaddr, self.stored[access])
                accessdata.ipaddr = access

                if store.user_id is not None:
                    accessdata.user_id = store.user_id

                if store.hostname is not None:
                    accessdata.hostname = store.hostname

                if store.country is not None:
                    accessdata.country = store.country

                if store.region is not None:
                    accessdata.region = store.region

                if store.city is not None:
                    accessdata.city = store.city

                if store.asn is not None:
                    accessdata.asn = store.asn

                if store.org is not None:
                    accessdata.org = store.org

                if store.last_access is not None:
                    accessdata.last_access = store.last_access
                elif store.attributes.get("last_authenticated") is not None:
                    accessdata.last_access = store.attributes["last_authenticated"]
                elif store.attributes.get("last_used_at") is not None:
                    accessdata.last_access = store.attributes["last_used_at"]

                if store.prev_access is not None:
                    accessdata.prev_access = store.prev_access
                elif store.attributes.get("previous_authenticated_time") is not None:
                    accessdata.prev_access = store.attributes[
                        "previous_authenticated_time"
                    ]
                elif store.attributes.get("prev_used_at") is not None:
                    accessdata.prev_access = store.attributes["prev_used_at"]

            ipaddress = IPData(accessdata, users, self.provider, False)
            if accessdata.ipaddr not in self.stored:
                ipaddress.lookup()
            self.hass.data[PLATFORM_NAME][access] = ipaddress
        self.write_to_file()

    def update(self):
        """Update sensor value."""
        updated = False
        users, tokens = load_authentications(
            self.hass.config.path(".storage/auth"), self.exclude, self.exclude_clients
        )
        _LOGGER.debug("Users %s", users)
        _LOGGER.debug("Access %s", tokens)
        for access in tokens:
            try:
                ValidateIP(access)
            except ValueError:
                continue

            if access in self.hass.data[PLATFORM_NAME]:
                ipaddress = self.hass.data[PLATFORM_NAME][access]

                try:
                    new = humanize_time(tokens[access]["last_used_at"])
                    stored = humanize_time(ipaddress.last_used_at)

                    if new == stored:
                        continue
                    if new is None or stored is None:
                        continue
                    if new > stored:
                        updated = True
                        _LOGGER.info("New successful login from known IP (%s)", access)
                        ipaddress.prev_used_at = ipaddress.last_used_at
                        ipaddress.last_used_at = tokens[access]["last_used_at"]
                except Exception:  # pylint: disable=broad-except
                    pass
            else:
                updated = True
                _LOGGER.warning("New successful login from unknown IP (%s)", access)
                accessdata = AuthenticatedData(access, tokens[access])
                ipaddress = IPData(accessdata, users, self.provider)
                ipaddress.lookup()

            if ipaddress.hostname is None:
                ipaddress.hostname = get_hostname(ipaddress.ip_address)

            if ipaddress.new_ip:
                if self.notify:
                    if ipaddress.asn in self.notify_exclude_asn:
                        # ASN is in exclude list
                        pass
                    elif ipaddress.hostname in self.notify_exclude_hostnames:
                        # Host name is in exclude list
                        pass
                    else:
                        ipaddress.notify(self.hass)
                ipaddress.new_ip = False

            self.hass.data[PLATFORM_NAME][access] = ipaddress

        for ipaddr in sorted(
            tokens, key=lambda x: tokens[x]["last_used_at"], reverse=True
        ):
            self.last_ip = self.hass.data[PLATFORM_NAME][ipaddr]
            break
        if self.last_ip is not None:
            self._state = self.last_ip.ip_address
        if updated:
            self.write_to_file()

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Last successful authentication"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:lock-alert"

    @property
    def extra_state_attributes(self):
        """Return attributes for the sensor."""
        if self.last_ip is None:
            return None
        return {
            ATTR_HOSTNAME: self.last_ip.hostname,
            ATTR_COUNTRY: self.last_ip.country,
            ATTR_REGION: self.last_ip.region,
            ATTR_CITY: self.last_ip.city,
            ATTR_ASN: self.last_ip.asn,
            ATTR_ORG: self.last_ip.org,
            ATTR_USER: self.last_ip.username,
            ATTR_NEW_IP: self.last_ip.new_ip,
            ATTR_LAST_AUTHENTICATE_TIME: self.last_ip.last_used_at,
            ATTR_PREVIOUS_AUTHENTICATE_TIME: self.last_ip.prev_used_at,
        }

    def write_to_file(self):
        """Write data to file."""
        if os.path.exists(self.out):
            info = get_outfile_content(self.out)
        else:
            info = {}

        for known in self.hass.data[PLATFORM_NAME]:
            known = self.hass.data[PLATFORM_NAME][known]
            info[known.ip_address] = {
                "user_id": known.user_id,
                "username": known.username,
                "last_used_at": known.last_used_at,
                "prev_used_at": known.prev_used_at,
                "country": known.country,
                "hostname": known.hostname,
                "region": known.region,
                "city": known.city,
                "asn": known.asn,
                "org": known.org,
            }
        with open(self.out, "w") as out_file:
            yaml.dump(info, out_file, default_flow_style=False, explicit_start=True)


def get_outfile_content(file):
    """Get the content of the outfile."""
    with open(file) as out_file:
        content = yaml.load(out_file, Loader=yaml.FullLoader)
    out_file.close()

    if isinstance(content, dict):
        return content
    return {}


def get_geo_data(ip_address, provider):
    """Get geo data for an IP."""
    result = {"result": False, "data": "none"}
    geo_data = PROVIDERS[provider](ip_address)
    geo_data.update_geo_info()

    if geo_data.computed_result is not None:
        result = {"result": True, "data": geo_data.computed_result}

    return result


def get_hostname(ip_address):
    """Return hostname for an IP."""
    hostname = None
    with suppress(Exception):
        hostname = socket.getfqdn(ip_address)
    return hostname


def load_authentications(authfile, exclude, exclude_clients):
    """Load info from auth file."""
    if not os.path.exists(authfile):
        _LOGGER.critical("File is missing %s", authfile)
        return False
    with open(authfile) as authfile:
        auth = json.loads(authfile.read())

    users = {}
    for user in auth["data"]["users"]:
        users[user["id"]] = user["name"]

    tokens = auth["data"]["refresh_tokens"]
    tokens_cleaned = {}

    for token in tokens:
        try:
            for excludeaddress in exclude:
                if ValidateIP(token["last_used_ip"]) in ip_network(
                    excludeaddress, False
                ):
                    raise Exception("IP in excluded address configuration")
            if token["client_id"] in exclude_clients:
                raise Exception("Client in excluded clients configuration")
            if token.get("last_used_at") is None:
                continue
            if token["last_used_ip"] in tokens_cleaned:
                if (
                    token["last_used_at"]
                    > tokens_cleaned[token["last_used_ip"]]["last_used_at"]
                ):
                    tokens_cleaned[token["last_used_ip"]]["last_used_at"] = token[
                        "last_used_at"
                    ]
                    tokens_cleaned[token["last_used_ip"]]["user_id"] = token["user_id"]
            else:
                tokens_cleaned[token["last_used_ip"]] = {}
                tokens_cleaned[token["last_used_ip"]]["last_used_at"] = token[
                    "last_used_at"
                ]
                tokens_cleaned[token["last_used_ip"]]["user_id"] = token["user_id"]
        except Exception:  # Gotta Catch 'Em All
            pass

    return users, tokens_cleaned


class AuthenticatedData:
    """Data class for authenticated values."""

    def __init__(self, ipaddr, attributes):
        """Initialize."""
        self.ipaddr = ipaddr
        self.attributes = attributes
        self.last_access = attributes.get("last_used_at")
        self.prev_access = attributes.get("prev_used_at")
        self.country = attributes.get("country")
        self.region = attributes.get("region")
        self.city = attributes.get("city")
        self.asn = attributes.get("asn")
        self.org = attributes.get("org")
        self.user_id = attributes.get("user_id")
        self.hostname = attributes.get("hostname")


class IPData:
    """IP Address class."""

    def __init__(self, access_data, users, provider, new=True):
        """Initialize."""
        self.all_users = users
        self.provider = provider
        self.ip_address = access_data.ipaddr
        self.last_used_at = access_data.last_access
        self.prev_used_at = access_data.prev_access
        self.user_id = access_data.user_id
        self.hostname = access_data.hostname
        self.city = access_data.city
        self.region = access_data.region
        self.country = access_data.country
        self.asn = access_data.asn
        self.org = access_data.org
        self.new_ip = new

    @property
    def username(self):
        """Return the username used for the login."""
        if self.user_id is None:
            return "Unknown"
        if self.user_id in self.all_users:
            return self.all_users[self.user_id]
        return "Unknown"

    def lookup(self):
        """Look up data for the IP address."""
        geo = get_geo_data(self.ip_address, self.provider)
        if geo["result"]:
            self.country = geo.get("data", {}).get("country")
            self.region = geo.get("data", {}).get("region")
            self.city = geo.get("data", {}).get("city")
            self.asn = geo.get("data", {}).get("asn")
            self.org = geo.get("data", {}).get("org")

    def notify(self, hass):
        """Create persistant notification."""
        notify = persistent_notification.create
        message = f"""
        **IP Address:**   {self.ip_address}
        **Username:**    {self.username}
        """

        for notify_val, notify_str in [
            (self.country, "Country"),
            (self.hostname, "Hostname"),
            (self.region, "Region"),
            (self.city, "City"),
            (self.asn, "ASN"),
            (self.org, "Organisation"),
        ]:
            if notify_val is not None:
                message += f"**{notify_str}:**  {notify_val}\n"

        if self.last_used_at is not None:
            message += f"**Login time:**   {self.last_used_at[:19].replace('T', ' ')}"

        notify(message, title="New successful login", notification_id=self.ip_address)
