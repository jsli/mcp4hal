import json
import logging
import threading
import time
import uuid
from typing import Any, Dict, List

import mcp.types as types
from fastmcp import FastMCP

from core.protocol.mqtt import MCP4HAL_MQTT_TOPIC_REGISTER, \
    MCP4HAL_MQTT_TOPIC_UNREGISTER, MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT, parse_mqtt_topic, MqttTopicEnum, \
    MqttMcpTool, MqttMcpServer, MCP4HAL_MQTT_TOPIC_TOOLCALL_F, McpMqttToolCallPayload, \
    MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F
from hal.mqtt.mqtt_client import MqttClient

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class McpServerProxy4Mqtt:
    mqtt_client: MqttClient

    # got from register
    remote_id: str
    remote_server: MqttMcpServer
    remote_tools: list[MqttMcpTool]
    remote_tools_map: dict[str: MqttMcpTool]

    mcp_typed_tools: list[types.Tool]
    '''converted tools from remote_tools'''

    inited: bool = False
    '''mcp remote初始化标记'''

    mount_server: FastMCP

    tool_call_response_event: threading.Event
    '''通过mqtt进行toolcall的同步事件'''

    tool_call_response_cache: dict[str, Any]

    _thread: threading.Thread

    def _on_register(self, topic, payload, client):
        if self.inited is True:
            logger.warning('##### inited! ignore!')
            return

        # note: payload中的uid优先级更高
        client_id, topic_type = parse_mqtt_topic(topic=topic)
        if 'uid' in payload:
            self.remote_id = payload['uid']
        else:
            self.remote_id = client_id

        name = payload['name']
        description = payload['description']

        self.mount_server._mcp_server.name = name

        self.remote_tools = [MqttMcpTool(**tool) for tool in payload['tools']]
        self.remote_tools_map = {}
        self.remote_server = MqttMcpServer(
            uid=self.remote_id,
            name=name,
            description=description,
            tools=self.remote_tools,
        )

        self.mcp_typed_tools = []
        for tool in self.remote_tools:
            self.remote_tools_map[tool.name] = tool
            self.mcp_typed_tools.append(
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

        self.inited = True
        logger.debug(f'Inited! remote info: {self.remote_server}')

    def _on_unregister(self, topic, payload, client):
        if self.inited is False:
            logger.warning('Not inited! ignore!')

        # note: payload中的uid优先级更高
        client_id, topic_type = parse_mqtt_topic(topic=topic)
        if 'uid' in payload:
            remote_id = payload['uid']
        else:
            remote_id = client_id
        if remote_id != self.remote_id:
            logger.warning(f'remote_id not matched! ignore! {remote_id} - {self.remote_id}')

        # cleanup
        self.inited = False
        self.remote_id = None
        self.remote_server = None
        self.remote_tools = None
        self.mcp_typed_tools = None
        self.remote_tools_map = None
        self.mount_server._mcp_server.name = 'FastMCP'
        logger.debug(f'UnInited! remote info: {self.remote_server}')

    def _on_tool_call(self, topic, payload, client):
        pass

    def _on_tool_call_result(self, topic, payload, client):
        tool_call_id = payload['tool_call_id']
        if tool_call_id in self.tool_call_response_cache:
            logger.debug(f'Got tool_call_result: {payload}')
            self.tool_call_response_cache[tool_call_id] = payload
            # 解除阻塞，通知结果
            self.tool_call_response_event.set()
        else:
            logger.debug(f'No need tool_call_result: {payload}')

    def _on_message(self, topic, payload, client):
        client_id, topic_type = parse_mqtt_topic(topic=topic)
        logger.debug(f'Got message: {client_id} - {topic_type}: {payload}')

        if topic_type == MqttTopicEnum.REGISTER:
            self._on_register(topic, payload, client)
        elif topic_type == MqttTopicEnum.UNREGISTER:
            self._on_unregister(topic, payload, client)
        elif topic_type == MqttTopicEnum.TOOLCALL:
            self._on_tool_call(topic, payload, client)
        elif topic_type == MqttTopicEnum.TOOLCALL_RESULT:
            self._on_tool_call_result(topic, payload, client)

    def __init__(self,
         broker: str,
         port: int = 1883,
         client_id: str = "",
         username: str = "",
         passwd: str = "",
         qos: int = 1,
    ):
        self._thread = None

        self.tool_call_response_event = threading.Event()
        self.tool_call_response_cache = {}

        self.inited = False
        self.remote_id = None
        self.remote_server = None
        self.remote_tools = None
        self.mcp_typed_tools = None
        self.remote_tools_map = None

        register_topic = MCP4HAL_MQTT_TOPIC_REGISTER
        unregister_topic = MCP4HAL_MQTT_TOPIC_UNREGISTER
        tool_call_result_topic = MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT

        self.mqtt_client = MqttClient(
            broker=broker,
            port=port,
            sub_topic=[
                register_topic,
                unregister_topic,
                tool_call_result_topic
            ],
            client_id=client_id,
            username=username,
            passwd=passwd,
            qos=qos
        )
        self.mqtt_client.connect()
        self.mqtt_client.set_message_callback(on_message_callback=self._on_message)
        self.mqtt_client.loop(daemon=False)

        self.mount_server = FastMCP()
        async def list_tools():
            if self.inited and self.mcp_typed_tools:
                return self.mcp_typed_tools
            else:
                return []

        async def handle_call_tool(name: str, arguments: Dict[str, Any] | None) -> List[
            types.TextContent | types.ImageContent]:
            """Handle tool execution requests."""
            try:
                if self.inited is False:
                    raise Exception('Not inited! Empty tools!')

                tool_call_id = str(uuid.uuid4())
                tool_call_topic = MCP4HAL_MQTT_TOPIC_TOOLCALL_F % self.remote_id
                tool_call_response_topic = f'{MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F % self.remote_id}/{tool_call_id}'

                tool = self.remote_tools_map[name]
                is_async = True if tool is None else tool.is_sync

                # 订阅临时主题
                if is_async:
                    self.mqtt_client.subscribe(tool_call_response_topic)
                    # 使用self.tool_call_response_cache来标记是个未执行完的任务
                    self.tool_call_response_cache[tool_call_id] = True

                # 发布tool call
                logger.info(f"Tool call received - Name: {name}, Arguments: {arguments} -> {tool_call_topic}")
                tool_call_payload = McpMqttToolCallPayload(id=tool_call_id, name=name, args=arguments)
                self.mqtt_client.publish(tool_call_topic, tool_call_payload)

                # 阻塞等待响应或超时
                if is_async:
                    self.tool_call_response_event.clear()
                    logger.debug('waiting for response........')
                    if not self.tool_call_response_event.wait(timeout=60):
                        raise TimeoutError("No response received within timeout")

                    time.sleep(5)

                    # 清理临时订阅
                    self.mqtt_client.unsubscribe(tool_call_response_topic)
                    logger.debug('unsubscribe for response topic %s' % tool_call_response_topic)

                    # 获取结果
                    response_data = self.tool_call_response_cache[tool_call_id]
                    if isinstance(response_data, dict):
                        response_data = json.dumps(response_data)
                    logger.debug('got response: %s' % response_data)

                    # 清理缓存
                    self.tool_call_response_cache.pop(tool_call_id)

                    return [types.TextContent(
                        type="text",
                        text=response_data
                    )]

                else:
                    return [types.TextContent(
                        type="text",
                        text='tool call send: ok'
                    )]
            except Exception as e:
                logger.error(f"Error handling tool call: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]

        self.mount_server._mcp_server.list_tools()(list_tools)
        self.mount_server._mcp_server.call_tool()(handle_call_tool)

    def run(self, host: str = '127.0.0.1', port: int = 8000, mount_path: str = '/mcp', transport = 'streamable-http'):
        if self.mount_server:
            self.mount_server.run(transport=transport, host=host, port=port, path=mount_path, uvicorn_config={'workers': 8})

    def _thread_main(self) -> None:
        try:
            self.run()
        finally:
            self._thread = None

    def loop_start(self):
        """This is part of the threaded client interface. Call this once to
        start a new thread to process network traffic. This provides an
        alternative to repeatedly calling `loop()` yourself.

        Under the hood, this will call `loop_forever` in a thread, which means that
        the thread will terminate if you call `disconnect()`
        """
        if self._thread is not None:
            return MQTTErrorCode.MQTT_ERR_INVAL

        self._sockpairR, self._sockpairW = _socketpair_compat()
        self._thread_terminate = False
        self._thread = threading.Thread(target=self._thread_main, name=f"paho-mqtt-client-{self._client_id.decode()}")
        self._thread.daemon = True
        self._thread.start()

        return MQTTErrorCode.MQTT_ERR_SUCCESS
