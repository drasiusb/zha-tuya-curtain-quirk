# ZHA quirk: Tuya TS0601 `_TZE204_guvc7pdy` curtain motor

Custom [ZHA](https://www.home-assistant.io/integrations/zha/) quirk for the Tuya
TS0601 curtain motor (`_TZE204_guvc7pdy`) in Home Assistant. ZHA has no built-in
support for this model.

## Device

[MOES ZigBee Smart Electric Motorized Splicing Curtain Tracks System](https://moeshouse.com/products/zigbee-electric-curtain-system)
(SKU `CM-PJ-T220-Z`): a Tuya curtain motor with a DIY splicing track and RF
remote. It pairs with ZHA as `_TZE204_guvc7pdy` / `TS0601`.

Assembly videos: [Google Drive](https://drive.google.com/drive/folders/1PjpF5Hz614iVJwVktwSWr9fHJbxDgWbf?usp=sharing)

## Pairing

Put the motor into pairing mode by pressing its button **3 times, about
1 second apart**. Pressing faster or slower doesn't work. Start pairing in ZHA
(**Add device**) first, then press the button.

## Install

1. Copy `Moes_ZigBee_SplitCurtain.py` to `/config/custom_zha_quirks/`.
2. Enable custom quirks in `configuration.yaml`:

   ```yaml
   zha:
     enable_quirks: true
     custom_quirks_path: /config/custom_zha_quirks/
   ```

3. Restart Home Assistant. After the restart, move each curtain once so HA picks
   up its real position.

## Datapoints

| DP | Meaning | Mapped to |
|----|---------|-----------|
| 1 | Control: 0 open, 1 stop, 2 close | `curtain_switch` |
| 2 | Set position (%) | `current_position_lift_percentage` |
| 3 | Reported position (%) | `current_position_lift_percentage` |

## Notes

- **Reversed motors.** Both motors this quirk was tuned on run reversed:
  the Tuya "close" command opens the curtain. `TUYA2ZB_COMMANDS` therefore maps
  HA's Open to Tuya CLOSE and HA's Close to Tuya OPEN. With that, Tuya's position
  already matches HA's convention (100 % = open), so no position conversion is
  needed. If your motor runs the standard way, swap those two lines back.
- **HA 2026.11 compatibility.** Commands pass `manufacturer=None`. The old value
  `manufacturer=-1` is rejected by newer zigpy versions, so no command reaches
  the motor.
