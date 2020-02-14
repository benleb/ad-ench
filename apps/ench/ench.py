"""AppDaemon EnCh app.

  @benleb / https://github.com/benleb/ad-ench

ench:
  module: ench
  class: EnCh
  notify: notify.me
  exclude:
    - sensor.out_of_order
    - binary_sensor.always_unavailable
  battery
    interval_min: 180
    min_level: 20
  unavailable
    interval_min: 60
  stale:
    max_stale_min: 15
    entities:
      - binary_sensor.cube
      - sensor.humidity_stove
      - device_tracker.boatymcboatface
"""

from datetime import datetime, timedelta
from fnmatch import fnmatch
from importlib import import_module
from typing import Any, Dict, List, Optional
from pkg_resources import parse_requirements as parse

import hassapi as hass
from pkg_helper import install_packages, missing_requirements

APP_NAME = "EnCh"
APP_ICON = "👩‍⚕️"
APP_VERSION = "0.6.0"
APP_REQUIREMENTS = {"adutils~=0.4.9"}

BATTERY_MIN_LEVEL = 20
INTERVAL_BATTERY_MIN = 180
INTERVAL_BATTERY = INTERVAL_BATTERY_MIN / 60

INTERVAL_UNAVAILABLE_MIN = 60
INTERVAL_UNAVAILABLE = INTERVAL_UNAVAILABLE_MIN / 60

INTERVAL_STALE_MIN = 15
MAX_STALE_MIN = 60

INITIAL_DELAY = 60

EXCLUDE = ["binary_sensor.updater", "persistent_notification.config_entry_discovery"]
BAD_STATES = ["unavailable", "unknown"]
LEVEL_ATTRIBUTES = ["battery_level", "Battery Level"]

ICONS = dict(battery="🔋", unavailable="⁉️ ", unknown="❓", stale="⏰")

# install requirements
missing = missing_requirements(APP_REQUIREMENTS)
if missing and install_packages(missing):
    [import_module(req.key) for req in parse(APP_REQUIREMENTS)]

from adutils import ADutils, hl, hl_entity  # noqa


class EnCh(hass.Hass):  # type: ignore
    """EnCh."""

    async def initialize(self) -> None:
        """Register API endpoint."""
        self.cfg: Dict[str, Any] = dict()
        self.cfg["show_friendly_name"] = bool(self.args.get("show_friendly_name", True))
        self.cfg["init_delay_secs"] = int(
            self.args.get("initial_delay_secs", INITIAL_DELAY)
        )

        # global notification
        if "notify" in self.args:
            self.cfg["notify"] = self.args.get("notify")

        # initial wait to give all devices a chance to become available
        init_delay = await self.datetime() + timedelta(
            seconds=self.cfg["init_delay_secs"]
        )

        # battery check
        if "battery" in self.args:

            config = self.args.get("battery")

            # store configuration
            self.cfg["battery"] = dict(
                interval_min=int(config.get("interval_min", INTERVAL_BATTERY_MIN)),
                min_level=int(config.get("min_level", BATTERY_MIN_LEVEL)),
            )

            # no, per check or global notification
            self.choose_notify_receipient("battery", config)

            # schedule check
            await self.run_every(
                self.check_battery,
                init_delay,
                self.cfg["battery"]["interval_min"] * 60,
            )

        # unavailable check
        if "unavailable" in self.args:

            config = self.args.get("unavailable")

            # store configuration
            self.cfg["unavailable"] = dict(
                interval_min=int(config.get("interval_min", INTERVAL_UNAVAILABLE_MIN)),
            )

            # no, per check or global notification
            self.choose_notify_receipient("unavailable", config)

            # schedule check
            self.run_every(
                self.check_unavailable,
                await self.datetime() + timedelta(seconds=self.cfg["init_delay_secs"]),
                self.cfg["unavailable"]["interval_min"] * 60,
            )

        # stale entities check
        if "stale" in self.args:

            config = self.args.get("stale", {})
            interval_min = config.get("interval_min", INTERVAL_STALE_MIN)
            max_stale_min = config.get("max_stale_min", MAX_STALE_MIN)

            # store configuration
            self.cfg["stale"] = dict(
                interval_min=int(min([interval_min, max_stale_min])),
                max_stale_min=int(max_stale_min),
            )

            self.cfg["stale"]["entities"] = config.get("entities", [])

            # no, per check or global notification
            self.choose_notify_receipient("stale", config)

            # schedule check
            self.run_every(
                self.check_stale,
                await self.datetime() + timedelta(seconds=self.cfg["init_delay_secs"]),
                self.cfg["stale"]["interval_min"] * 60,
            )

        # merge excluded entities
        exclude = set(EXCLUDE)
        exclude.update([e.lower() for e in self.args.get("exclude", set())])
        self.cfg["exclude"] = sorted(list(exclude))

        # set units
        self.cfg.setdefault(
            "_units", dict(interval_min="min", max_stale_min="min", min_level="%"),
        )

        # init adutils
        self.adu = ADutils(APP_NAME, self.cfg, icon=APP_ICON, ad=self, show_config=True)

    async def check_battery(self, _: Any) -> None:
        """Handle scheduled checks."""
        check_config = self.cfg["battery"]
        results: List[str] = []

        self.adu.log(f"Checking entities for low battery levels...", icon=APP_ICON)

        entities = filter(
            lambda entity: not any(
                fnmatch(entity, pattern) for pattern in self.cfg["exclude"]
            ),
            await self.get_state(),
        )

        for entity in sorted(entities):
            battery_level = None
            try:
                # check entities which may be battery level sensors
                if "battery_level" in entity or "battery" in entity:
                    battery_level = int(await self.get_state(entity))

                # check entity attributes for battery levels
                if not battery_level:
                    for attr in LEVEL_ATTRIBUTES:
                        battery_level = int(
                            await self.get_state(entity, attribute=attr)
                        )
                        break
            except (TypeError, ValueError):
                pass

            if battery_level and battery_level <= check_config["min_level"]:
                results.append(entity)
                self.adu.log(
                    f"{await self._name(entity)} has low "
                    f"{hl(f'battery → {hl(int(battery_level))}')}% | "
                    f"last update: {await self.adu.last_update(entity)}",
                    icon=ICONS["battery"],
                )

        # send notification
        notify = self.cfg.get("notify") or check_config.get("notify")
        if notify and results:
            self.call_service(
                str(notify).replace(".", "/"),
                message=f"{ICONS['battery']} Battery low ({len(results)}): "
                f"{', '.join([e for e in results])}",
            )

        self._print_result("battery", results, "low battery levels")

    async def check_unavailable(self, _: Any) -> None:
        """Handle scheduled checks."""
        check_config = self.cfg["unavailable"]
        results: List[str] = []

        self.adu.log(
            f"Checking entities for unavailable/unknown state...", icon=APP_ICON
        )

        entities = filter(
            lambda entity: not any(
                fnmatch(entity, pattern) for pattern in self.cfg["exclude"]
            ),
            await self.get_state(),
        )

        for entity in sorted(entities):
            state = await self.get_state(entity_id=entity)

            if state in BAD_STATES and entity not in results:
                results.append(entity)
                self.adu.log(
                    f"{await self._name(entity)} is {hl(state)} | "
                    f"last update: {await self.adu.last_update(entity)}",
                    icon=ICONS[state],
                )

        # send notification
        notify = self.cfg.get("notify") or check_config.get("notify")
        if notify and results:
            self.call_service(
                str(notify).replace(".", "/"),
                message=f"{APP_ICON} Unavailable entities ({len(results)}): "
                f"{', '.join([e for e in results])}",
            )

        self._print_result("unavailable", results, "unavailable/unknown state")

    async def check_stale(self, _: Any) -> None:
        check_config = self.cfg["stale"]
        """Handle scheduled checks."""
        results: List[str] = []

        self.adu.log(f"Checking for stale entities...", icon=APP_ICON)

        if self.cfg["stale"]["entities"]:
            all_entities = self.cfg["stale"]["entities"]
        else:
            all_entities = await self.get_state()

        entities = filter(
            lambda entity: not any(
                fnmatch(entity, pattern) for pattern in self.cfg["exclude"]
            ),
            all_entities,
        )

        for entity in sorted(entities):

            last_update = self.convert_utc(
                await self.get_state(entity_id=entity, attribute="last_updated")
            )
            now: datetime = await self.datetime(aware=True)

            stale_time: timedelta = now - last_update
            max_stale_min = timedelta(minutes=self.cfg["stale"]["max_stale_min"])

            if stale_time and stale_time >= max_stale_min:
                results.append(entity)
                self.adu.log(
                    f"{await self._name(entity)} is "
                    f"{hl(f'stale since {hl(int(stale_time.seconds / 60))}')}min | "
                    f"last update: {await self.adu.last_update(entity)}",
                    icon=ICONS["stale"],
                )

        # send notification
        notify = self.cfg.get("notify") or check_config.get("notify")
        if notify and results:
            self.call_service(
                str(notify).replace(".", "/"),
                message=f"{APP_ICON} Stalled entities ({len(results)}): "
                f"{', '.join([e for e in results])}",
            )

        self._print_result("stale", results, "stalled updates")

    def choose_notify_receipient(self, check: str, config: Dict[str, Any]) -> None:
        if "notify" in config and "notify" not in self.cfg:
            self.cfg[check]["notify"] = config["notify"]

    async def _name(self, entity: str, friendly_name: bool = False) -> Optional[str]:
        name: Optional[str] = None
        if self.cfg["show_friendly_name"]:
            name = await self.friendly_name(entity)
        else:
            name = hl_entity(entity)
        return name

    def _print_result(self, check: str, entities: List[str], reason: str) -> None:
        # entites_found = len(entities)
        if entities:
            self.adu.log(
                f"{hl(f'{len(entities)} entities')} with {hl(reason)}!", icon=APP_ICON,
            )
        else:
            self.adu.log(f"{hl(f'no entities')} with {hl(reason)}!", icon=APP_ICON)
