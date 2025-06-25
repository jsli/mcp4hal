from mcp4hal.core.protocol import MCP4HAL_MQTT_TOPIC_REGISTER, \
    MCP4HAL_MQTT_TOPIC_UNREGISTER, MqttMcpTool, MqttMcpServer, \
    MqttBrokerConnectionConfig, parse_mqtt_topic, MqttTopicEnum, MqttMcpServerMountConfig, \
    MQTT_TOPIC_PREFIX
from mcp4hal.hal.mqtt.mqtt_client import MqttClient
from mcp4hal.utils.logger import get_logger
from .mcp_server_proxy_mqtt_worker import McpServerProxyMqttWorker


logger = get_logger(__name__)


class McpServerProxyMqttSupervisor:
    _connection_config: MqttBrokerConnectionConfig | None = None

    _mqtt_client: MqttClient

    _worker_map: dict[str: McpServerProxyMqttWorker]
    '''维护一个worker的map'''

    _remote_server: dict[str: MqttMcpServer]
    '''维护一个已连接的map'''

    _current_port = 13307
    '''mcp web server端口的起始点'''

    _mount_host: str
    '''mcp server挂载的host'''

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
                host=self._mount_host,
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
         mount_host: str = '127.0.0.1',
         port_start: int = 13307
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
        self._mount_host = mount_host
        self._current_port = port_start

        self._mqtt_client.connect()

    def start(self, daemon: bool = True):
        if self._mqtt_client:
            # 管理所有请求
            self._mqtt_client.loop(daemon=daemon)

    def get_mcp_servers(self):
        mcp_servers = []
        for worker in self._worker_map.values():
            mount_config = worker.get_mount_config()
            mcp_server = {
                'url': f'{mount_config.schema}://{mount_config.host}:{mount_config.port}{mount_config.mount_path}',
                'host': mount_config.host,
                'port': mount_config.port,
                'mount_path': mount_config.mount_path,
                'transport': mount_config.transport,
                'is_available': worker.is_available(),
            }
            mcp_servers.append(mcp_server)
        return mcp_servers
