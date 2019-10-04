# EnCh - Entity Checker

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

*REPLACES THE OLD [github.com/benleb/ad-batterycheck](https://github.com/benleb/ad-batterycheck)*

**NEEDS THE APPDAEMON BETA OR DEV BRANCH! Current stable (v3.0.5) will not work!**

*Entity check [AppDaemon](https://github.com/home-assistant/appdaemon) app which reads out the `battery_level` attribute and/or state (`unknown` or `unavailable` currently) of Home Assistant entities and sends a notification if desired.*

## Installation

Use [HACS](https://github.com/custom-components/hacs) or [download](https://github.com/benleb/ad-ench/releases) the `ench` directory from inside the `apps` directory here to your local `apps` directory, then add the configuration to enable the `ench` module.

## App configuration

```yaml
ench:
  module: ench
  class: EnCh
  notify: "notify.mobile_app"
  show_friendly_name: False
  exclude:
    - sensor.out_of_order
    - binary_sensor.always_unavailable
  battery:
    interval: 15
    min_level: 20
  unavailable:
    interval: 13
```

key | optional | type | default | description
-- | -- | -- | -- | --
`module` | False | string | ench | The module name of the app.
`class` | False | string | EnCh | The name of the python class.
`notify` | True | string | | The Home Assistant service used for notification
`notify` | True | list | | Excluded entities
`battery` | True | | | Set to enable low battery check
`min_level` | True | integer | 20 | Minimum battery level a entity should have
`interval` | True | integer | 18 | Hours between checks
`unavailable` | True | | | Set to enable unavailable state check
`interval` | True | integer | 6 | Hours between checks
