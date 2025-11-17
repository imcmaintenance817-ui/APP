[app]

title = MaintLogbook
package.name = maintlogbook
package.domain = org.imc

# main python file
source.dir = .
source.main = main.py

# include all required files
source.include_exts = py,png,jpg,kv,atlas,csv,xlsx

version = 0.1

# Required modules
# pandas removed because your code no longer uses it
requirements = python3,kivy,kivymd,openpyxl

orientation = portrait
fullscreen = 0

# Android settings
android.api = 33
android.minapi = 21
android.ndk = 25b

# Build architectures
android.archs = arm64-v8a,armeabi-v7a

# Permissions needed for writing Excel files
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# Allow backup
android.allow_backup = True

# Disable Gstreamer (saves ~50 MB)
use_gstreamer = 0


[buildozer]
log_level = 2
warn_on_root = 1
