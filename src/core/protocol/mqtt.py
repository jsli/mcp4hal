from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional, Literal, List, Dict

from mcp import types
from pydantic import BaseModel

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


MCP4HAL_MQTT_QOS = 1
'''mqtt qos, 送达1次，消息不会丢失，也不会重复'''


MCP_WEB_PORT_START = 13307
'''mcp web server端口的起始点'''


class McpMqttToolPayload(BaseModel):
    name: str

    description: str

    parameters: list[dict[str, Any]]

    is_sync: bool = False
    '''是否同步，异步不需要等待返回'''


class McpMqttRegisterPayload(BaseModel):
    uid: str
    '''client id'''

    name: str

    description: str

    tools: list[McpMqttToolPayload]


class McpMqttUnRegisterPayload(BaseModel):
    uid: str
    '''client id'''


McpMqttLastWillPayload = McpMqttUnRegisterPayload
"""遗嘱消息"""


class McpMqttToolCallPayload(BaseModel):
    name: str
    """The name of the tool to be called."""

    args: dict[str, Any]
    """The arguments to the tool call."""

    id: Optional[str]
    """An identifier associated with the tool call."""


class McpMqttToolCallResultPayload(BaseModel):
    status: Literal["success", "error"] = "success"

    content: Any

    tool_call_id: str


class MqttTopicEnum(StrEnum):
    REGISTER = 'register'
    UNREGISTER = 'unregister'
    TOOLCALL = 'tc'
    TOOLCALL_RESULT = 'tcr'


@dataclass
class MqttMcpTool:
    name: str

    description: str

    parameters: List[Dict[str, Any]] = field(default_factory=list)

    is_sync: bool = True
    '''是否同步，异步不需要等待返回'''


@dataclass
class MqttMcpServer:
    uid: str

    name: str

    description: str

    tools: list[MqttMcpTool]


@dataclass
class MqttMcpServerMountConfig:
    schema: str = 'http'

    host: str = '0.0.0.0'

    port: int = 8000

    mount_path: str = '/mcp'

    transport = 'streamable-http'


@dataclass
class MqttBrokerConnectionConfig:
    """mqtt broker连接配置"""

    broker: str

    port: int

    client_id: str

    username: str

    passwd: str

    qos: int


def convert_to_mcp_typed_tools(tools: list[MqttMcpTool]):
    mcp_typed_tools = []
    for tool in tools:
        mcp_typed_tools.append(
            types.Tool(
                name=tool.name,
                description=tool.description,
                inputSchema={
                    "type": "object",
                    "properties": {
                        param["name"]: {
                            "type": param["type"],
                            "description": param["description"],
                            **({"enum": param["enum"]} if "enum" in param else {})
                        }
                        for param in tool.parameters
                    },
                    "required": [
                        param["name"]
                        for param in tool.parameters
                        if param.get("required", False)
                    ]
                }
            )
        )


def parse_mqtt_topic(topic):
    """
    根据预定义的协议，解析topic得出3层结构: MQTT_TOPIC_PREFIX/{client_id}/{MqttTopicEnum}
    """
    topic_parts = topic.split('/')

    # 合法性验证
    if len(topic_parts) != 3:
        return None, None
    if topic_parts[0] != MQTT_TOPIC_PREFIX:
        return None, None
    types = [_type.value for _type in MqttTopicEnum]
    if topic_parts[2] not in types:
        return None, None

    return topic_parts[1], topic_parts[2]
