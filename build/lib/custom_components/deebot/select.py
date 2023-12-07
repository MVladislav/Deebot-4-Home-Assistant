"""Select module."""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic

from deebot_client.capabilities import CapabilitySetTypes
from deebot_client.device import Device
from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .controller import DeebotController
from .entity import DeebotEntity, DeebotEntityDescription, EventT


@dataclass(kw_only=True)
class DeebotSelectEntityDescription(
    SelectEntityDescription,  # type: ignore
    DeebotEntityDescription,
    Generic[EventT],
):
    """Deebot select entity description."""

    current_option_fn: Callable[[EventT], str | None]
    options_fn: Callable[[CapabilitySetTypes], list[str]]


ENTITY_DESCRIPTIONS: tuple[DeebotSelectEntityDescription, ...] = (
    DeebotSelectEntityDescription(
        capability_fn=lambda caps: caps.settings.efficiency_mode,
        current_option_fn=lambda e: e.efficiency.display_name,
        options_fn=lambda eff: [mode.display_name for mode in eff.types],
        key="efficiency_mode",
        translation_key="efficiency_mode",
        entity_registry_enabled_default=False,
        icon="mdi:lightning-bolt",
        entity_category=EntityCategory.CONFIG,
    ),
    DeebotSelectEntityDescription(
        capability_fn=lambda caps: caps.fan_speed,
        current_option_fn=lambda e: e.speed.display_name,
        options_fn=lambda speed: [mode.display_name for mode in speed.types],
        key="fan_speed",
        translation_key="fan_speed",
        entity_registry_enabled_default=False,
        icon="mdi:fan-chevron-up",
        entity_category=EntityCategory.CONFIG,
    ),
    DeebotSelectEntityDescription(
        capability_fn=lambda caps: caps.water,
        current_option_fn=lambda e: e.amount.display_name,
        options_fn=lambda water: [amount.display_name for amount in water.types],
        key="water_amount",
        translation_key="water_amount",
        entity_registry_enabled_default=False,
        icon="mdi:water",
        entity_category=EntityCategory.CONFIG,
    ),
    DeebotSelectEntityDescription(
        capability_fn=lambda caps: caps.clean.work_mode,
        current_option_fn=lambda e: e.mode.display_name,
        options_fn=lambda cap: [mode.display_name for mode in cap.types],
        key="work_mode",
        translation_key="work_mode",
        entity_registry_enabled_default=False,
        icon="mdi:cog",
        entity_category=EntityCategory.CONFIG,
    ),
)

ENTITY_ENABLE_DESCRIPTIONS: tuple[DeebotSelectEntityDescription, ...] = (
    DeebotSelectEntityDescription(
        capability_fn=lambda caps: caps.clean.auto_empty
        if caps.clean.auto_empty
        else None,
        current_option_fn=lambda e: e.mode.display_name,
        options_fn=lambda aut: [mode.display_name for mode in aut.types],
        key="auto_empty",
        translation_key="auto_empty",
        entity_registry_enabled_default=False,
        icon="mdi:delete-empty",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add entities for passed config_entry in HA."""
    controller: DeebotController = hass.data[DOMAIN][config_entry.entry_id]
    controller.register_platform_add_entities(
        DeebotSelectEntity, ENTITY_DESCRIPTIONS, async_add_entities
    )
    controller.register_platform_add_entities(
        DeebotSelectEnableEntity, ENTITY_ENABLE_DESCRIPTIONS, async_add_entities
    )


class DeebotSelectEntity(
    DeebotEntity[CapabilitySetTypes[EventT, str, str], DeebotSelectEntityDescription],
    SelectEntity,  # type: ignore
):
    """Deebot select entity."""

    _attr_current_option: str | None = None

    def __init__(
        self,
        device: Device,
        capability: CapabilitySetTypes[EventT, str, str],
        entity_description: DeebotSelectEntityDescription | None = None,
        **kwargs: Any,
    ):
        super().__init__(device, capability, entity_description, **kwargs)
        self._attr_options = self.entity_description.options_fn(capability)

    async def async_added_to_hass(self) -> None:
        """Set up the event listeners now that hass is ready."""
        await super().async_added_to_hass()

        async def on_water_info(event: EventT) -> None:
            self._attr_current_option = self.entity_description.current_option_fn(event)
            self.async_write_ha_state()

        self.async_on_remove(
            self._device.events.subscribe(self._capability.event, on_water_info)
        )

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._device.execute_command(self._capability.set(option))


class DeebotSelectEnableEntity(
    DeebotEntity[
        CapabilitySetTypes[EventT, bool, str, str], DeebotSelectEntityDescription
    ],
    SelectEntity,  # type: ignore
):
    """Deebot select entity."""

    _attr_current_option: str | None = None

    def __init__(
        self,
        device: Device,
        capability: CapabilitySetTypes[EventT, bool, str, str],
        entity_description: DeebotSelectEntityDescription | None = None,
        **kwargs: Any,
    ):
        super().__init__(device, capability, entity_description, **kwargs)
        self._attr_options = self.entity_description.options_fn(capability)

    async def async_added_to_hass(self) -> None:
        """Set up the event listeners now that hass is ready."""
        await super().async_added_to_hass()

        async def on_water_info(event: EventT) -> None:
            self._attr_current_option = self.entity_description.current_option_fn(event)
            self.async_write_ha_state()

        self.async_on_remove(
            self._device.events.subscribe(self._capability.event, on_water_info)
        )

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self._device.execute_command(self._capability.set(True, option))
