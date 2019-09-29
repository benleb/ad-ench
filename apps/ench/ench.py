"""AppDaemon EnCh app.

  @benleb / https://github.com/benleb/ad-ench

ench:
  module: ench
  class: EnCh
  battery_interval: 18
  battery_min_level: 20
  unavailable_interval: 6
  notify: notify.me
"""

from datetime import timedelta
from typing import Any, Dict

from adutils import ADutils
import appdaemon.plugins.hass.hassapi as hass

APP_NAME = "EnCh"
APP_ICON = "👩‍⚕️"
APP_VERSION = "0.1.0"

DEFAULT_BATTERY_MIN_LEVEL = 20
DEFAULT_INTERVAL = 18
DEFAULT_INTERVAL_BATTERY = 18
DEFAULT_INTERVAL_UNAVAILABLE = 6

EXCLUDED_ENTITIES = ["persistent_notification.config_entry_discovery"]

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
                interval=self.args.get("battery").get("interval", DEFAULT_INTERVAL_BATTERY),
                min_level=self.args.get("battery").get("min_level", DEFAULT_BATTERY_MIN_LEVEL),
            )

            # schedule check
            self.run_every(
                self.check_battery,
                self.datetime() + timedelta(seconds=5),
                self.cfg["battery"]["interval"] * 60 * 60,
            )

        # unavailable check
        if self.args.get("unavailable"):
            self.cfg["unavailable"] = dict(
                interval=self.args.get("unavailable").get("interval", DEFAULT_INTERVAL_UNAVAILABLE),
            )

            self.run_every(
                self.check_unavailable,
                self.datetime() + timedelta(seconds=3),
                self.cfg["unavailable"]["interval"] * 60 * 60,
            )

        self.adu = ADutils(APP_NAME, self.cfg, icon=APP_ICON, ad=self)
        self.adu.show_info()

    def check_battery(self, _: Any) -> None:
        """Handle scheduled checks."""
        entities_low_battery: Dict[str, int] = dict()

        for entity in self.get_state():
            if entity.lower() in EXCLUDED_ENTITIES:
                continue

            try:
                battery_level = self.get_state(entity_id=entity, attribute="battery_level")
                # self.log(f"{entity} -> {battery_level}")
                if battery_level and battery_level <= int(self.cfg["battery"]["min_level"]):
                    self.adu.log(f"Battery low! \033[1m{entity}\033[0m - \033[1m{int(battery_level)}%\033[0m", icon=ICONS['battery'])
                    entities_low_battery[entity] = battery_level
            except TypeError as error:
                self.adu.log(f"Getting state/battery level failed for {entity}: {error}")

        # send notification
        if self.cfg["notify"] and entities_low_battery:
            self.call_service(
                str(self.cfg["notify"]).replace(".", "/"),
                message=f"{ICONS['battery']} Battery low ({len(entities_low_battery)}): {', '.join([e for e in entities_low_battery])}",
            )

    def check_unavailable(self, _: Any) -> None:
        """Handle scheduled checks."""
        entities_unavailable: Dict[str, str] = dict()

        for entity in self.get_state():
            if entity.lower() in EXCLUDED_ENTITIES:
                continue

            try:
                state = self.get_state(entity_id=entity)
                if state in ["unavailable", "unknown"] and entity not in entities_unavailable:
                    entities_unavailable[entity] = state
            except TypeError as error:
                self.adu.log(f"Getting state/battery level failed for {entity}: {error}")

        for entity in sorted(entities_unavailable):
            state = entities_unavailable[entity]
            self.adu.log(f"State of \033[1m{entity}\033[0m{f' ({self.friendly_name(entity)})' if self.cfg['show_friendly_name'] else ''} is \033[1m{entities_unavailable[entity]}\033[0m!", icon=ICONS[state])

        # send notification
        if self.cfg["notify"] and entities_unavailable:
            self.call_service(
                str(self.cfg["notify"]).replace(".", "/"),
                message=f"{APP_ICON} Unavailable entities ({len(entities_unavailable)}): {', '.join([e for e in entities_unavailable])}",
            )
