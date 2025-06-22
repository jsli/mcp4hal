# 1. 如何编译mpy文件

```shell
git clone https://github.com/micropython/micropython.git
cd micropython/mpy-cross
make

./mpy-cross -march=xtensawin /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/base/micropython/mcp4hal_mqtt/wifi_utils.py

mpremote connect /dev/cu.usbmodem1101 cp /Users/manson/ai/app/physical_agent/mcp4hal/src/hardware/base/micropython/mcp4hal_mqtt/wifi.mpy :/lib/wifi.mpy
```


# 2. esp32上安装umqtt.simple
```shell
import mip
mip.install("umqtt.simple")
```
