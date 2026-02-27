import datetime
from kivy.config import Config
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivymd.uix.scrollview import MDScrollView
from ui_utils import NoBorderButton
import json
from kivymd.toast import toast

# 全局变量：存储历史数据
GLOBAL_HISTORY_DATA = []
HISTORY_UPDATE_CALLBACKS = []

def register_history_callback(callback):
    if callback not in HISTORY_UPDATE_CALLBACKS:
        HISTORY_UPDATE_CALLBACKS.append(callback)

def unregister_history_callback(callback):
    if callback in HISTORY_UPDATE_CALLBACKS:
        HISTORY_UPDATE_CALLBACKS.remove(callback)

def update_history_data(new_record):
    """统一更新历史数据，并触发UI刷新"""
    GLOBAL_HISTORY_DATA.insert(0, new_record)
    if len(GLOBAL_HISTORY_DATA) > 20:
        GLOBAL_HISTORY_DATA.pop()
    for cb in HISTORY_UPDATE_CALLBACKS:
        cb()

# 首页构建
def create_home_page(app_instance):
    home_layout = MDBoxLayout(
        orientation="vertical",
        padding=dp(20),
        spacing=dp(20),
        size_hint_y=None,
    )
    home_layout.bind(minimum_height=home_layout.setter('height'))
    
    # 注册MQTT回调（避免重复注册）
    def register_mqtt_callback(dt):
        if app_instance and hasattr(app_instance, 'mqtt_client') and app_instance.mqtt_client:
            app_instance.mqtt_client.set_parsed_data_callback(update_sensor_ui_and_record_history)
            print("✅ MQTT回调注册成功")
        else:
            # 延迟1秒重试（最多重试5次）
            if not hasattr(register_mqtt_callback, 'retry_count'):
                register_mqtt_callback.retry_count = 0
            register_mqtt_callback.retry_count += 1
            if register_mqtt_callback.retry_count <= 5:
                print(f"⚠️ MQTT客户端未初始化，{register_mqtt_callback.retry_count}秒后重试...")
                Clock.schedule_once(register_mqtt_callback, 1)
            else:
                print("❌ MQTT回调注册失败：达到最大重试次数")
    # 初始延迟1秒（给MQTT更多初始化时间）
    Clock.schedule_once(register_mqtt_callback, 1)

    # 顶部栏：溶解氧 + 手动开关
    top_bar = MDBoxLayout(
        orientation="horizontal",
        spacing=dp(20),
        size_hint_y=None,
        height=dp(30)
    )
    do_label = MDLabel(
        text="溶解氧: 7.25mg/L",
        font_size=dp(18),
        font_name="CustomChinese",
        halign="left",
        valign="middle",
        theme_text_color="Custom",
        text_color=(0, 0, 1, 1)
    )
    
    # PH值和温度标签
    ph_label = MDLabel(
        text="PH值: 7.0",
        font_size=dp(18),
        font_name="CustomChinese",
        theme_text_color="Custom",
        text_color=(0, 0, 1, 1)
    )
    temp_label = MDLabel(
        text="温度: 25.5℃",
        font_size=dp(18),
        font_name="CustomChinese",
        theme_text_color="Custom",
        text_color=(0, 0, 1, 1)
    )

    def update_sensor_ui_and_record_history(parsed_data):
        """更新UI标签 + 记录历史数据"""
        try:
            # 更新溶解氧/PH/温度UI
            if "do" in parsed_data and parsed_data["do"] is not None:
                do_value = round(float(parsed_data["do"]), 2)
                do_label.text = f"溶解氧: {do_value}mg/L"
            if "ph" in parsed_data and parsed_data["ph"] is not None:
                ph_value = round(float(parsed_data["ph"]), 1)
                ph_label.text = f"PH值: {ph_value}"
            if "temp" in parsed_data and parsed_data["temp"] is not None:
                temp_value = round(float(parsed_data["temp"]), 1)
                temp_label.text = f"温度: {temp_value}℃"

            # 记录历史数据
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            do_val = do_label.text.replace("溶解氧: ", "").replace("mg/L", "")
            ph_val = ph_label.text.replace("PH值: ", "")
            temp_val = temp_label.text.replace("温度: ", "").replace("℃", "")
            history_record = f"{current_time}: 溶解氧{do_val}mg/L | PH{ph_val} | 温度{temp_val}℃"
            
            update_history_data(history_record)

        except (ValueError, TypeError):
            do_label.text = "溶解氧: 数据异常mg/L"
            ph_label.text = "PH值: 数据异常"
            temp_label.text = "温度: 数据异常℃"

    # 手动开关
    switch_label = MDLabel(
        text="手动开关",
        font_size=dp(16),
        halign="right",
        valign="middle",
        font_name="CustomChinese",
        size_hint_x=None,
        width=dp(80)
    )
    switch_btn = NoBorderButton(
        text="关",
        button_type="switch",
        size_hint_x=None,
        width=dp(60),
        size_hint_y=None,
        height=dp(30)
    )
    switch_btn.app_instance = app_instance

    def toggle_switch(instance):
        # 切换开关状态
        instance.current_state = "开" if instance.current_state == "关" else "关"
        instance.text = instance.current_state
        instance.update_button_colors()
        
        # 发送数据到MQTT服务器
        send_data = "yes" if instance.current_state == "开" else "no"
        cmd_desc = "启动" if instance.current_state == "开" else "停止"
        
        try:
            if not hasattr(instance, 'app_instance') or not instance.app_instance:
                raise Exception("未获取到APP实例")
            
            mqtt_client = instance.app_instance.mqtt_client
            if not mqtt_client:
                raise Exception("MQTT客户端未初始化")
            
            send_result = mqtt_client.publish_command("esp32/switch", send_data)
            if send_result:
                toast(f"设备{cmd_desc}成功")
            else:
                raise Exception("MQTT未连接")
        
        except Exception as e:
            error_msg = f"❌ 开关操作失败：{str(e)}"
            print(error_msg)
            toast(error_msg)

    switch_btn.bind(on_press=toggle_switch)
    top_bar.add_widget(do_label)
    top_bar.add_widget(switch_label)
    top_bar.add_widget(switch_btn)
    home_layout.add_widget(top_bar)

    # 中间区域：阈值输入框 + 按钮列
    middle_layout = MDBoxLayout(
        orientation="horizontal",
        spacing=dp(20),
        size_hint_y=None,
        height=dp(100)
    )
    input_container = MDBoxLayout(
        orientation="vertical",
        spacing=dp(10),
        size_hint_x=1,
        size_hint_y=None,
        height=dp(120)
    )
    max_input = MDBoxLayout(
        orientation="horizontal",
        spacing=dp(10),
        size_hint_y=None,
        height=dp(40)
    )
    max_label = MDLabel(text="设置最高值:", font_size=dp(16), font_name="CustomChinese")
    max_textfield = MDTextField(hint_text="", size_hint_x=1)
    max_input.add_widget(max_label)
    max_input.add_widget(max_textfield)

    min_input = MDBoxLayout(
        orientation="horizontal",
        spacing=dp(10),
        size_hint_y=None,
        height=dp(40)
    )
    min_label = MDLabel(text="设置最低值:", font_size=dp(16), font_name="CustomChinese")
    min_textfield = MDTextField(hint_text="", size_hint_x=1)
    min_input.add_widget(min_label)
    min_input.add_widget(min_textfield)

    input_container.add_widget(max_input)
    input_container.add_widget(min_input)

    # 确认按钮
    button_container = MDBoxLayout(
        orientation="vertical",
        spacing=dp(10),
        size_hint_x=None,
        width=dp(90),
        size_hint_y=None,
        height=dp(120)
    )
    confirm_btn = NoBorderButton(
        text="确认",
        size_hint_x=None,
        width=dp(90),
        size_hint_y=None,
        height=dp(40)
    )
    def check_input_validity(*args):
        max_val = max_textfield.text.strip()
        min_val = min_textfield.text.strip()
        confirm_btn.is_disabled = (not max_val) or (not min_val)
        confirm_btn.update_button_colors()
    max_textfield.bind(text=check_input_validity)
    min_textfield.bind(text=check_input_validity)
    check_input_validity()

    # 确认按钮点击事件
    def on_confirm_click(instance):
        if instance.is_disabled:
            return
        
        instance.is_pressed = True
        instance.update_button_colors()
        
        max_val = max_textfield.text.strip()
        min_val = min_textfield.text.strip()
        
        # 校验输入是否为数字
        try:
            float(max_val)
            float(min_val)
        except ValueError:
            error_msg = f"❌ 阈值输入无效：请输入数字"
            print(error_msg)
            app_instance._update_recv_data(error_msg)
            Clock.schedule_once(lambda x: instance.reset_button_state(), 2)
            return
        
        # 构造JSON数据
        try:
            threshold_data = json.dumps({
                "max_do": max_val,
                "min_do": min_val,
                "timestamp": str(datetime.datetime.now())
            }, ensure_ascii=False)
        except Exception as e:
            error_msg = f"❌ 构造JSON失败：{str(e)}"
            print(error_msg)
            app_instance._update_recv_data(error_msg)
            Clock.schedule_once(lambda x: instance.reset_button_state(), 2)
            return
        
        # 发送数据到服务器
        try:
            if not app_instance or not app_instance.mqtt_client:
                raise Exception("MQTT客户端未初始化")
            
            send_result = app_instance.mqtt_client.publish_command("esp32/threshold", threshold_data)
            if send_result:
                success_msg = f"✅ 阈值已发送：最高{max_val} | 最低{min_val}"
                app_instance._update_recv_data(success_msg)
            else:
                raise Exception("MQTT未连接")
        
        except Exception as e:
            error_msg = f"❌ 发送阈值失败：{str(e)}"
            print(error_msg)
            app_instance._update_recv_data(error_msg)
        
        Clock.schedule_once(lambda x: instance.reset_button_state(), 2)
    
    confirm_btn.app_instance = app_instance
    confirm_btn.bind(on_press=on_confirm_click)

    # 历史数据按钮
    history_btn = NoBorderButton(
        text="历史数据",
        size_hint_x=None,
        width=dp(90),
        size_hint_y=None,
        height=dp(40)
    )
    def on_history_click(instance):
        instance.is_pressed = True
        instance.update_button_colors()
        from ui_utils import switch_page
        switch_page(app_instance, "history")
        Clock.schedule_once(lambda x: instance.reset_button_state(), 2)
    history_btn.bind(on_press=on_history_click)

    button_container.add_widget(confirm_btn)
    button_container.add_widget(history_btn)
    middle_layout.add_widget(input_container)
    middle_layout.add_widget(button_container)
    home_layout.add_widget(middle_layout)

    # 底部：PH值 + 温度展示
    sensor_layout = MDBoxLayout(
        orientation="horizontal",
        spacing=dp(40),
        size_hint_y=None,
        height=dp(50)
    )
    sensor_layout.add_widget(ph_label)
    sensor_layout.add_widget(temp_label)
    home_layout.add_widget(sensor_layout)


    ph_table_layout = MDBoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(230),
        pos_hint={"center_x": 0.55}
    )
    ph_table_image = Image(
        source="ph_safe_table.jpg",
        size_hint=(None, None),
        size=(dp(280), dp(280)),
        allow_stretch=True,
        keep_ratio=True
    )
    ph_table_layout.add_widget(ph_table_image)
    home_layout.add_widget(ph_table_layout)

    ph_note_layout = MDBoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(40)  # 增加高度，优化显示
    )
    ph_note_label = MDLabel(
        text="PH值安全范围在6~9",
        font_size=dp(16),
        font_name="CustomChinese",
        halign="center",
        bold=True
    )
    ph_note_layout.add_widget(ph_note_label)
    home_layout.add_widget(ph_note_layout)

    return home_layout

# 历史数据页面
def create_history_page(app_instance):
    history_layout = MDBoxLayout(
        orientation="vertical",
        padding=dp(20),
        spacing=dp(10),
        size_hint=(1, 1),
    )

    history_title = MDLabel(
        text="设备历史数据",
        font_size=dp(22),
        font_name="CustomChinese",
        halign="center",
        bold=True,
        size_hint_y=None,
        height=dp(60)
    )
    history_layout.add_widget(history_title)

    scroll_view = ScrollView(
        size_hint=(1, 1),
        do_scroll_x=False,
        scroll_type=['content', 'bars'],
        bar_width=dp(1),
        bar_color=(0.3, 0.3, 0.3, 1),
        bar_inactive_color=(0.8, 0.8, 0.8, 1),
        always_overscroll=True,
        scroll_wheel_distance=dp(20)
    )

    scroll_content = MDBoxLayout(
        orientation="vertical",
        spacing=dp(10),
        size_hint=(1, None),
        padding=dp(5)
    )
    scroll_content.bind(minimum_height=scroll_content.setter('height'))
    
    def refresh_history_ui():
        scroll_content.clear_widgets()
        # 确定展示数据
        display_data = GLOBAL_HISTORY_DATA if len(GLOBAL_HISTORY_DATA) > 0 else [
            "暂无历史数据，请先等待设备上传数据...",
            "2026-01-11 16:00: 溶解氧7.25mg/L | PH7.0 | 温度25.5℃"
        ]
        # 重新添加数据标签
        for idx, data in enumerate(display_data):
            data_label = MDLabel(
                text=data,
                font_size=dp(16),
                font_name="CustomChinese",
                halign="left",
                size_hint_y=None,
                height=dp(40),
                theme_text_color="Custom",
                text_color=(0.2, 0.2, 0.2, 1) if idx != 0 or len(GLOBAL_HISTORY_DATA) > 0 else (0.8, 0, 0, 1),
                valign="middle",
            )
            scroll_content.add_widget(data_label)

    # 初始化时先刷新一次
    refresh_history_ui()
    # 注册回调（切换页面时自动刷新）
    register_history_callback(refresh_history_ui)

    scroll_view.add_widget(scroll_content)
    history_layout.add_widget(scroll_view)

    # 页面销毁时注销回调
    def on_remove(instance, parent):
        unregister_history_callback(refresh_history_ui)
    history_layout.bind(on_remove=on_remove)

    return history_layout

# 个人中心页面
def create_me_page(app_instance):
    me_layout = MDBoxLayout(
        orientation="vertical",
        padding=dp(20),
        spacing=dp(15),
        size_hint_y=None,
    )
    me_layout.bind(minimum_height=me_layout.setter('height'))
    me_layout.add_widget(MDLabel(
        text="我的个人中心",
        font_size=dp(20),
        halign="center",
        font_name="CustomChinese",
        bold=True
    ))
    
    # 显示MQTT连接状态
    if hasattr(app_instance, 'mqtt_client') and app_instance.mqtt_client:
        connect_status = "已连接" if app_instance.mqtt_client.connected else "未连接"
        status_color = (0, 0.8, 0, 1) if app_instance.mqtt_client.connected else (0.8, 0, 0, 1)
    else:
        connect_status = "未初始化"
        status_color = (0.5, 0.5, 0.5, 1)
    
    status_label = MDLabel(
        text=f"服务器连接状态: {connect_status}",
        font_size=dp(16),
        font_name="CustomChinese",
        theme_text_color="Custom",
        text_color=status_color
    )
    me_layout.add_widget(status_label)
    
    # 设备信息
    me_layout.add_widget(MDLabel(
        text="设备编号：DEV-20260111",
        font_size=dp(16),
        font_name="CustomChinese"
    ))
    me_layout.add_widget(MDLabel(
        text="当前在线：是",
        font_size=dp(16),
        font_name="CustomChinese"
    ))

    # 运行日志
    me_layout.add_widget(MDLabel(
        text="运行日志",
        font_size=dp(18),
        font_name="CustomChinese",
        bold=True,
        size_hint_y=None,
        height=dp(40)
    ))
    # 日志滚动视图
    log_scroll_view = ScrollView(
        size_hint=(1, None),
        height=dp(200),
        do_scroll_x=False
    )
    # 日志标签
    log_label = MDLabel(
        text="", 
        font_name="CustomChinese", 
        size_hint_y=None,
        valign="top",
        halign="left"
    )
    log_label.is_log_label = True  # 标记为日志标签
    log_label.bind(texture_size=log_label.setter('size'))
    # 初始化日志内容
    from main import recv_data_list
    log_label.text = "\n".join(recv_data_list) + "\n"
    log_scroll_view.add_widget(log_label)
    me_layout.add_widget(log_scroll_view)

    return me_layout

# 整体UI构建
def create_app_ui(app_instance):
    # 基础配置
    Window.orientation = 'portrait'
    
    # 注册中文字体
    from ui_utils import register_chinese_font
    register_chinese_font()

    # 主题配置
    app_instance.theme_cls.primary_palette = "Blue"
    app_instance.theme_cls.theme_style = "Light"
    app_instance.theme_cls.font_styles.update({
        "H5": [ "CustomChinese", 24, False, 0.15 ],
        "Body1": [ "CustomChinese", 14, False, 0.15 ]
    })

    # 主容器
    main_container = MDBoxLayout(
        orientation="vertical",
        padding=0,
        spacing=0,
        size_hint=(1, 1)
    )

    # 页面容器（用于切换页面）
    app_instance.page_container = MDScrollView(
        do_scroll_x=False,
        do_scroll_y=True,  # 允许垂直滚动（适配小屏幕）
        size_hint=(1, 1),
        pos_hint={"top": 1.0}
    )
    app_instance.current_page = create_home_page(app_instance)
    app_instance.page_container.add_widget(app_instance.current_page)
    main_container.add_widget(app_instance.page_container)

    # 底部导航栏
    bottom_nav_bar = MDBoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(60),
        padding=[dp(60), dp(5), dp(60), dp(5)],
        spacing=Window.width * 0.2,
        md_bg_color=(1, 1, 1, 1),
        pos_hint={"center_x": 0.5, "y": 0.0}
    )
    # 导航栏阴影
    with bottom_nav_bar.canvas.before:
        Color(0, 0, 0, 0.1)
        Rectangle(
            pos=(bottom_nav_bar.x, bottom_nav_bar.y + bottom_nav_bar.height),
            size=(bottom_nav_bar.width, 2)
        )
    # 首页导航项
    nav_item1 = MDBoxLayout(
        orientation="vertical",
        size_hint_x=1,
        spacing=dp(2),
        pos_hint={"center_x": 0.5, "center_y": 0.5}
    )
    nav_item1_icon = MDIconButton(
        icon="home",
        size_hint=(None, None),
        size=(dp(24), dp(24)),
        pos_hint={"center_x": 0.5},
        md_bg_color=(1, 1, 1, 0),
        text_color=(0, 0, 0, 1)
    )
    from ui_utils import switch_page
    nav_item1_icon.bind(on_press=lambda x: switch_page(app_instance, "home"))
    nav_item1_text = MDLabel(
        text="首页",
        font_size=dp(12),
        font_name="CustomChinese",
        halign="center",
        color=(0, 0, 0, 1)
    )
    nav_item1.add_widget(nav_item1_icon)
    nav_item1.add_widget(nav_item1_text)

    # 个人中心导航项
    nav_item2 = MDBoxLayout(
        orientation="vertical",
        size_hint_x=1,
        spacing=dp(2),
        pos_hint={"center_x": 0.5, "center_y": 0.5}
    )
    nav_item2_icon = MDIconButton(
        icon="account-circle",
        size_hint=(None, None),
        size=(dp(24), dp(24)),
        pos_hint={"center_x": 0.5},
        md_bg_color=(1, 1, 1, 0),
        text_color=(0, 0, 0, 1)
    )
    nav_item2_icon.bind(on_press=lambda x: switch_page(app_instance, "me"))
    nav_item2_text = MDLabel(
        text="我",
        font_size=dp(12),
        font_name="CustomChinese",
        halign="center",
        color=(0, 0, 0, 1)
    )
    nav_item2.add_widget(nav_item2_icon)
    nav_item2.add_widget(nav_item2_text)

    bottom_nav_bar.add_widget(nav_item1)
    bottom_nav_bar.add_widget(nav_item2)
    main_container.add_widget(bottom_nav_bar)

    return main_container