[app]

# (str) Title of your application
title = IMC Logbook

# (str) Package name
package.name = imclogbook

# (str) Package domain (needed for android/ios packaging)
package.domain = org.imc

# (str) Source code directory
source.dir = .

# (list) Source files to include
source.include_exts = py,kv,csv,xlsx,png,jpg,atlas

# (str) Application version
version = 0.1

# (list) Application requirements
requirements = python3,kivy,kivymd,pandas,openpyxl

# (str) Supported orientations
orientation = portrait

# (bool) Fullscreen (0 = no, 1 = yes)
fullscreen = 0

# (list) Android permissions
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (list) Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) Allow Android auto backup feature
android.allow_backup = True

# (str) Android debug artifact type
android.debug_artifact = apk

# (str) Python-for-Android bootstrap
p4a.bootstrap = sdl2

# (str) Kivy version for iOS
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

# (bool) iOS code signing allowed
ios.codesign.allowed = false

[buildozer]

# (int) Log level (0 = error, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if run as root
warn_on_root = 1

# (str) Path to build output directory
build_dir = ./.buildozer
bin_dir = ./bin
