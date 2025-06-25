# mcp4hal



## Getting started
本项目实现了基于mqtt broker进行mcp协议转换，可以将mqtt client变成一个可以被llm agent调用的mcp server/tools。


## 架构图

## 如何使用
### sdk&源码
- sdk地址: [mcp4hal](https://pypi.org/project/mcp4hal/)
- 源码地址: [mcp4hal](https://github.com/jsli/mcp4hal)

### example运行
- 搭建一个mqtt broker，可以选择使用[mosquitto](https://github.com/eclipse-mosquitto/mosquitto)
- 选择一个mcu，比如esp32S3，也可以软件模拟（可以参考`mcp4hal/tests/mqtt/mock_mqtt_mcu.py`）。
- 启动参考项目

	```
	# server
	> cd $source_code_dir
	> mv .env.example .evn  # 编辑.env文件，正确配置相关参数
	> ./startup.sh  # 启动服务

	# client
	> # 连接好esp32设备
	> cd $source_code_dir/hardware/base/micropython/mcp4hal_mqtt
	> # 修改main.py文件头部的相关配置，包括wifi和mqtt配置
	> cd $source_code_dir/hardware/esp32/script
	> # 编辑flash.sh文件，配置好相关变量
	> ./flash.sh  # 将client代码刷到esp32上
	> # 重新启动esp32板子，可以看到日志输出，wifi连接以及mqtt连接
	```
- 调用测试：使用[mcp inspector](https://github.com/modelcontextprotocol/inspector)进行mcp调用测试