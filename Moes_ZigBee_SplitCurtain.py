"""Tuya MCU based cover and blinds."""
from typing import Dict, Optional, Union
from zigpy.profiles import zha
import zigpy.types as t
from zigpy.zcl import foundation
from zigpy.zcl.clusters.closures import WindowCovering
from zigpy.zcl.clusters.general import (
    Basic,
    GreenPowerProxy,
    Groups,
    # Identify,
    Ota,
    Scenes,
    Time,
)

from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
)
from zhaquirks.tuya import (
    NoManufacturerCluster,
    TUYA_MCU_COMMAND,
    TuyaLocalCluster,
    # TuyaManufacturerWindowCover,
    # TuyaManufCluster,
    TuyaWindowCover,
    # TuyaWindowCoverControl,
)
from zhaquirks.tuya.mcu import (
    DPToAttributeMapping,
    TuyaClusterData,
    # TuyaDPType,
    TuyaMCUCluster,
)


# Maps OPEN/CLOSE/STOP cover commands from Tuya to Zigbee
# https://github.com/zigpy/zigpy/blob/master/zigpy/zcl/clusters/closures.py#L558
# https://developer.tuya.com/en/docs/iot-device-dev/zigbee-curtain-switch-access-standard?id=K9ik6zvra3twv#title-7-DP1%20and%20DP4%20Curtain%20switch%201%20and%202
class TuyaCC(t.enum8):
    """Tuya cover commands."""

    OPEN = 0x00
    STOP = 0x01
    CLOSE = 0x02


class ZclCC(t.enum8):
    """ZCL cover commands."""

    OPEN = 0x00
    CLOSE = 0x01
    STOP = 0x02


TUYA2ZB_COMMANDS = {
    ZclCC.OPEN: TuyaCC.OPEN,
    ZclCC.CLOSE: TuyaCC.CLOSE,
    ZclCC.STOP: TuyaCC.STOP,
}


class TuyaWindowCovering(NoManufacturerCluster, WindowCovering, TuyaLocalCluster):
    """Tuya MCU WindowCovering cluster."""

    """Add additional attributes for direction"""
    attributes = WindowCovering.attributes.copy()
    attributes.update(
        {
            0xF000: ("curtain_switch", t.enum8, True),  # 0: open, 1: stop, 2: close
            0xF001: ("accurate_calibration", t.enum8, True),  # 0: calibration started, 1: calibration finished
            0xF002: ("motor_steering", t.enum8, True),  # 0: default, 1: reverse
            0xF003: ("travel", t.uint16_t, True),  # 30 to 9000 (units of 0.1 seconds)
        }
    )

    async def command(
        self,
        command_id: Union[foundation.GeneralCommand, int, t.uint8_t],
        *args,
        manufacturer: Optional[Union[int, t.uint16_t]] = None,
        expect_reply: bool = True,
        tsn: Optional[Union[int, t.uint8_t]] = None,
    ):
        """Override the default Cluster command."""

        # if manufacturer is None:
        #     manufacturer = self.endpoint.device.manufacturer

        self.debug(
            "Sending Tuya Cluster Command. Cluster Command is %x, Arguments are %s",
            command_id,
            args,
        )

        # (upopen, downclose, stop)
        if command_id in (0x0002, 0x0000, 0x0001):  # ¿0x0003: continue?
            cluster_data = TuyaClusterData(
                endpoint_id=self.endpoint.endpoint_id,
                cluster_name=self.ep_attribute,
                cluster_attr="curtain_switch",
                attr_value=TUYA2ZB_COMMANDS[command_id],  # convert tuya2zigbee command
                expect_reply=expect_reply,
                manufacturer=-1,
            )
            self.endpoint.device.command_bus.listener_event(
                TUYA_MCU_COMMAND,
                cluster_data,
            )
            return foundation.GENERAL_COMMANDS[
                foundation.GeneralCommand.Default_Response
            ].schema(command_id=command_id, status=foundation.Status.SUCCESS)

        # (go_to_lift_percentage)
        elif command_id == 0x0005:
            lift_value = args[0]

            cluster_data = TuyaClusterData(
                endpoint_id=self.endpoint.endpoint_id,
                cluster_name=self.ep_attribute,
                cluster_attr="current_position_lift_percentage",
                attr_value=lift_value,
                expect_reply=expect_reply,
                manufacturer=-1,
            )
            self.endpoint.device.command_bus.listener_event(
                TUYA_MCU_COMMAND,
                cluster_data,
            )
            return foundation.GENERAL_COMMANDS[
                foundation.GeneralCommand.Default_Response
            ].schema(command_id=command_id, status=foundation.Status.SUCCESS)

        # # Custom Command
        # elif command_id == 0x0006:  # ¿doc reference?
        #     tuya_payload.status = args[0]
        #     tuya_payload.tsn = args[1]
        #     tuya_payload.command_id = args[2]
        #     tuya_payload.function = args[3]
        #     tuya_payload.data = args[4]

        self.warning("Unsupported command_id: %s", command_id)
        return foundation.GENERAL_COMMANDS[
            foundation.GeneralCommand.Default_Response
        ].schema(command_id=command_id, status=foundation.Status.UNSUP_CLUSTER_COMMAND)


class TuyaWindowCoverManufCluster(TuyaMCUCluster):
    """Tuya with WindowCover data points."""

    attributes = TuyaMCUCluster.attributes.copy()
    attributes.update(
        {
            0x5000: ("backlight_mode", t.enum8, True),  # 0: off, 1: on
            0x8001: ("indicator_status", t.enum8, True),  # 0: status, 1: position, 2: off (¿backlight_mode?)
        }
    )

    dp_to_attribute: Dict[int, DPToAttributeMapping] = {
        1: DPToAttributeMapping(
            TuyaWindowCovering.ep_attribute,
            "curtain_switch",
            # dp_type=TuyaDPType.ENUM,
        ),
        2: DPToAttributeMapping(
            TuyaWindowCovering.ep_attribute,
            "current_position_lift_percentage",  # for Slider movement
            # dp_type=TuyaDPType.VALUE,
        ),
        3: DPToAttributeMapping(
            TuyaWindowCovering.ep_attribute,
            "current_position_lift_percentage",  # for Slider updates
            # dp_type=TuyaDPType.ENUM,
        ),
        # 4: DPToAttributeMapping(
        #     TuyaWindowCovering.ep_attribute,
        #     "on_off",
        #     dp_type=TuyaDPType.ENUM,
        #     endpoint_id=2,
        # ),
        # 5: DPToAttributeMapping(
        #     TuyaWindowCovering.ep_attribute,
        #     "current_position_lift_percentage",
        #     dp_type=TuyaDPType.VALUE,
        #     endpoint_id=2,
        # ),
        # 6: DPToAttributeMapping(
        #     TuyaWindowCovering.ep_attribute,
        #     "accurate_calibration",
        #     dp_type=TuyaDPType.ENUM,
        #     endpoint_id=2,
        # ),
        # 7: DPToAttributeMapping(
        #     TuyaMCUCluster.ep_attribute,
        #     "backlight_mode",
        #     dp_type=TuyaDPType.ENUM,
        # ),
        # 8: DPToAttributeMapping(
        #     TuyaWindowCovering.ep_attribute,
        #     "motor_steering",
        #     dp_type=TuyaDPType.ENUM,
        # ),
        # 9: DPToAttributeMapping(
        #     TuyaWindowCovering.ep_attribute,
        #     "motor_steering",
        #     dp_type=TuyaDPType.ENUM,
        #     endpoint_id=2,
        # ),
        # 10: DPToAttributeMapping(
        #     TuyaWindowCovering.ep_attribute,
        #     "quick_calibration",
        #     dp_type=TuyaDPType.ENUM,
        # ),
        # 11: DPToAttributeMapping(
        #     TuyaWindowCovering.ep_attribute,
        #     "quick_calibration",
        #     dp_type=TuyaDPType.ENUM,
        #     endpoint_id=2,
        # ),
        # 14: DPToAttributeMapping(
        #     TuyaMCUCluster.ep_attribute,
        #     "indicator_status",
        #     dp_type=TuyaDPType.ENUM,
        # ),
    }

    data_point_handlers = {
        1: "_dp_2_attr_update",
        2: "_dp_2_attr_update",
        3: "_dp_2_attr_update",
        4: "_dp_2_attr_update",
        5: "_dp_2_attr_update",
        6: "_dp_2_attr_update",
        7: "_dp_2_attr_update",
        8: "_dp_2_attr_update",
        9: "_dp_2_attr_update",
        10: "_dp_2_attr_update",
        11: "_dp_2_attr_update",
        14: "_dp_2_attr_update",
    }


class TuyaCover0601_GP(TuyaWindowCover):
    """Tuya blind controller device."""
    signature = {
        # "NodeDescriptor(
        #     logical_type=<LogicalType.Router: 1>, complex_descriptor_available=0, user_descriptor_available=0,
        #     reserved=0, aps_flags=0, frequency_band=<FrequencyBand.Freq2400MHz: 8>,
        #     mac_capability_flags=<MACCapabilityFlags.AllocateAddress|RxOnWhenIdle|MainsPowered|FullFunctionDevice: 142>,
        #     manufacturer_code=4417, maximum_buffer_size=66, maximum_incoming_transfer_size=66, server_mask=10752,
        #     maximum_outgoing_transfer_size=66, descriptor_capability_field=<DescriptorCapability.NONE: 0>,
        #     *allocate_address=True, *is_alternate_pan_coordinator=False, *is_coordinator=False, *is_end_device=False,
        #     *is_full_function_device=True, *is_mains_powered=True, *is_receiver_on_when_idle=True, *is_router=True, *is_security_capable=False
        # )
        MODELS_INFO: [
            ("_TZE204_guvc7pdy", "TS0601"),
        ],
        ENDPOINTS: {
            1: {
                PROFILE_ID: zha.PROFILE_ID,
                DEVICE_TYPE: zha.DeviceType.SMART_PLUG,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaWindowCoverManufCluster.cluster_id,
                ],
                OUTPUT_CLUSTERS: [Time.cluster_id, Ota.cluster_id],
            },
            242: {
                PROFILE_ID: 41440,
                DEVICE_TYPE: 97,
                INPUT_CLUSTERS: [],
                OUTPUT_CLUSTERS: [GreenPowerProxy.cluster_id],
            },
        },
    }

    replacement = {
        ENDPOINTS: {
            1: {
                DEVICE_TYPE: zha.DeviceType.WINDOW_COVERING_DEVICE,
                INPUT_CLUSTERS: [
                    Basic.cluster_id,
                    Groups.cluster_id,
                    Scenes.cluster_id,
                    TuyaWindowCoverManufCluster,
                    TuyaWindowCovering,
                ],
                OUTPUT_CLUSTERS: [Time.cluster_id, Ota.cluster_id],
            },
            242: {
                PROFILE_ID: 41440,
                DEVICE_TYPE: 97,
                INPUT_CLUSTERS: [],
                OUTPUT_CLUSTERS: [GreenPowerProxy.cluster_id],
            },
        }
    }
