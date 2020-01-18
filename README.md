# EnCh - Entity Checker

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

*EnCh is an [AppDaemon](https://github.com/home-assistant/appdaemon) app which can check Home Assistant entities and sends a notification if desired.*

## Supprted Checks

* low **battery levels** of various devices
* proper entity state, e.g. **not `unknown` or `unavailable`**
* **stale entites** (not updated for a specified time)

## Installation

Use [HACS](https://github.com/custom-components/hacs) or [download](https://github.com/benleb/ad-ench/releases) the `ench` directory from inside the `apps` directory here to your local `apps` directory, then add the configuration to enable the `ench` module.

## App configuration

Here's an exemplary configuration for this app (to be added to AppDaemon's configuration file, typically `apps.yaml`). Adjust the values as you wish.

```yaml
ench:
  module: ench
  class: EnCh
  notify: "notify.mobile_app_user"
  show_friendly_name: False
  exclude:
    - sensor.out_of_order
    - binary_sensor.always_unavailable
  battery:
    interval_min: 180
    min_level: 20
  unavailable:
    interval_min: 60
    notify: "notify.mobile_app_otheruser"
  stale:
    max_stale_min: 15
    entities:
      - binary_sensor.cube
      - sensor.humidity_stove
      - device_tracker.boatymcboatface
```

### Configuration

#### General

key | optional | type | default | description
-- | -- | -- | -- | --
`module` | False | string | ench | The module name of the app.
`class` | False | string | EnCh | The name of the python class.
`notify` | True | string | | The Home Assistant service used for notification
`initial_delay_secs` | True | int | 120 | Time to wait before first checks. This grace-period is necessary to give slow devices and integrations in Home Assistant a chance to become "available".
`exclude` | True | list | | Excluded entities. Supports wildcard/patterns via [fnmatch](https://docs.python.org/3/library/fnmatch.html)
`battery` | True | map | | Set to enable low battery check
`unavailable` | True | map | | Set to enable unavailable state check
`stale` | True | map | | Set to enable stale state/entity check

#### Battery configuration

key | optional | type | default | description
-- | -- | -- | -- | --
`min_level` | True | integer | 20 | Minimum battery level a entity should have
`interval_min` | True | integer | 180 | Minutes between checks
`notify` | True | string | | The Home Assistant service used for notification (Takes precedence over the `notify` setting configured in *General* section)

#### Unavailable/unknown state configuration

key | optional | type | default | description
-- | -- | -- | -- | --
`interval_min` | True | integer | 60 | Minutes between checks
`notify` | True | string | | The Home Assistant service used for notification (Takes precedence over the `notify` setting configured in *General* section)

#### Stale entity/state configuration

key | optional | type | default | description
-- | -- | -- | -- | --
`interval_min` | True | integer | 15 | Minutes between checks (if this is longer than `max_stale_min`, we use that instead)
`max_stale_min` | True | integer | 60 | If an entity is not updated during this time, a notification is triggered
`entities` | True | List | | If a list of entities is given, just these will be checked. Omitting this option checks all entities.
`notify` | True | string | | The Home Assistant service used for notification (Takes precedence over the `notify` setting configured in *General* section)
