## App configuration

```yaml
ench:
  module: ench
  class: EnCh
  notify: "notify.mobile_app"
  show_friendly_name: False
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
`battery` | True | | | Set to enable low battery check
`min_level` | True | integer | 20 | Minimum battery level a entity should have
`interval` | True | integer | 18 | Hours between checks
`unavailable` | True | | | Set to enable unavailable state check
`interval` | True | integer | 18 | Hours between checks
