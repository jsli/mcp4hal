import json
import threading
import uuid
from typing import Any, Dict, List

import mcp.types as types
from fastmcp import FastMCP

from mcp4hal.core.protocol import parse_mqtt_topic, MqttTopicEnum, \
    MqttMcpTool, MqttMcpServer, MCP4HAL_MQTT_TOPIC_TOOLCALL_F, McpMqttToolCallPayload, \
    MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F, MqttBrokerConnectionConfig, MqttMcpServerMountConfig
from mcp4hal.hal.mqtt.mqtt_client import MqttClient
from mcp4hal.utils.logger import get_logger

logger = get_logger(__name__)


class McpServerProxyMqttWorker:
    _connection_config: MqttBrokerConnectionConfig | None = None

    _mqtt_client: MqttClient

    _remote_server: MqttMcpServer

    _mount_config: MqttMcpServerMountConfig

    _remote_tools_map: dict[str: MqttMcpTool]

    _tool_call_topic: str
    '''发送toolcall的mqtt topic'''

    _tool_call_result_topic: str
    '''获取toolcall result的mqtt topic'''

    _mcp_typed_tools: list[types.Tool]
    '''converted tools from remote_tools'''
    _remote_tools_map: dict[str: types.Tool]

    _remote_available: bool = False
    '''mcp remote是否可用标记'''

    _mount_server: FastMCP

    _tool_call_response_event: threading.Event
    '''通过mqtt进行toolcall的同步事件'''

    _tool_call_response_cache: dict[str, Any]

    _thread: threading.Thread

    _mount_path: str

    @classmethod
    def create_worker(
        cls,
        connection_config: MqttBrokerConnectionConfig,
        remote_server: MqttMcpServer,
        mount_config: MqttMcpServerMountConfig,
    ):
        return cls(connection_config=connection_config, remote_server=remote_server, mount_config=mount_config)

    def __init__(self,
        connection_config: MqttBrokerConnectionConfig,
        remote_server: MqttMcpServer,
        mount_config: MqttMcpServerMountConfig,
    ):
        # remote 相关
        self._connection_config = connection_config
        self._remote_server = remote_server
        self._mount_config = mount_config
        self._mcp_typed_tools = []
        self._remote_tools_map = {}
        self._sync_remote_server(remote_server)

        # 线程相关
        self._thread = None
        self._mount_server = None

        # mqtt相关
        self._mqtt_client = MqttClient(
            broker=connection_config.broker,
            port=connection_config.port,
            client_id=f'{connection_config.client_id}-{mount_config.port}',
            username=connection_config.username,
            passwd=connection_config.passwd,
            qos=connection_config.qos,
            sub_topic=[
                MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F % remote_server.uid
            ],
            on_message_callback=self._on_message
        )
        self._mqtt_client.connect()
        self._mqtt_client.loop(daemon=False)

        # toolcall同步相关
        self._tool_call_topic = MCP4HAL_MQTT_TOPIC_TOOLCALL_F % remote_server.uid
        self._tool_call_response_event = threading.Event()
        self._tool_call_response_cache = {}

        # mount相关
        self._init_mount_server()

    def _on_tool_call_result(self, topic, payload, client):
        tool_call_id = payload['tool_call_id']
        if tool_call_id in self._tool_call_response_cache:
            logger.debug(f'Got tool_call_result: {payload}')
            self._tool_call_response_cache[tool_call_id] = payload
            # 解除阻塞，通知结果
            self._tool_call_response_event.set()
        else:
            logger.debug(f'No need tool_call_result: {payload}')

    def _on_message(self, topic, payload, client):
        client_id, topic_type = parse_mqtt_topic(topic=topic)
        logger.debug(f'Got message: {client_id} - {topic_type}: {payload}')
        if topic_type == MqttTopicEnum.TOOLCALL_RESULT:
            self._on_tool_call_result(topic, payload, client)

    def _clean_remote_server(self):
        # 设置remote已不可用
        self._remote_available = False
        self.remote_server = None
        self._mcp_typed_tools = []
        self._remote_tools_map = {}

    def _sync_remote_server(self, remote_server):
        self._remote_available = True
        self._remote_server = remote_server

        self._mcp_typed_tools = []
        self._remote_tools_map = {}
        for tool in self._remote_server.tools:
            self._remote_tools_map[tool.name] = tool
            self._mcp_typed_tools.append(
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

    def _init_mount_server(self):
        """初始化mcp server，只在__init__中调用1次"""
        if self._mount_server is not None:
            logger.warning(f'_mount_server is already running!!!')

        self._mount_server = FastMCP()

        async def list_tools():
            if self._remote_available and self._mcp_typed_tools:
                return self._mcp_typed_tools
            else:
                return []

        async def handle_call_tool(name: str, arguments: Dict[str, Any] | None) -> List[
            types.TextContent | types.ImageContent]:
            """Handle tool execution requests."""
            try:
                if self._remote_available is False:
                    raise Exception('Not inited! Empty tools!')

                tool_call_id = str(uuid.uuid4())
                tool_call_response_topic = f'{MCP4HAL_MQTT_TOPIC_TOOLCALL_RESULT_F % self._remote_server.uid}/{tool_call_id}'

                tool = self._remote_tools_map[name]
                is_sync = True if tool is None else tool.is_sync

                # 订阅临时主题
                if is_sync:
                    self._mqtt_client.subscribe(tool_call_response_topic)
                    # 使用self.tool_call_response_cache来标记是个未执行完的任务
                    self._tool_call_response_cache[tool_call_id] = True

                # 发布tool call
                logger.info(f"Tool call received - Name: {name}, Arguments: {arguments} -> {self._tool_call_topic}")
                tool_call_payload = McpMqttToolCallPayload(id=tool_call_id, name=name, args=arguments)
                self._mqtt_client.publish(self._tool_call_topic, tool_call_payload)

                # 阻塞等待响应或超时
                if is_sync:
                    self._tool_call_response_event.clear()
                    logger.debug('waiting for response........')
                    if not self._tool_call_response_event.wait(timeout=60):
                        raise TimeoutError("No response received within timeout")

                    # 清理临时订阅
                    self._mqtt_client.unsubscribe(tool_call_response_topic)
                    logger.debug('unsubscribe for response topic %s' % tool_call_response_topic)

                    # 获取结果
                    response_data = self._tool_call_response_cache[tool_call_id]
                    if isinstance(response_data, dict):
                        response_data = json.dumps(response_data)
                    logger.debug('got response: %s' % response_data)

                    # 清理缓存结果
                    self._tool_call_response_cache.pop(tool_call_id)

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

        self._mount_server._mcp_server.list_tools()(list_tools)
        self._mount_server._mcp_server.call_tool()(handle_call_tool)

    def _run(self):
        if self._mount_server:
            self._mount_server.run(
                transport=self._mount_config.transport,
                host=self._mount_config.host,
                port=self._mount_config.port,
                path=self._mount_config.mount_path,
                # uvicorn_config={'workers': 8}
            )

    def start(self):
        """开启线程，监听mcp请求，并且执行mqtt转发"""
        logger.debug(f'1worker started! {self._remote_server}')
        if self._thread is not None:
            logger.warning(f'McpServerProxyMqttWorker is already running: {self._remote_server}')
            return

        self._thread = threading.Thread(target=self._run, name=f"{self.__class__.__name__}-{self._remote_server.name}")
        self._thread.start()
        logger.debug(f'2worker started! {self._remote_server}')

    def restart(self, remote_server: MqttMcpServer):
        """当remote重新可用时，调用"""
        logger.debug(f'1worker restarted! {self._remote_server}')
        if self._remote_available is True:
            logger.warning(f'McpServerProxyMqttWorker is already available: {self._remote_server}')
            return

        # 设置remote可用
        self._sync_remote_server(remote_server)
        logger.debug(f'2worker restarted! {self._remote_server}')

    def stop(self):
        """当remote不可用时，调用"""
        logger.debug(f'1worker stopped! {self._remote_server}')
        if self._thread is None:
            logger.warning(f'McpServerProxyMqttWorker is not running: {self._remote_server}')
            return

        # 设置remote已不可用
        self._clean_remote_server()
        logger.debug(f'2worker stopped! {self._remote_server}')

    def get_mount_config(self):
        return self._mount_config

    def is_available(self):
        return self._remote_available
