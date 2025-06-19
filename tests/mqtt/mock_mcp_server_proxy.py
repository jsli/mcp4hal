import logging

from hal.mqtt import McpServerProxy4Mqtt

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

client_id = 'mock_server'
username = 'mqtt_dev'
# passwd = '123456'
passwd = 'abcd1234'
# broker = '127.0.0.1'
broker = '192.168.152.224'
port = 1883
qos = 1

proxy_server = McpServerProxy4Mqtt(
    broker=broker,
    port=port,
    client_id=client_id,
    username=username,
    passwd=passwd,
    qos=qos
)
proxy_server.run()
