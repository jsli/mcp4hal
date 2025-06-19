import logging

from core.protocol.mqtt import McpMqttLastWillPayload, MCP4HAL_MQTT_TOPIC_REGISTER_F, MCP4HAL_MQTT_TOPIC_WILL_F, \
    McpMqttRegisterPayload, McpMqttToolPayload, McpMqttToolCallResultPayload, MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F, \
    MCP4HAL_MQTT_TOPIC_TOOLCALL_F
from hal.mqtt.mqtt_client import MqttClient

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

register_payload = McpMqttRegisterPayload(
    uid=client_id,
    name='计算器',
    description='计算器',
    tools=[
        McpMqttToolPayload(
            name='add',
            description='计算两个数的和',
            is_async=True,
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
        McpMqttToolPayload(
            name='sub',
            description='计算两个数的差',
            is_async=False,
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
    ]
)


def on_tool_call(topic: str, message: dict, client):
    logger.debug('=============on_tool_call=============')
    if topic == tool_call_topic:
        logger.debug(topic)
        name = message['name']
        tool_call_id = message['id']
        args = message['args']
        if name == 'add':
            res = int(args['a']) + int(args['b'])
            tool_call_result = McpMqttToolCallResultPayload(tool_call_id=tool_call_id, content=res)
            mqtt_client.publish(tool_call_result_topic, tool_call_result)
        elif name == 'sub':
            res = int(args['a']) - int(args['b'])
            tool_call_result = McpMqttToolCallResultPayload(tool_call_id=tool_call_id, content=res)
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
mqtt_client.connect()
mqtt_client.set_message_callback(on_message_callback=on_tool_call)

mqtt_client.publish(register_topic, register_payload)

mqtt_client.loop(daemon=True)
