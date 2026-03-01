[app]
title = 水质监控
package.name = esp32app
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf,json
source.include_patterns = ph_safe_table.jpg,Font_0.ttf
#source.include_patterns = image/* 打包image目录下的文件 pack files in the image directory
version = 0.0.1
#fullscreen = 0
orientation = portrait
# 修复后的依赖（关键！）
requirements = python3,kivy==2.2.1,kivymd==1.2.0,pyjnius==1.4.0,requests==2.31.0,kivy-garden==0.1.4,openssl,sqlite3
#icon.filename = icon.png
#presplash.filename = presplash.png
entrypoint = main.py

#这些不要改 don't change these
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
# 修复后的权限（关键！）
android.permissions = INTERNET,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

# 新增核心配置（解决闪退/APK打包问题）
android.add_assets = Font_0.ttf,ph_safe_table.jpg
android.request_android_permissions = True
android.extra_manifest_headers = android:requestLegacyExternalStorage="true"
android.debug = True
android.aab = False
p4a.build_mode = debug
p4a.add_jars = androidx.core:core:1.10.1,com.google.android.material:material:1.11.0
p4a.add_aars = 
p4a.mavens = https://maven.google.com

#以下为release模式需要 following is required for release mode

#强制构建APK而不是AAB（现在生效了）
#android.keystore = /home/runner/work/RepositoryName/AndAgain/DomainName.PackageName.keystore
#android.keystore_storepass = android
#android.keystore_keypass = android
#android.keystore_alias = DomainName.PackageName

[buildozer]
log_level = 2
warn_on_root = 1
