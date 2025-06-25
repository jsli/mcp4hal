import json
from typing import Callable, Optional, Any

import paho.mqtt.client as mqtt
from pydantic import BaseModel

from mcp4hal.utils.logger import get_logger

logger = get_logger(__name__)


class MqttClient:
    client: Any

    def __init__(
        self,
        broker: str,
        sub_topic: str | list[str] = None,
        will_topic: str = "",
        will_topic_payload: Any = None,
        port: int = 1883,
        client_id: str = "",
        username: str = "",
        passwd: str = "",
        qos: int = 1,
        on_message_callback: Optional[Callable] = None,
    ):
        """
        初始化 MQTT 客户端
        :param broker: MQTT 服务器地址（如 "broker.hivemq.com"）
        :param port: 端口号（默认 1883）
        :param sub_topic: 订阅主题
        :param will_topic: 遗嘱主题
        :param will_topic_payload: 遗嘱主题payload
        :param client_id: 客户端 ID（若为空则自动生成）
        :param username: 用户名
        :param passwd: 密码
        :param qos: qos
        :param on_message_callback: 自定义消息处理函数（可选）
        """
        self.broker = broker
        self.sub_topic = sub_topic
        self.will_topic = will_topic
        self.will_topic_payload = will_topic_payload
        self.port = port
        self.qos = qos
        self.client_id = client_id or f"mcp4hal-mqtt-{id(self)}"
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        self.client.enable_logger(logger)
        if username and passwd:
            self.client.username_pw_set(username, passwd)

        self.on_message_callback = on_message_callback

        # 绑定回调函数
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # 设置遗嘱消息
        if self.will_topic:
            payload = self._convert_payload(self.will_topic_payload)
            self.client.will_set(topic=self.will_topic, payload=payload, qos=self.qos, retain=True)

    @property
    def ori_client(self):
        return self.client

    @classmethod
    def _convert_payload(cls, payload):
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        elif isinstance(payload, BaseModel):
            payload = payload.model_dump_json()
        return payload

    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties):
        logger.debug(f"===============Disconnected with disconnect_flags: {disconnect_flags}")
        logger.debug(f"===============Disconnected with code: {rc}")

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """连接成功回调"""
        logger.debug(f"Connected to MQTT Broker (client: {client})")
        logger.debug(f"Connected to MQTT Broker (userdata: {userdata})")
        logger.debug(f"Connected to MQTT Broker (flags: {flags})")
        logger.debug(f"Connected to MQTT Broker (reason_code: {reason_code})")
        logger.debug(f"Connected to MQTT Broker (properties: {properties})")

        if self.sub_topic:
            if isinstance(self.sub_topic, str):
                self.client.subscribe(topic=self.sub_topic, qos=self.qos)
                logger.debug(f"Subscribed to topic: {self.sub_topic}")
            elif isinstance(self.sub_topic, list):
                for topic in self.sub_topic:
                    self.client.subscribe(topic=topic, qos=self.qos)
                    logger.debug(f"Subscribed to topic: {topic}")

    def _on_message(self, client, userdata, msg):
        """收到消息回调"""
        try:
            payload = msg.payload.decode("utf-8")
            logger.debug(f"Received message on {msg.topic}: {payload}")

            # 尝试解析 JSON
            try:
                data = json.loads(payload)
                logger.debug(f"Parsed JSON: {data}")
            except json.JSONDecodeError:
                data = payload

            # 如果用户指定了自定义回调，则调用
            if self.on_message_callback:
                self.on_message_callback(msg.topic, data, client)

        except Exception as e:
            logger.debug(f"Error processing message: {e}")

    def connect(self, ):
        """连接 MQTT 服务器"""
        self.client.connect(host=self.broker, port=self.port, keepalive=30)

    def loop(self, daemon: bool=False):
        if daemon:
            self.client.loop_forever()  # 阻塞
        else:
            self.client.loop_start()  # 启动后台线程处理消息

    def disconnect(self):
        """断开连接"""
        self.client.loop_stop()
        self.client.disconnect()

    def publish(self, topic: str, payload: dict | str | BaseModel):
        """发布消息"""
        payload = self._convert_payload(payload)
        info = self.client.publish(topic, payload, qos=self.qos)
        logger.debug(f'========= publish {topic} -> {info}')

    def subscribe(self, topic: str):
        """订阅消息"""
        self.client.subscribe(topic=topic, qos=self.qos)

    def unsubscribe(self, topic: str):
        """取消订阅消息"""
        self.client.unsubscribe(topic)

    def set_message_callback(self, on_message_callback: Optional[Callable] = None):
        self.on_message_callback = on_message_callback


# 示例用法
if __name__ == "__main__":
    def custom_callback(topic: str, payload, client):
        logger.debug(f"[Custom Callback] Topic: {topic}, Payload: {payload}")

    # 初始化客户端
    mqtt_client = MqttClient(
        broker="localhost",  # 替换为你的 MQTT Broker
        username='mqtt_dev',
        passwd='123456',
        sub_topic='mcp4hal/mock_client/tc',
        client_id="my_device_123",
        on_message_callback=custom_callback,
    )

    # 连接并订阅
    mqtt_client.connect()
    mqtt_client.loop(daemon=True)

    try:
        # 模拟发布测试消息（实际使用时由其他客户端发布）
        mqtt_client.publish(f"/dev/{mqtt_client.client_id}", {"sensor": 25.5})
        while True:
            pass  # 保持运行
    except KeyboardInterrupt:
        mqtt_client.disconnect()
