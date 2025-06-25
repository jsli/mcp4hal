import json

import machine

from mqtt_client import MicropythonMqttClient
from protocol import MCP4HAL_MQTT_TOPIC_REGISTER_F, MCP4HAL_MQTT_TOPIC_WILL_F, MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F, \
    MCP4HAL_MQTT_TOPIC_TOOLCALL_F, MCP4HAL_MQTT_QOS

# WIFI配置部分
WIFI_SSID = "ZYYJY"
WIFI_PASS = "qwert123"

# MQTT配置部分
MQTT_USERNAME = 'mqtt_dev'
MQTT_PASSWD='abcd1234'
MQTT_BROKER='192.168.152.224'
MQTT_PORT = 1883
MQTT_QOS = MCP4HAL_MQTT_QOS

# ID配置
uid = machine.unique_id()
unique_id = ''.join(['{:02x}'.format(b) for b in uid])
CLIENT_ID = f"mcp4hal_{unique_id}"  # 唯一客户端ID

# mcp tool配置
tools = {
    'led': {
        'name': 'led',
        'description': '控制电灯的开关，如果打开，光会变量。如果关闭，光会变暗',
        'is_sync': False,
        'parameters': [
            {
                'name': 'status',
                'type': 'string',
                'required': True,
                'description': '控制开关的状态，如果是on则表示打开，如果是off，表示关闭',
            },
        ],
    }
}

# mcp server配置
server_config = {
    'name': 'MCU工具包',
    'description': 'MCU工具包',
    'tools': list(tools.values())
}

# mcp4hal协议部分
register_topic = MCP4HAL_MQTT_TOPIC_REGISTER_F % CLIENT_ID
register_payload = {
    'uid': CLIENT_ID,
}
register_payload.update(server_config)

will_topic = MCP4HAL_MQTT_TOPIC_WILL_F % CLIENT_ID
will_payload = {
    'uid': CLIENT_ID
}

tool_call_topic = MCP4HAL_MQTT_TOPIC_TOOLCALL_F % CLIENT_ID
tool_call_result_topic = MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F % CLIENT_ID


# ==========特定功能实现===========
# TODO: 扩展功能步骤
#   1. 实现功能函数
#   2. 在on_tool_call根据name，来选择对应的功能函数
#   3. 在tools字典中定义好描述
def led_switch(status):
    """实现led灯开关"""

    # 定义 LED 所连接的 GPIO 引脚
    LED_PIN = 1  # 例如，使用 GPIO2（D4）

    # 初始化 GPIO 引脚为输出模式
    led = machine.Pin(LED_PIN, machine.Pin.OUT)

    if status == 'on':
        led.value(0)
        return {
            'status': 'success',
            'content': 'on',
        }
    elif status == 'off':
        led.value(1)
        return {
            'status': 'success',
            'content': 'off',
        }
    else:
        return {
            'status': 'error',
            'content': status,
        }


def on_tool_call(name, tool_call_id, args):
    """处理tool call消息"""
    tool_call_result = {
        'status': 'error',
        'content': '',
    }
    if name == 'led':
        tool_call_result = led_switch(args['status'])

    # 是否返回结果
    _tool = tools.get(name)
    if _tool and _tool.get('is_sync', False):
        result = {
            'tool_call_id': tool_call_id,
        }
        result.update(tool_call_result)
        return result
    else:
        return None


# 主函数
def main():
    # 初始化MQTT客户端
    client = MicropythonMqttClient(
        mqtt_broker=MQTT_BROKER,
        mqtt_port=MQTT_PORT,
        mqtt_username=MQTT_USERNAME,
        mqtt_password=MQTT_PASSWD,
        client_id=CLIENT_ID,
        mqtt_qos=1,
        wifi_ssid=WIFI_SSID,
        wifi_password=WIFI_PASS,
        keepalive=30
    )

    # 消息回调函数
    def on_message(topic, msg):
        print(f"收到消息: Topic={topic.decode()}, Message={msg.decode()}")
        message = json.loads(msg)
        topic = topic.decode()
        if topic == tool_call_topic:
            tool_call_result = on_tool_call(message['name'], message['id'], message['args'])
            if tool_call_result:
                client.publish(tool_call_result_topic, tool_call_result)

    client.set_callback(on_message)

    # 设置遗嘱消息
    client.set_last_will(will_topic=will_topic, will_payload=will_payload)
    client.connect()
    print(f"已连接到MQTT服务器: {MQTT_BROKER}")

    # 监听toolcall
    client.subscribe(tool_call_topic)

    # 发送register
    client.publish(topic=register_topic, payload=register_payload)

    client.run(blocking=True)

main()
