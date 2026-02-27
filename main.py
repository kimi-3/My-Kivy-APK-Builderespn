# main.py：仅保留MQTT连接测试功能（修复初始化顺序错误）
from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', False)

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window

# 导入简化后的MQTT工具类
from esp32_mqtt_utils import Esp32MqttClient

# 全局日志存储
recv_data_list = []

# 适配dp单位
def dp(value):
    from kivy.metrics import dp as kivy_dp
    return kivy_dp(value)

# 构建测试UI
def create_test_ui(app_instance):
    main_layout = MDBoxLayout(
        orientation="vertical",
        padding=dp(20),
        spacing=dp(20),
        size_hint=(1, 1)
    )
    
    # 标题
    main_layout.add_widget(MDLabel(
        text="MQTT连接测试",
        font_size=dp(20),
        halign="center",
        size_hint_y=None,
        height=dp(60)
    ))
    
    # 连接/断开按钮
    btn_layout = MDBoxLayout(
        orientation="horizontal",
        spacing=dp(20),
        size_hint_y=None,
        height=dp(60)
    )
    # 连接按钮
    connect_btn = MDRaisedButton(text="启动连接", size_hint=(0.5, 1))
    connect_btn.bind(on_press=lambda x: app_instance.start_mqtt_test())
    btn_layout.add_widget(connect_btn)
    
    # 断开按钮
    disconnect_btn = MDRaisedButton(text="断开连接", size_hint=(0.5, 1))
    disconnect_btn.bind(on_press=lambda x: app_instance.stop_mqtt_test())
    btn_layout.add_widget(disconnect_btn)
    main_layout.add_widget(btn_layout)
    
    # 连接状态显示
    app_instance.status_label = MDLabel(
        text="当前状态：未初始化",
        font_size=dp(16),
        halign="center",
        theme_text_color="Custom",
        text_color=(0.8, 0, 0, 1),
        size_hint_y=None,
        height=dp(40)
    )
    main_layout.add_widget(app_instance.status_label)
    
    # 日志展示区域
    main_layout.add_widget(MDLabel(
        text="运行日志：",
        font_size=dp(16),
        size_hint_y=None,
        height=dp(30)
    ))
    log_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
    app_instance.log_label = MDLabel(
        text="",
        font_size=dp(14),
        size_hint_y=None,
        valign="top",
        halign="left"
    )
    app_instance.log_label.bind(texture_size=app_instance.log_label.setter('size'))
    log_scroll.add_widget(app_instance.log_label)
    main_layout.add_widget(log_scroll)
    
    return main_layout

# 主APP类（仅测试MQTT连接）
class Esp32MobileApp(MDApp):
    def __init__(self,** kwargs):
        super().__init__(**kwargs)
        # MQTT配置（替换为你的实际服务器信息）
        self.mqtt_config = {
            "broker": "iaa16ebf.ala.cn-hangzhou.emqxsl.cn",
            "port": 8883,
            "username": "esp32",
            "password": "123456"
        }
        self.mqtt_client = None
        self.status_label = None  # 先初始化为空
        self.log_label = None     # 先初始化为空

    def build(self):
        Window.orientation = 'portrait'
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        
        # 第一步：先创建UI（赋值log_label/status_label）
        ui_layout = create_test_ui(self)
        
        # 第二步：再初始化MQTT客户端（此时log_label已存在）
        self._init_mqtt_client()
        
        return ui_layout

    def _init_mqtt_client(self):
        """初始化MQTT客户端（此时UI已创建）"""
        self.mqtt_client = Esp32MqttClient(
            broker=self.mqtt_config["broker"],
            port=self.mqtt_config["port"],
            username=self.mqtt_config["username"],
            password=self.mqtt_config["password"],
            data_callback=self._update_log
        )
        self._update_log("✅ MQTT客户端已初始化，点击【启动连接】测试")
        self.status_label.text = "当前状态：客户端已初始化"
        self.status_label.text_color = (0, 0.6, 0, 1)

    def start_mqtt_test(self):
        """启动连接测试"""
        if self.mqtt_client:
            self.mqtt_client.start_mqtt()
            self.status_label.text = "当前状态：正在连接..."
            self.status_label.text_color = (0.8, 0.6, 0, 1)

    def stop_mqtt_test(self):
        """断开连接测试"""
        if self.mqtt_client:
            self.mqtt_client.stop_mqtt()
            self.status_label.text = "当前状态：已手动断开"
            self.status_label.text_color = (0.8, 0, 0, 1)

    def _update_log(self, content):
        """更新日志展示（增加空值保护）"""
        global recv_data_list
        recv_data_list.append(content)
        # 仅保留最新20条日志
        if len(recv_data_list) > 20:
            recv_data_list = recv_data_list[-20:]
        
        # 核心修复：先判断log_label是否存在，再赋值
        if self.log_label is not None:
            self.log_label.text = "\n".join(recv_data_list)
        
        # 更新连接状态（增加空值保护）
        if self.mqtt_client and self.mqtt_client.connected and self.status_label is not None:
            self.status_label.text = "当前状态：已连接"
            self.status_label.text_color = (0, 0.8, 0, 1)

if __name__ == "__main__":
    Esp32MobileApp().run()