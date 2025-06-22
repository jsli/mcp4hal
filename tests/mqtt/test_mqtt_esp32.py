import json
from mqtt_client import MicropythonMqttClient


MQTT_TOPIC_PREFIX = 'mcp4hal'


MCP4HAL_MQTT_TOPIC_REGISTER_F = f'{MQTT_TOPIC_PREFIX}/%s/register'
MCP4HAL_MQTT_TOPIC_REGISTER = f'{MQTT_TOPIC_PREFIX}/+/register'
'''mqtt client注册为mcp server的topic, client->hal'''


MCP4HAL_MQTT_TOPIC_UNREGISTER_F = f'{MQTT_TOPIC_PREFIX}/%s/unregister'
MCP4HAL_MQTT_TOPIC_UNREGISTER = f'{MQTT_TOPIC_PREFIX}/+/unregister'
'''mqtt client注销mcp server的topic, client->hal'''


MCP4HAL_MQTT_TOPIC_WILL_F = MCP4HAL_MQTT_TOPIC_UNREGISTER_F
MCP4HAL_MQTT_TOPIC_WILL = MCP4HAL_MQTT_TOPIC_UNREGISTER
'''mqtt client的遗嘱消息，注销'''


MCP4HAL_MQTT_TOPIC_TOOLCALL_F = f'{MQTT_TOPIC_PREFIX}/%s/tc'
MCP4HAL_MQTT_TOPIC_TOOLCALL = f'{MQTT_TOPIC_PREFIX}/+/tc'
'''mqtt client订阅接收tool call的topic, client<-hal'''


MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F = f'{MQTT_TOPIC_PREFIX}/%s/tcr'
MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT = f'{MQTT_TOPIC_PREFIX}/+/tcr'
'''mqtt client发布toolcall result topic, client->hal'''


# ===== 配置部分 =====
WIFI_SSID = "ZJJYJ"
WIFI_PASS = "qwert123"
MQTT_USERNAME='mqtt_dev'
MQTT_PASSWD='abcd1234'
MQTT_BROKER='192.168.152.224'
MQTT_PORT=1883
MQTT_QOS=1

unique_id = '1234'
CLIENT_ID = f"micropython_esp32_{unique_id}"  # 唯一客户端ID


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
    },
    # 'add': {
    #     'name': 'add',
    #     'description': '计算两个数的和',
    #     'is_sync': True,
    #     'parameters': [
    #         {
    #             'name': 'a',
    #             'type': 'int',
    #             'required': True,
    #             'description': '一个整数',
    #         },
    #         {
    #             'name': 'b',
    #             'type': 'int',
    #             'required': True,
    #             'description': '一个整数',
    #         }
    #     ],
    # },
    # 'sub': {
    #     'name': 'sub',
    #     'description': '计算两个数的差',
    #     'is_sync': True,
    #     'parameters': [
    #         {
    #             'name': 'a',
    #             'type': 'int',
    #             'required': True,
    #             'description': '一个整数',
    #         },
    #         {
    #             'name': 'b',
    #             'type': 'int',
    #             'required': True,
    #             'description': '一个整数',
    #         }
    #     ],
    # }
}

register_topic = MCP4HAL_MQTT_TOPIC_REGISTER_F % CLIENT_ID
register_payload = {
    'uid': CLIENT_ID,
    'name': 'MCU工具包',
    'description': 'MCU工具包',
    'tools': tools.values()
}

will_topic = MCP4HAL_MQTT_TOPIC_WILL_F % CLIENT_ID
will_payload = {
    'uid': CLIENT_ID
}

tool_call_topic = MCP4HAL_MQTT_TOPIC_TOOLCALL_F % CLIENT_ID
tool_call_result_topic = MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F % CLIENT_ID


# 消息回调函数
def on_message(topic, msg):
    print(f"收到消息: Topic={topic.decode()}, Message={msg.decode()}")


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
        callback=on_message,
        wifi_ssid=WIFI_SSID,
        wifi_password=WIFI_PASS,
    )

    # 设置遗嘱消息
    client.set_last_will(will_topic=will_topic, will_payload=will_payload)
    client.connect()
    print(f"已连接到MQTT服务器: {MQTT_BROKER}")

    # 监听toolcall
    client.subscribe(tool_call_topic)

    # 发送register
    client.publish(topic=register_topic, payload=register_payload)

    client.run(blocking=True)
