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

# API alvo e minima
android.api = 33
android.minapi = 23

# IMPORTANTE: fixar o build-tools 33.0.2, que ainda possui o 'aidl'.
# As versoes 34+ removeram o aidl e quebram o Buildozer.
android.build_tools = 33.0.2

# Arquiteturas suportadas
android.archs = arm64-v8a,armeabi-v7a

# Aceita a licenca do SDK automaticamente
android.accept_sdk_license = True
