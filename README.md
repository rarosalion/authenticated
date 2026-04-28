# authenticated

A platform which allows you to get information successful logins to Home Assistant.

Note that this integration is a very minor update from the [depreciated custom component](https://github.com/custom-components/authenticated) by @ludeeus. At this stage, it's simply an update of the development environment only.

It works for me, but hasn't gone through thorough testing or updates.

If that doesn't worry you, then you should know what to get from this repo, or use [HACS](https://hacs.xyz/).

For general info about securing your instance:
- https://www.home-assistant.io/docs/authentication/
- https://www.home-assistant.io/docs/authentication/multi-factor-auth
- https://www.home-assistant.io/docs/configuration/securing/

# Installation (HACS - preferred)
Add this repo as a custom repository in HACS: [https://github.com/rarosalion/authenticated](https://github.com/rarosalion/authenticated) (for instructions on how to add a custom repository you can visit https://hacs.xyz/docs/faq/custom_repositories/)
Add the config to configuration.yaml following the instructions below
# Installation (manual)
Using the tool of choice open the directory (folder) for your HA configuration (where you find configuration.yaml).
If you do not have a custom_components directory (folder) there, you need to create it.
In the custom_components directory (folder) create a new folder called authenticated.
Download all the files from the custom_components/authenticated/ directory (folder) in this repository.
Place the files you downloaded in the new directory (folder) you created.
Restart Home Assistant
Add the config to configuration.yaml following the instructions below

# Changelog

## v0.0.3

* Added notify_exclude_hostnames and notify_exclude_asns options 

## v0.0.2

* Updated for Python 3.13
* Included ASN and Organisational name output

## v0.0.1

* Initial fork of [custom-components/authenticated](https://github.com/custom-components/authenticated) by @ludeeus.
* Updated development environment for 2024.5.5 including Python 3.12



# Old Readme (may or may not be accurate)

**Example configuration.yaml:**

```yaml
sensor:
  - platform: authenticated
```

**Configuration variables:**

| key                     | required | default | description                                                                              |
| ----------------------- | -------- | ------- | ---------------------------------------------------------------------------------------- |
| **platform**            | yes      |         | The sensor platform name.                                                                |
| **enable_notification** | no       | `true`  | Turn on/off `persistant_notifications` when a new IP is detected, can be `true`/`false`. |
| **exclude**             | no       |         | A list of IP addresses you want to exclude.                                              |
| **provider**            | no       | 'ipapi' | The provider you want to use for GEO Lookup, 'ipapi', 'extreme', 'ipvigilante'.          |
| **log_location**        | no       |         | Full path to the logfile.                                                                |
| **notify_exclude_asns** | no       | []      | A list of ASNs that will be excluded from notifications. Note they will still be logged as normal, and this setting has no effect if `enable_notification` is set to `false`.
| **notify_exclude_hostnames** | no       | []      | A list of hostnames that will be excluded from notifications. Note they will still be logged as normal, and this setting has no effect if `enable_notification` is set to `false`.


**Sample overview:**\
![Sample overview](/img/overview.png)

If a new IP is detected, it will be added to a `.ip_authenticated.yaml` file in your configdir, with this information:

```yaml
8.8.8.8:
  city: Mountain View
  country: US
  hostname: google-public-dns-a.google.com
  last_authenticated: '2018-07-26 09:27:01'
  previous_authenticated_time: '2018-07-26 09:27:01'
  region: california
```

If not disabled, you will also be presented with a `persistent_notification` about the event:\
![notification](/img/persistant_notification.png)

## Debug logging

In your `configuration.yaml`

```yaml
logger:
  default: warn
  logs:
    custom_components.sensor.authenticated: debug
```

***
