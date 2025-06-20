import logging

from core.protocol.mqtt import MqttBrokerConnectionConfig
from hal.mqtt.mcp_server_proxy_mqtt_supervisor import McpServerProxyMqttSupervisor

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



# proxy_server = McpServerProxy4Mqtt(
#     broker=broker,
#     port=port,
#     client_id=client_id,
#     username=username,
#     passwd=passwd,
#     qos=qos
# )
# proxy_server.run()

connection_config = MqttBrokerConnectionConfig(
    client_id = 'mock_server',
    username = 'mqtt_dev',
    # passwd = '123456',
    passwd = 'abcd1234',
    # broker = '127.0.0.1',
    broker = '192.168.152.224',
    port = 1883,
    qos = 1,
)
supervisor = McpServerProxyMqttSupervisor(connection_config=connection_config)
supervisor.start()
