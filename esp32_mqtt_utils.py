# esp32_mqtt_utils.py：仅保留MQTT连接测试核心
import paho.mqtt.client as mqtt
import ssl
import time
from kivy.clock import Clock

class Esp32MqttClient:
    def __init__(self, broker, port, username, password, data_callback=None, max_reconnect_attempts=5):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.data_callback = data_callback  # 日志回调
        
        self.mqtt_client = None
        self.connected = False
        self.reconnect_count = 0
        self.max_reconnect_attempts = max_reconnect_attempts

    def init_mqtt_client(self):
        """初始化MQTT客户端（仅保留基础TLS）"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.username_pw_set(self.username, self.password)
            
            # 简化TLS配置（测试用）
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.mqtt_client.tls_set_context(context)
            
            # 绑定核心回调
            self.mqtt_client.on_connect = self._on_connect
            self.mqtt_client.on_disconnect = self._on_disconnect
            
            self._log_msg(f"✅ MQTT客户端初始化完成")
            return True
        except Exception as e:
            self._log_msg(f"❌ 客户端初始化失败：{str(e)}")
            self.mqtt_client = None
            return False

    def start_mqtt(self):
        """启动连接（测试核心）"""
        if self.mqtt_client is None:
            if not self.init_mqtt_client():
                return
        
        try:
            self.mqtt_client.connect(self.broker, self.port)
            self.mqtt_client.loop_start()
            self._log_msg(f"🔄 发起MQTT连接请求...")
        except Exception as e:
            self._log_msg(f"❌ 连接发起失败：{str(e)}")
            self._reconnect()

    def stop_mqtt(self):
        """手动断开（测试用）"""
        try:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                self.connected = False
                self._log_msg(f"ℹ️ MQTT已手动断开")
        except Exception as e:
            self._log_msg(f"❌ 断开失败：{str(e)}")

    def _on_connect(self, client, userdata, flags, rc):
        """连接结果回调（核心测试点）"""
        rc_msg = {
            0: "连接成功",
            1: "协议版本错误",
            2: "无效客户端ID",
            3: "服务器不可用",
            4: "用户名/密码错误",
            5: "未授权访问",
            6: "未知错误"
        }
        if rc == 0:
            self.connected = True
            self.reconnect_count = 0
            self._log_msg(f"✅ MQTT连接成功：{rc_msg[rc]}")
            # 测试订阅（可选）
            self.mqtt_client.subscribe("esp32/test")
        else:
            self.connected = False
            self._log_msg(f"❌ 连接失败[码{rc}]：{rc_msg.get(rc, '未知错误')}")
            self._reconnect()

    def _on_disconnect(self, client, userdata, rc):
        """断开回调"""
        self.connected = False
        if rc != 0:
            self._log_msg(f"⚠️ MQTT意外断开[码{rc}]，准备重连...")
            self._reconnect()
        else:
            self._log_msg(f"ℹ️ MQTT正常断开")

    def _reconnect(self):
        """自动重连（测试用）"""
        if self.reconnect_count < self.max_reconnect_attempts:
            self.reconnect_count += 1
            self._log_msg(f"🔄 第{self.reconnect_count}次重连（5秒后）")
            Clock.schedule_once(lambda dt: self.start_mqtt(), 5)
        else:
            self._log_msg(f"❌ 达到最大重连次数，停止尝试")

    def _log_msg(self, msg):
        """统一日志（带时间戳）"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        log_msg = f"[{timestamp}] {msg}"
        print(log_msg)
        if self.data_callback:
            Clock.schedule_once(lambda dt: self.data_callback(log_msg), 0)