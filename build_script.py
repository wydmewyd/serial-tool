import PyInstaller.__main__
import os
import shutil

def build():
    # 确保UI文件存在
    if not os.path.exists('serial_tool.ui'):
        raise FileNotFoundError("serial_tool.ui not found in current directory")
    
    # PyInstaller配置
    params = [
        'serial_tool_2.py',
        '--onefile',
        '--windowed',
        '--add-data', 'serial_tool.ui;.',
        '--icon=icon.ico' if os.path.exists('icon.ico') else '',
        '--clean'
    ]
    
    # 移除之前构建的dist和build目录
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # 运行PyInstaller
    PyInstaller.__main__.run(params)

if __name__ == '__main__':
    build()
