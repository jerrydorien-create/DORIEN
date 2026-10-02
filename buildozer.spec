[app]

# Nome exibido do app
title = Simulador CNC

# Nome do pacote e dominio (ajuste o dominio se quiser publicar)
package.name = cncsimulator
package.domain = org.cnc.sim

# Codigo fonte
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

# Versao do app
version = 1.0

# Dependencias Python (Kivy ja inclui o necessario para desenho)
requirements = python3,kivy==2.3.0

# Orientacao: todas (retrato e paisagem)
orientation = all

# Tela cheia desligada (mantem a barra de status)
fullscreen = 0

# Icone / splash (opcional - descomente e aponte para seus arquivos)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

[buildozer]

# Nivel de log (2 = detalhado)
log_level = 2
warn_on_root = 1

[app:android]

# APIs do Android
android.api = 34
android.minapi = 23

# Arquiteturas (celulares modernos sao arm64; a 2a cobre aparelhos antigos)
android.archs = arm64-v8a,armeabi-v7a

# Permite backup e aceita a licenca do SDK automaticamente
android.accept_sdk_license = True

# Sem permissoes especiais necessarias para este app
# android.permissions =
