
[app]

title = Simulador CNC
package.name = cncsimulator
package.domain = org.cnc.sim

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 1.0

requirements = python3,kivy==2.3.0

orientation = all
fullscreen = 0

[buildozer]

log_level = 2
warn_on_root = 1

[app:android]

android.api = 33
android.minapi = 23

# Usa o SDK que ja preparamos no workflow (com build-tools 33.0.2 que tem o aidl)
android.sdk_path = /home/runner/android-sdk

# NAO deixar o Buildozer atualizar/instalar build-tools novo (que quebra o aidl)
android.skip_update = True

android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
