#!/bin/sh

mpremote connect /dev/cu.usbmodem1101 mkdir /lib

/Users/manson/ai/mcu/micropython/mpy-cross/build/mpy-cross -march=xtensawin -o /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/esp32/script/build/wifi_utils.mpy /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/base/micropython/mcp4hal_mqtt/wifi_utils.py
/Users/manson/ai/mcu/micropython/mpy-cross/build/mpy-cross -march=xtensawin -o /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/esp32/script/build/mqtt_client.mpy /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/base/micropython/mcp4hal_mqtt/mqtt_client.py
/Users/manson/ai/mcu/micropython/mpy-cross/build/mpy-cross -march=xtensawin -o /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/esp32/script/build/protocol.mpy /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/base/micropython/mcp4hal_mqtt/protocol.py

mpremote connect /dev/cu.usbmodem1101 cp /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/esp32/script/build/wifi_utils.mpy :/lib/wifi_utils.mpy
mpremote connect /dev/cu.usbmodem1101 cp /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/esp32/script/build/mqtt_client.mpy :/lib/mqtt_client.mpy
mpremote connect /dev/cu.usbmodem1101 cp /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/esp32/script/build/protocol.mpy :/lib/protocol.mpy
mpremote connect /dev/cu.usbmodem1101 cp /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/base/micropython/mcp4hal_mqtt/main.py :/main.py
