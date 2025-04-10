import PyInstaller.__main__
import os
import sys

# 检查必要文件是否存在
required_files = ['serial_tool.py', 'serial_tool.ui']
missing_files = [f for f in required_files if not os.path.exists(f)]
if missing_files:
    print(f"错误：缺少必要文件: {', '.join(missing_files)}")
    sys.exit(1)

# 使用我们创建的icon.ico作为应用图标
icon_file = 'icon.ico'
if not os.path.exists(icon_file):
    print(f"警告：图标文件 {icon_file} 不存在，将不使用图标")

args = [
    'serial_tool.py',
    '--onefile',
    '--windowed',
    '--add-data', 'serial_tool.ui:serial_tool.ui',  # 明确指定目标文件名
    '--name', 'SerialTool',
    '--clean',
    '--noconsole'
]

# 如果图标文件存在则添加图标参数
if os.path.exists(icon_file):
    args.extend(['--icon', icon_file])

PyInstaller.__main__.run(args)
