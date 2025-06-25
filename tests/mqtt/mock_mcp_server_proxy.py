import logging

from mcp4hal.core.protocol.mqtt_schema import MqttBrokerConnectionConfig
from mcp4hal.hal.mqtt.mcp_server_proxy_mqtt_supervisor import McpServerProxyMqttSupervisor

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


connection_config = MqttBrokerConnectionConfig(
    client_id = 'mock_server',
    username = 'mqtt_dev',
    # broker = '127.0.0.1',
    # passwd = '123456',
    broker = '192.168.152.224',
    passwd = 'abcd1234',
    port = 1883,
    qos = 1,
)
supervisor = McpServerProxyMqttSupervisor(connection_config=connection_config)
supervisor.start()
