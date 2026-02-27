# main.py：主运行文件，程序入口，整合UI、MQTT和业务逻辑
from kivy.config import Config

# 全局变量：存储接收的数据（用于UI展示）
recv_data_list = []

# 配置手机端窗口（竖屏，适配手机分辨率）
Config.set('graphics', 'width', '360')   # 手机宽度
Config.set('graphics', 'height', '640')  # 手机高度
Config.set('graphics', 'resizable', False)  # 禁止缩放
Config.set('graphics', 'fullscreen', '0')   # 非全屏（测试用，发布可改1）

from kivymd.app import MDApp
from esp32_mqtt_utils import Esp32MqttClient
from app_ui_pages import create_app_ui
from kivy.clock import Clock


class Esp32MobileApp(MDApp):
    def __init__(self,** kwargs):
        super().__init__(**kwargs)
        # MQTT服务器配置（替换为你的服务器信息）
        self.mqtt_config = {
            "broker": "iaa16ebf.ala.cn-hangzhou.emqxsl.cn",
            "port": 8883,
            "username": "esp32",
            "password": "123456"
        }
        # 初始化属性
        self.mqtt_client = None
        self.page_container = None  # 页面容器
        self.current_page = None    # 当前页面

    def build(self):
        """程序构建入口：先创建UI，再延迟启动MQTT"""
        self.title = "水质监控APP"  # 手机端标题栏
        main_layout = create_app_ui(self)
        # 延迟初始化MQTT（确保UI加载完成）
        Clock.schedule_once(lambda dt: self._init_mqtt_client(), 0.5)
        return main_layout

    def _init_mqtt_client(self):
        """初始化MQTT客户端"""
        try:
            self.mqtt_client = Esp32MqttClient(
                broker=self.mqtt_config["broker"],
                port=self.mqtt_config["port"],
                username=self.mqtt_config["username"],
                password=self.mqtt_config["password"],
                data_callback=self._update_recv_data
            )
            self.mqtt_client.start_mqtt()
            print("✅ MQTT客户端初始化完成")  # 新增：标记初始化完成
        except Exception as e:
            self._update_recv_data(f"❌ MQTT初始化失败：{str(e)}")
            print(f"❌ MQTT初始化异常：{str(e)}")

    def _update_recv_data(self, content):
        """更新日志数据（线程安全）"""
        global recv_data_list
        recv_data_list.append(content)
        # 限制日志条数，避免内存溢出
        if len(recv_data_list) > 20:
            recv_data_list = recv_data_list[-20:]
        
        # 更新个人中心的日志显示
        if hasattr(self, 'current_page') and self.current_page:
            for child in self.current_page.walk():
                if hasattr(child, 'is_log_label') and child.is_log_label:
                    child.text = "\n".join(recv_data_list) + "\n"
                    # 自动滚动到最新日志
                    if child.parent and hasattr(child.parent, 'scroll_y'):
                        child.parent.scroll_y = 0

        # 更新个人中心连接状态
        if any(keyword in content for keyword in ["MQTT连接成功", "MQTT连接失败", "连接异常"]):
            self.update_me_page_status()

    def update_me_page_status(self):
        """更新个人中心的连接状态"""
        if not hasattr(self, 'current_page'):
            return
        # 检查是否在个人中心页面
        page_texts = [child.text for child in self.current_page.children if hasattr(child, 'text')]
        if "我的个人中心" in page_texts:
            from app_ui_pages import create_me_page
            self.page_container.clear_widgets()
            self.current_page = create_me_page(self)
            self.page_container.add_widget(self.current_page)
    def publish_command(self, topic, command):
        """发布指令到MQTT服务器"""
        # 新增：空值保护
        if not self.mqtt_client:
            self.data_callback("❌ MQTT客户端未创建，无法发送指令")
            return False
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
if __name__ == "__main__":
    """程序入口：启动APP主循环"""
    Esp32MobileApp().run()