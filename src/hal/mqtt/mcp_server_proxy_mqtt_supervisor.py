from core.protocol.mqtt import MCP4HAL_MQTT_TOPIC_REGISTER, \
    MCP4HAL_MQTT_TOPIC_UNREGISTER, MqttMcpTool, MqttMcpServer, \
    MqttBrokerConnectionConfig, parse_mqtt_topic, MqttTopicEnum, MCP_WEB_PORT_START, MqttMcpServerMountConfig, \
    MQTT_TOPIC_PREFIX
from hal.mqtt.mqtt_client import MqttClient
from utils.logger import get_logger
from .mcp_server_proxy_mqtt_worker import McpServerProxyMqttWorker


logger = get_logger(__name__)


class McpServerProxyMqttSupervisor:
    _connection_config: MqttBrokerConnectionConfig | None = None

    _mqtt_client: MqttClient

    _worker_map: dict[str: McpServerProxyMqttWorker]
    '''维护一个worker的map'''

    _remote_server: dict[str: MqttMcpServer]
    '''维护一个已连接的map'''

    _current_port = MCP_WEB_PORT_START

    def _on_register(self, topic, payload, client):
        # note: payload中的uid优先级更高
        client_id, topic_type = parse_mqtt_topic(topic=topic)
        if 'uid' in payload:
            remote_id = payload['uid']
        else:
            remote_id = client_id
        name = payload['name']
        description = payload['description']

        remote_tools = [MqttMcpTool(**tool) for tool in payload['tools']]
        remote_server = MqttMcpServer(
            uid=remote_id,
            name=name,
            description=description,
            tools=remote_tools,
        )
        self._remote_server[remote_id] = remote_server

        if remote_id in self._worker_map:
            worker = self._worker_map[remote_id]
            worker.restart(remote_server)
        else:
            self._current_port += 1
            mount_config = MqttMcpServerMountConfig(
                port=self._current_port,
                mount_path=f'/{MQTT_TOPIC_PREFIX}/{client_id}'
            )
            worker = McpServerProxyMqttWorker.create_worker(
                connection_config=self._connection_config,
                remote_server=remote_server,
                mount_config=mount_config
            )
            self._worker_map[remote_id] = worker
            worker.start()

    def _on_unregister(self, topic, payload, client):
        # note: payload中的uid优先级更高
        client_id, topic_type = parse_mqtt_topic(topic=topic)
        if 'uid' in payload:
            remote_id = payload['uid']
        else:
            remote_id = client_id

        if remote_id in self._worker_map:
            worker = self._worker_map[remote_id]
            worker.stop()

    def _on_message(self, topic, payload, client):
        client_id, topic_type = parse_mqtt_topic(topic=topic)
        logger.debug(f'Got message: {client_id} - {topic_type}: {payload}')

        if topic_type == MqttTopicEnum.REGISTER:
            self._on_register(topic, payload, client)
        elif topic_type == MqttTopicEnum.UNREGISTER:
            self._on_unregister(topic, payload, client)
        else:
            logger.warning(f'unknown message: {topic} - {payload}')

    def __init__(self,
         connection_config: MqttBrokerConnectionConfig,
    ):
        self._connection_config = connection_config
        self._mqtt_client = MqttClient(
            broker=connection_config.broker,
            port=connection_config.port,
            client_id=connection_config.client_id,
            username=connection_config.username,
            passwd=connection_config.passwd,
            qos=connection_config.qos,
            sub_topic=[
                MCP4HAL_MQTT_TOPIC_REGISTER, MCP4HAL_MQTT_TOPIC_UNREGISTER
            ],
            on_message_callback=self._on_message
        )
        self._worker_map = {}
        self._remote_server = {}

        self._mqtt_client.connect()

    def start(self, daemon: bool = True):
        if self._mqtt_client:
            # 管理所有请求
            self._mqtt_client.loop(daemon=daemon)
