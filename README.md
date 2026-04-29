# Notes on Support (or lack thereof)

This integration was a very minor update from the [depreciated custom component](https://github.com/custom-components/authenticated) by @ludeeus.

Please consider this plugin "best effort". It was never my code, but I took it and got it working for me, and learned a few things in the process. It still works for me, and has seemingly worked for others. It's also been broken by Homeassistant updates, and left dead for long periods of time. If it breaks again, and you feel like submitting a PR to update it, I'll probably accept it and make a new release (when I see the PR). Otherwise, I might come back and fix it when it bothers me enough to spend some time on it.

If that bothers you, I completely understand. You're welcome to fork this code again (I might even use your version, if you're more reliable than me at updating it!), or find something else that meets your needs. If this doesn't bother you, please read on...

# authenticated

A platform which allows you to get information successful logins to Home Assistant.

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

## v0.0.5

* Merged documentation updates from BlythMeister
* Using async_create instead of deprecated persistent_notification (thanks miguelrjim)

## v0.0.4

* Added notify_exclude_hostnames and notify_exclude_asns options

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
| **provider**            | no       | 'ipinfo' | The provider you want to use for GEO Lookup, 'ipapi', 'ipinfo'.          |
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
