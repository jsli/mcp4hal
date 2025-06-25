import json
import time

import machine
# from umqtt.simple import MQTTClient
from umqtt.robust import MQTTClient

from wifi_utils import connect_wifi


class MicropythonMqttClient:
    def __init__(
        self,
        mqtt_broker,
        mqtt_port,
        mqtt_username,
        mqtt_password,
        client_id = None,
        mqtt_qos = 1,
        callback = None,
        wifi_ssid = None,
        wifi_password = None,
        keepalive = 30,
    ):
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password

        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        self.mqtt_qos = mqtt_qos
        self.client_id = client_id if client_id else  f"{str(machine.unique_id())}"

        self.callback = callback
        self.connected = False

        self.client = MQTTClient(
            client_id=self.client_id,
            server=self.mqtt_broker,
            port=self.mqtt_port,
            user=self.mqtt_username,
            password=self.mqtt_password,
            keepalive=keepalive,
        )

    def on_message(self, topic, payload):
        print(f"收到消息: Topic={topic}, Message={payload}")
        if self.callback:
            self.callback(topic, payload)

    def connect(self):
        if not self.connected:
            if self.wifi_ssid:
                connect_wifi(self.wifi_ssid, self.wifi_password)

            print(f"连接MQTT服务器: {self.mqtt_broker}")
            self.client.set_callback(self.on_message)
            self.client.connect()
            self.connected = True
            print(f"已连接到MQTT服务器: {self.mqtt_broker}")

    def set_callback(self, callback):
        self.callback = callback

    def set_last_will(self, will_topic, will_payload):
        """设置遗嘱消息"""
        if not self.connected:
            '''在未链接时设置'''
            self.client.set_last_will(
                topic=will_topic.encode('utf-8'),
                msg=json.dumps(will_payload).encode('utf-8'),
                retain=True,
                qos=self.mqtt_qos
            )

    def subscribe(self, topic):
        if self.connected:
            self.client.subscribe(topic.encode('utf-8'))
            print(f"已订阅主题: {topic}")

    def publish(self, topic, payload):
        if self.connected:
            if isinstance(payload, dict):
                payload = json.dumps(payload).encode('utf-8')
            self.client.publish(topic.encode('utf-8'), payload)
            print(f"已发布: Topic={topic}, Message={payload}")

    def disconnect(self):
        self.client.disconnect()
        self.connected = False
        print(f"已断开MQTT连接: {self.mqtt_broker}")

    def fetch_messages(self, blocking=False):
        """检查消息"""
        if blocking:
            print('等待消息')
            res = self.client.wait_msg()  # 阻塞等待
            print(f'获取到消息: {res}')
        else:
            print('检查消息')
            res = self.client.check_msg()  # 非阻塞检查
            print(f'检查获取到消息: {res}')

    def run(self, blocking = False):
        print(f'running in blocking mode: [{blocking}]')
        while not self.connected:
            print('not connected. waiting')
            time.sleep(1)

        try:
            while True:
                self.fetch_messages(blocking)
        except KeyboardInterrupt:
            print("断开连接...")
        finally:
            self.disconnect()
