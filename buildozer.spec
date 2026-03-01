[app]
title = 水质监控
package.name = esp32app
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf,json
source.include_patterns = ph_safe_table.jpg,Font_0.ttf
version = 0.0.1
orientation = portrait
# 精简依赖（移除冗余的sqlite3，安卓自带；openssl用系统版本）
requirements = python3,kivy==2.2.1,kivymd==1.2.0,pyjnius==1.4.0,requests==2.31.0,kivy-garden==0.1.4
entrypoint = main.py

# 基础配置（保留不变）
android.accept_sdk_license = True
android.allow_api_min = 21
android.api = 33
android.minapi = 21
android.ndk = 25b
exclude_patterns = **/test/*, **/tests/*
android.gradle_download = https://services.gradle.org/distributions/gradle-7.6.4-all.zip
android.gradle_plugin = 7.4.2
android.sdk = 33
android.ndk_api = 21
p4a.gradle_dependencies = gradle:7.6.4
p4a.bootstrap = sdl2
p4a.gradle_options = -Dorg.gradle.java.home=/usr/lib/jvm/java-17-openjdk-amd64
# 权限（保留修正后的）
android.permissions = INTERNET,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# 修复后的核心配置（解决闪退+能生成APK）
android.add_assets = Font_0.ttf,ph_safe_table.jpg
android.request_android_permissions = True
# 修复Manifest头格式（关键！）
android.extra_manifest_headers = <application android:requestLegacyExternalStorage="true"/>
android.debug = True
android.aab = False  # 强制生成APK（生效）
# 移除冲突配置
# p4a.build_mode = debug （删除这行）
# 移除不兼容的jars配置（KivyMD 1.2.0不需要额外安卓X依赖）
# p4a.add_jars = ... （删除这行）
# p4a.add_aars = ... （删除这行）
# p4a.mavens = ... （删除这行）

#release模式配置（保留注释）
#android.keystore = /home/runner/work/RepositoryName/AndAgain/DomainName.PackageName.keystore
#android.keystore_storepass = android
#android.keystore_keypass = android
#android.keystore_alias = DomainName.PackageName

[buildozer]
log_level = 2
warn_on_root = 1
