"""AppDaemon EnCh app.

  @benleb / https://github.com/benleb/ad-ench

ench:
  module: ench
  class: EnCh
  exclude:
    - sensor.out_of_order
    - binary_sensor.always_unavailable
  battery
    interval: 18
    min_level: 20
  unavailable
    interval: 6
  notify: notify.me
"""

from datetime import timedelta
from typing import Any, Dict

import adutils
import hassapi as hass

APP_NAME = "EnCh"
APP_ICON = "👩‍⚕️"
APP_VERSION = "0.4.3"

BATTERY_MIN_LEVEL = 20
INTERVAL_BATTERY = 18
INTERVAL_UNAVAILABLE = 6

EXCLUDE = [
    "binary_sensor.updater",
    "persistent_notification.config_entry_discovery",
]

ICONS = dict(
    battery="🔋",
    unavailable="⁉️ ",
    unknown="❓",
)


class EnCh(hass.Hass):  # type: ignore
    """ench."""

    def initialize(self) -> None:
        """Register API endpoint."""
        self.cfg: Dict[str, Any] = dict()
        self.cfg["notify"] = self.args.get("notify")
        self.cfg["show_friendly_name"] = bool(self.args.get("show_friendly_name", True))

        # battery check
        if "battery" in self.args:
            self.cfg["battery"] = dict(
                interval=self.args.get("battery").get("interval", INTERVAL_BATTERY),
                min_level=self.args.get("battery").get("min_level", BATTERY_MIN_LEVEL),
            )

            # schedule check
            self.run_every(
                self.check_battery,
                self.datetime() + timedelta(seconds=60),
                self.cfg["battery"]["interval"] * 60 * 60,
            )

        # unavailable check
        if self.args.get("unavailable"):
            self.cfg["unavailable"] = dict(
                interval=self.args.get("unavailable").get("interval", INTERVAL_UNAVAILABLE),
            )

            self.run_every(
                self.check_unavailable,
                self.datetime() + timedelta(seconds=55),
                self.cfg["unavailable"]["interval"] * 60 * 60,
            )

        # merge excluded entities
        exclude = set(EXCLUDE)
        exclude.update([e.lower() for e in self.args.get("exclude", set())])
        self.cfg["exclude"] = sorted(list(exclude))

        # set units
        self.cfg.setdefault("_units", dict(interval="h", min_level="%"))

        # init adutils
        self.adu = adutils.ADutils(APP_NAME, self.cfg, icon=APP_ICON, ad=self, show_config=True)

    def check_battery(self, _: Any) -> None:
        """Handle scheduled checks."""
        entities_low_battery: Dict[str, int] = dict()

        self.adu.log(f"Checking entities for low battery levels...", APP_ICON)
        for entity in self.get_state():
            if entity.lower() in self.cfg["exclude"]:
                continue

            try:
                battery_level = self.get_state(entity_id=entity, attribute="battery_level")
                if battery_level and battery_level <= int(self.cfg["battery"]["min_level"]):
                    self.adu.log(f"Battery low! \033[1m{entity}\033[0m → \033[1m{int(battery_level)}%\033[0m", icon=ICONS['battery'])
                    entities_low_battery[entity] = battery_level
            except TypeError as error:
                self.adu.log(f"Getting state/battery level failed for {entity}: {error}")

        # send notification
        if self.cfg["notify"] and entities_low_battery:
            self.call_service(
                str(self.cfg["notify"]).replace(".", "/"),
                message=f"{ICONS['battery']} Battery low ({len(entities_low_battery)}): {', '.join([e for e in entities_low_battery])}",
            )

        self._print_result("battery", entities_low_battery, "low battery levels")

    def check_unavailable(self, _: Any) -> None:
        """Handle scheduled checks."""
        entities_unavailable: Dict[str, str] = dict()

        self.adu.log(f"Checking entities for unavailable/unknown state...", APP_ICON)
        for entity in self.get_state():
            if entity.lower() in self.cfg["exclude"]:
                continue

            try:
                state = self.get_state(entity_id=entity)
                if state in ["unavailable", "unknown"] and entity not in entities_unavailable:
                    entities_unavailable[entity] = state
            except TypeError as error:
                self.adu.log(f"Getting state/battery level failed for {entity}: {error}")

        for entity in sorted(entities_unavailable):
            state = entities_unavailable[entity]
            self.adu.log(f"\033[1m{entity}\033[0m{f' ({self.friendly_name(entity)})' if self.cfg['show_friendly_name'] else ''} is \033[1m{entities_unavailable[entity]}\033[0m!", icon=ICONS[state])

        # send notification
        if self.cfg["notify"] and entities_unavailable:
            self.call_service(
                str(self.cfg["notify"]).replace(".", "/"),
                message=f"{APP_ICON} Unavailable entities ({len(entities_unavailable)}): {', '.join([e for e in entities_unavailable])}",
            )

        self._print_result("unavailable", entities_unavailable, "unavailable/unknown state")

    def _print_result(self, check: str, entities: Dict[str, Any], reason: str) -> None:
        entites_found = len(entities)
        if entites_found > 0:
            self.adu.log(f"got \033[1m{entites_found} entities\033[0m with \033[1m{reason}\033[0m!\n", APP_ICON)
        else:
            self.adu.log(f"no entities with {reason} found", APP_ICON)
