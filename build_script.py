import PyInstaller.__main__
import os
import shutil

def build():
    # 确保UI文件存在
    if not os.path.exists('serial_tool.ui'):
        raise FileNotFoundError("serial_tool.ui not found in current directory")
    
    # PyInstaller配置
    print("正在检查资源文件...")
    if not os.path.exists('serial_tool.ui'):
        raise FileNotFoundError("serial_tool.ui文件未找到，请确保它在项目根目录")
    if os.path.exists('icon.ico'):
        print("找到图标文件: icon.ico")
    else:
        print("警告: 未找到图标文件icon.ico")

    params = [
        'serial_tool_2.py',
        '--onefile',
        '--windowed',
        '--add-data', 'serial_tool.ui:.',  # 修改分隔符为冒号(Windows兼容)
        '--icon=icon.ico' if os.path.exists('icon.ico') else '',
        '--clean',
        '--noconfirm'
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
