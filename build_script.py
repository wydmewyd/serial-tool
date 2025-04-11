import PyInstaller.__main__
import os
import shutil

def build():
    # 确保UI文件存在
    if not os.path.exists('serial_tool.ui'):
        raise FileNotFoundError("serial_tool.ui not found in current directory")
    
    # PyInstaller配置
    # 设置控制台编码为UTF-8
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("[INFO] Checking resource files...")
    if not os.path.exists('serial_tool.ui'):
        raise FileNotFoundError("serial_tool.ui not found in project root")
    if os.path.exists('icon.ico'):
        print("[OK] Found icon file: icon.ico")
    else:
        print("[WARN] Icon file not found: icon.ico")

    params = [
        'serial_tool_2.py',
        '--onefile',
        '--windowed',
        '--add-data', 'serial_tool.ui:.',  # 修改分隔符为冒号(Windows兼容)
        '--icon=icon.ico' if os.path.exists('icon.ico') else '',
        '--clean',
        '--noconfirm',
        '--hidden-import=serial.tools.list_ports',
        '--hidden-import=serial.win32'
    ]
    print("PyInstaller参数:", params)
    
    # 移除之前构建的dist和build目录
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # 运行PyInstaller
    PyInstaller.__main__.run(params)

if __name__ == '__main__':
    build()
