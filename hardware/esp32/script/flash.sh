#!/bin/sh


# /dev/xxx 下的设备文件
device_id=/dev/cu.usbmodem1101

# mpy工具路径，工具地址：https://github.com/micropython/micropython/tree/master/mpy-cross
mpy_cross_bin=/Users/manson/ai/mcu/micropython/mpy-cross/build/mpy-cross

# mpy工具编译后的文件夹
build_dir=/Users/manson/ai/app/physical_agent/mcp4hal/hardware/esp32/script/build

# 项目源代码路径前缀
source_code_dir=/Users/manson/ai/app/physical_agent

mkdir -p $build_dir

# 创建设备上/lib目录
mpremote connect $device_id mkdir /lib

# mpy编译文件
$mpy_cross_bin -march=xtensawin -o $build_dir/wifi_utils.mpy $source_code_dir/mcp4hal/hardware/base/micropython/mcp4hal_mqtt/wifi_utils.py
$mpy_cross_bin -march=xtensawin -o $build_dir/mqtt_client.mpy $source_code_dir/mcp4hal/hardware/base/micropython/mcp4hal_mqtt/mqtt_client.py
$mpy_cross_bin -march=xtensawin -o $build_dir/protocol.mpy $source_code_dir/mcp4hal/hardware/base/micropython/mcp4hal_mqtt/protocol.py

# 拷贝文件和主脚本
mpremote connect $device_id cp $build_dir/wifi_utils.mpy :/lib/wifi_utils.mpy
mpremote connect $device_id cp $build_dir/mqtt_client.mpy :/lib/mqtt_client.mpy
mpremote connect $device_id cp $build_dir/protocol.mpy :/lib/protocol.mpy
mpremote connect $device_id cp $source_code_dir/mcp4hal/hardware/base/micropython/mcp4hal_mqtt/main.py :/main.py
