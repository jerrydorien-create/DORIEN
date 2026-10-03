[app]

# Nome exibido do app
title = Simulador CNC

# Nome do pacote e dominio
package.name = cncsimulator
package.domain = org.cnc.sim

# Codigo fonte
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

# Versao do app
version = 1.0

# Dependencias Python
requirements = python3,kivy==2.3.0

# Orientacao: todas (retrato e paisagem)
orientation = all

# Tela cheia desligada (mantem a barra de status)
fullscreen = 0

# ---- Configuracoes do Android (TUDO precisa ficar na secao [app]) ----

# APIs do Android (igual a plataforma que o workflow instala: android-33)
android.api = 33
android.minapi = 23

# Arquiteturas (arm64 = celulares modernos; a 2a cobre aparelhos antigos)
android.archs = arm64-v8a,armeabi-v7a

# Aceita a licenca do SDK automaticamente
android.accept_sdk_license = True

# Usa o SDK que o workflow ja preparou (build-tools 33.0.2 contem o aidl)
# e impede o Buildozer de atualizar/baixar o proprio SDK (que puxaria o build-tools 37)
android.sdk_path = /home/runner/.buildozer/android/platform/android-sdk
android.skip_update = True

# Usa uma versao ESTAVEL do python-for-android (Python 3.11).
# A versao mais nova usa Python 3.14, que quebra a compilacao do Kivy 2.3.0.
p4a.branch = v2024.01.21


[buildozer]

# Nivel de log (2 = detalhado)
log_level = 2
warn_on_root = 1
