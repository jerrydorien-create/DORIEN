
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
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk
android.skip_update = True
p4a.branch = v2024.01.21
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
