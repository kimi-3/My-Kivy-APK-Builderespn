# esp32_mqtt_utils.py：MQTT工具类，封装连接和数据收发
import paho.mqtt.client as mqtt
from threading import Thread
import json
from kivy.clock import Clock

class Esp32MqttClient:
    def __init__(self, broker, port, username, password, data_callback):
        """
        初始化MQTT客户端
        :param broker: MQTT服务器地址
        :param port: 端口（8883为TLS加密端口）
        :param username: 认证用户名
        :param password: 认证密码
        :param data_callback: 数据接收回调（更新UI）
        """
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.data_callback = data_callback
        self.mqtt_client = None
        self.mqtt_thread = None
        self.connected = False
        self.parsed_data_callback = None  # 解析后的数据回调
        self.latest_data = {}  # 存储最新传感器数据

    def set_parsed_data_callback(self, callback):
        """设置解析后的数据回调（供UI层使用）"""
        self.parsed_data_callback = callback

    def init_mqtt_client(self):
        """初始化MQTT客户端配置"""
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(self.username, self.password)
        # 配置TLS加密（EMQX Serverless必须）
        self.mqtt_client.tls_set()
        # 绑定回调函数
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message

    def start_mqtt(self):
        """启动MQTT通信（独立线程）"""
        self.init_mqtt_client()
        self.mqtt_thread = Thread(target=self._mqtt_loop, daemon=True).start()

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            self.connected = True
            self.data_callback("✅ MQTT连接成功，已开始接收数据")
            # 订阅传感器数据主题
            client.subscribe("esp32/sensor")
            client.subscribe("esp32/threshold_response")
        else:
            self.connected = False
            self.data_callback(f"❌ MQTT连接失败（错误码：{rc}）")

    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            # 解析原始消息
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            self.data_callback(f"📥 [{topic}] {payload}")

            # 解析传感器数据（JSON格式）
            if topic == "esp32/sensor":
                parsed_data = json.loads(payload)
                self.latest_data = parsed_data
                # 转发解析后的数据到UI（主线程）
                if self.parsed_data_callback:
                    Clock.schedule_once(lambda dt: self.parsed_data_callback(parsed_data))

        except json.JSONDecodeError:
            self.data_callback(f"❌ 数据格式错误：{payload}")
        except Exception as e:
            self.data_callback(f"❌ 接收数据失败：{str(e)}")

    def _mqtt_loop(self):
        """MQTT循环（带自动重连）"""
        reconnect_interval = 5  # 重连间隔5秒
        max_reconnect_attempts = 10  # 最大重连次数
        reconnect_count = 0

        while reconnect_count < max_reconnect_attempts:
            try:
                self.mqtt_client.connect(self.broker, self.port, 60)
                self.connected = True
                self.mqtt_client.loop_forever()
                break
            except Exception as e:
                reconnect_count += 1
                self.connected = False
                error_msg = f"❌ 重连({reconnect_count}/{max_reconnect_attempts})：{str(e)}"
                self.data_callback(error_msg)
                if reconnect_count >= max_reconnect_attempts:
                    self.data_callback("❌ 达到最大重连次数，停止尝试")
                    break
                import time
                time.sleep(reconnect_interval)

    def publish_command(self, topic, command):
        """发布指令到MQTT服务器"""
        if not self.connected:
            self.data_callback("❌ MQTT未连接，无法发送指令")
            return False
        try:
            self.mqtt_client.publish(topic, command, qos=0)
            self.data_callback(f"📤 已发送：{command}")
            return True
        except Exception as e:
            self.data_callback(f"❌ 发送失败：{str(e)}")
            return False