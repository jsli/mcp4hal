from core.protocol import McpMqttLastWillPayload, MCP4HAL_MQTT_TOPIC_REGISTER_F, MCP4HAL_MQTT_TOPIC_WILL_F, \
    McpMqttRegisterPayload, McpMqttToolPayload, McpMqttToolCallResultPayload, MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F, \
    MCP4HAL_MQTT_TOPIC_TOOLCALL_F
from hal.mqtt.mqtt_client import MqttClient
from utils.logger import get_logger

logger = get_logger(__name__)

client_id = 'mock_client'
port = 1883
qos = 1
username = 'mqtt_dev'
# passwd = '123456'
passwd = 'abcd1234'
# broker = '127.0.0.1'
broker = '192.168.152.224'

will_topic = MCP4HAL_MQTT_TOPIC_WILL_F % client_id
will_payload = McpMqttLastWillPayload(uid=client_id)

register_topic = MCP4HAL_MQTT_TOPIC_REGISTER_F % client_id
tool_call_topic = MCP4HAL_MQTT_TOPIC_TOOLCALL_F % client_id
tool_call_result_topic = MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F % client_id

tools = {
    'add': McpMqttToolPayload(
        name='add',
        description='计算两个数的和',
        is_sync=True,
        parameters=[
            {
                'name': 'a',
                'type': 'int',
                'required': True,
                'description': '一个整数',
            },
            {
                'name': 'b',
                'type': 'int',
                'required': True,
                'description': '一个整数',
            }
        ],
    ),
    'sub': McpMqttToolPayload(
        name='sub',
        description='计算两个数的差',
        is_sync=False,
        parameters=[
            {
                'name': 'a',
                'type': 'int',
                'required': True,
                'description': '一个整数',
            },
            {
                'name': 'b',
                'type': 'int',
                'required': True,
                'description': '一个整数',
            }
        ]
    )
}

register_payload = McpMqttRegisterPayload(
    uid=client_id,
    name='计算器',
    description='计算器',
    tools=tools.values()
)


def on_tool_call(topic: str, message: dict, client):
    logger.debug('=============on_tool_call=============')
    if topic == tool_call_topic:
        logger.debug(topic)
        name = message['name']
        tool_call_id = message['id']
        args = message['args']
        tool_call_result = ''
        if name == 'add':
            res = int(args['a']) + int(args['b'])
            tool_call_result = McpMqttToolCallResultPayload(tool_call_id=tool_call_id, content=res)
        elif name == 'sub':
            res = int(args['a']) - int(args['b'])
            tool_call_result = McpMqttToolCallResultPayload(tool_call_id=tool_call_id, content=res)

        # 是否返回结果
        _tool = tools.get(name)
        if _tool and _tool.is_sync:
            mqtt_client.publish(tool_call_result_topic, tool_call_result)

mqtt_client = MqttClient(
    broker=broker,
    port=port,
    sub_topic=tool_call_topic,
    client_id=client_id,
    username=username,
    passwd=passwd,
    will_topic=will_topic,
    will_topic_payload=will_payload,
    qos=qos
)

# 设置遗嘱消息
# mqtt_client.set_last_will(will_topic=will_topic, will_payload=will_payload)

mqtt_client.connect()
mqtt_client.set_message_callback(on_message_callback=on_tool_call)

mqtt_client.publish(register_topic, register_payload)

mqtt_client.loop(daemon=True)
