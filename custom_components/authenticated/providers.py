"""Providers."""

import logging

import requests

from . import AuthenticatedBaseException

_LOGGER = logging.getLogger(__name__)

PROVIDERS = {}


def register_provider(classname):
    """Register providers when used as a decorator."""
    PROVIDERS[classname.name] = classname
    return classname


class GeoProvider:
    """GeoProvider class."""

    url = None

    def __init__(self, ipaddr):
        """Initialize."""
        self.result = {}
        self.ipaddr = ipaddr

    @property
    def country(self):
        """Return country name or None."""
        return self.result.get("country")

    @property
    def region(self):
        """Return region name or None."""
        return self.result.get("region")

    @property
    def city(self):
        """Return city name or None."""
        return self.result.get("city")

    @property
    def asn(self):
        """Return ASN or None."""
        return self.result.get("asn")

    @property
    def org(self):
        """Return organisation name or None."""
        return self.result.get("org")

    @property
    def computed_result(self):
        """Return the computed result."""
        if self.result is not None:
            return {
                "country": self.country,
                "region": self.region,
                "city": self.city,
                "asn": self.asn,
                "org": self.org,
            }
        return None

    def update_geo_info(self):
        """Update Geo Information."""
        self.result = {}
        try:
            api = self.url.format(self.ipaddr)
            header = {"user-agent": "Home Assistant/Python"}
            data = requests.get(api, headers=header, timeout=5).json()

            _LOGGER.debug(data)

            if data.get("error"):
                if data.get("reason") == "RateLimited":
                    raise AuthenticatedBaseException(
                        "RatelimitError, try a different provider."
                    )

            elif data.get("status", "success") == "error" or data.get("reserved"):
                return

            elif data.get("status", "success") == "fail":
                raise AuthenticatedBaseException(
                    "[{}] - {}".format(
                        self.ipaddr, data.get("message", "Unknown error.")
                    )
                )

            self.result = data
            self.parse_data()
        except AuthenticatedBaseException as exception:
            _LOGGER.error(exception)
        except requests.exceptions.ConnectionError:
            pass

    def parse_data(self):
        """Parse data from geoprovider."""
        self.result = self.result


@register_provider
class IPApi(GeoProvider):
    """IPApi class."""

    url = "https://ipapi.co/{}/json"
    name = "ipapi"

    @property
    def country(self):
        """Return country name or None."""
        return self.result.get("country_name")


@register_provider
class IPInfo(GeoProvider):
    """IPInfo class."""

    url = "https://ipinfo.io/{}/json"
    name = "ipinfo"

    @property
    def asn(self):
        """Return ASN or None."""
        org = self.result.get("org")
        return org.split(" ", 1)[0] if org else None

    @property
    def org(self):
        """Return organisation name or None."""
        org = self.result.get("org")
        _LOGGER.debug(f"ORG: {org}")
        return org.split(" ", 1)[1] if org else None
