import sys
import os
import json
import serial
import serial.tools.list_ports
from datetime import datetime
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox, 
                            QFileDialog, QListWidgetItem)

class SerialThread(QThread):
    data_received = pyqtSignal(bytes)
    
    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = True
        
    def run(self):
        while self.running and self.serial_port.is_open:
            if self.serial_port.in_waiting:
                try:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    self.data_received.emit(data)
                except Exception as e:
                    print(f"串口读取错误: {e}")
    
    def stop(self):
        self.running = False
        self.wait()

class SerialTool(QMainWindow):
    def _get_resource_path(self, relative_path):
        """获取资源文件的绝对路径，兼容开发环境和PyInstaller打包环境"""
        try:
            # PyInstaller创建的临时文件夹路径
            base_path = sys._MEIPASS
            # 在打包环境中，文件会被解压到临时目录的根目录
            resource_path = os.path.join(base_path, os.path.basename(relative_path))
            if os.path.exists(resource_path):
                return resource_path
        except Exception:
            pass
        
        # 回退到开发环境路径
        return os.path.abspath(relative_path)

    def __init__(self):
        super().__init__()
        ui_path = self._get_resource_path('serial_tool.ui')
        if not os.path.exists(ui_path):
            QMessageBox.critical(self, "错误", f"无法找到UI文件: {ui_path}")
            sys.exit(1)
        uic.loadUi(ui_path, self)
        
        # 初始化变量
        self.serial_port = None
        self.serial_thread = None
        self.history_limit = 100  # 历史记录最大数量
        
        # 初始化UI
        self.init_ui()
        
        # 连接信号槽
        self.connect_signals()
        
        # 初始化串口
        self.refresh_ports()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置串口参数选项 - 紧凑布局
        self.baudCombo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baudCombo.setCurrentText("115200")
        self.baudCombo.setMaximumWidth(120)
        
        self.dataBitsCombo.addItems(["5", "6", "7", "8"])
        self.dataBitsCombo.setCurrentText("8")
        self.dataBitsCombo.setMaximumWidth(60)
        
        self.stopBitsCombo.addItems(["1", "1.5", "2"])
        self.stopBitsCombo.setCurrentText("1")
        self.stopBitsCombo.setMaximumWidth(60)
        
        self.parityCombo.addItems(["无", "奇校验", "偶校验", "标记", "空格"])
        self.parityCombo.setCurrentText("无")
        self.parityCombo.setMaximumWidth(80)
        
        # 设置时间格式选项
        self.timeFormatCombo.addItems([
            "%H:%M:%S",
            "%Y-%m-%d %H:%M:%S", 
            "[%H:%M:%S]",
            "[%Y-%m-%d %H:%M:%S]"
        ])
        self.timeFormatCombo.setCurrentText("[%H:%M:%S]")
        self.timeFormatCombo.setMaximumWidth(180)
        
        # 调整控件间距
        self.portCombo.setMinimumHeight(30)
        self.openBtn.setMinimumHeight(30)
        self.refreshBtn.setMinimumHeight(30)
        
        # 设置历史记录自动换行
        self.historyList.setWordWrap(True)
        
        # 设置接收区和发送区自动换行
        self.receiveText.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.sendText.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        
        # 设置窗口图标
        try:
            self.setWindowIcon(QtGui.QIcon('app.ico'))
        except:
            pass
        
    def connect_signals(self):
        """连接信号和槽"""
        self.refreshBtn.clicked.connect(self.refresh_ports)
        self.openBtn.clicked.connect(self.toggle_serial)
        self.sendBtn.clicked.connect(self.send_data)
        self.clearReceiveBtn.clicked.connect(self.clear_receive)
        self.saveReceiveBtn.clicked.connect(self.save_receive_data)
        self.resendBtn.clicked.connect(self.resend_data)
        self.deleteBtn.clicked.connect(self.delete_history)
        self.clearHistoryBtn.clicked.connect(self.clear_history)
        self.formatJsonBtn.clicked.connect(self.format_json)
        
        self.timestampCheck.stateChanged.connect(self.toggle_timestamp)
        self.hexDisplayCheck.stateChanged.connect(self.toggle_hex_display)
        
    def refresh_ports(self):
        """刷新可用串口列表"""
        self.portCombo.clear()
        try:
            ports = serial.tools.list_ports.comports()
            if not ports:
                self.portCombo.addItem("未检测到串口设备", "")
                print("未检测到串口设备，请检查:")
                print("1. 设备是否已连接")
                print("2. 驱动程序是否安装")
                print("3. 设备管理器是否显示COM端口")
            else:
                for port in ports:
                    desc = f"{port.device} - {port.description}" if port.description else port.device
                    self.portCombo.addItem(desc, port.device)
        except Exception as e:
            self.portCombo.addItem("串口检测失败", "")
            print(f"串口检测错误: {str(e)}")
    
    def toggle_serial(self):
        """打开/关闭串口"""
        if self.serial_port and self.serial_port.is_open:
            self.close_serial()
            self.openBtn.setText("打开串口")
        else:
            if self.open_serial():
                self.openBtn.setText("关闭串口")
    
    def open_serial(self):
        """打开串口"""
        port_name = self.portCombo.currentData()  # 获取实际端口名
        if not port_name:
            QMessageBox.warning(self, "警告", "请选择串口号!")
            return False
        
        try:
            # 配置串口参数
            baudrate = int(self.baudCombo.currentText())
            bytesize = int(self.dataBitsCombo.currentText())
            
            stopbits_map = {
                "1": serial.STOPBITS_ONE,
                "1.5": serial.STOPBITS_ONE_POINT_FIVE,
                "2": serial.STOPBITS_TWO
            }
            stopbits = stopbits_map[self.stopBitsCombo.currentText()]
            
            parity_map = {
                "无": serial.PARITY_NONE,
                "奇校验": serial.PARITY_ODD,
                "偶校验": serial.PARITY_EVEN,
                "标记": serial.PARITY_MARK,
                "空格": serial.PARITY_SPACE
            }
            parity = parity_map[self.parityCombo.currentText()]
            
            # 创建串口对象
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits,
                timeout=1
            )
            
            # 启动接收线程
            self.serial_thread = SerialThread(self.serial_port)
            self.serial_thread.data_received.connect(self.process_received_data)
            self.serial_thread.start()
            
            return True
            
        except serial.SerialException as e:
            error_msg = f"无法打开串口 {port_name}:\n{str(e)}\n\n"
            error_msg += "可能原因:\n"
            error_msg += "1. 端口已被其他程序占用\n"
            error_msg += "2. 驱动程序未正确安装\n"
            error_msg += "3. 设备已断开连接\n"
            error_msg += "4. 需要管理员权限"
            QMessageBox.critical(self, "串口错误", error_msg)
            return False
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发生未知错误: {str(e)}")
            return False
    
    def close_serial(self):
        """关闭串口"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread = None
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
    
    def send_data(self):
        """发送数据"""
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(self, "警告", "请先打开串口!")
            return
        
        data = self.sendText.toPlainText()
        if not data:
            QMessageBox.warning(self, "警告", "请输入要发送的数据!")
            return
        
        try:
            # 处理十六进制发送
            if self.hexSendCheck.isChecked():
                data = self.hex_string_to_bytes(data)
            else:
                # 自动添加换行
                if self.appendNewlineCheck.isChecked() and not data.endswith("\n"):
                    data += "\n"
                data = data.encode('utf-8')
            
            self.serial_port.write(data)
            
            # 添加到历史记录
            self.add_to_history(data)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发送失败: {str(e)}")
    
    def add_to_history(self, data):
        """添加数据到历史记录"""
        try:
            # 如果是十六进制数据，转换为可读格式
            if self.hexSendCheck.isChecked():
                display_data = " ".join(f"{b:02X}" for b in data)
            else:
                display_data = data.decode('utf-8', errors='replace').strip()
            
            # 添加时间戳
            if self.timestampCheck.isChecked():
                time_format = self.timeFormatCombo.currentText()
                timestamp = datetime.now().strftime(time_format)
                display_text = f"{timestamp} {display_data}"
            else:
                display_text = display_data
            
            # 创建历史记录项
            item = QListWidgetItem(display_text)
            item.setData(QtCore.Qt.UserRole, data)  # 保存原始数据
            
            # 添加到列表
            self.historyList.insertItem(0, item)
            
            # 限制历史记录数量
            if self.historyList.count() > self.history_limit:
                self.historyList.takeItem(self.historyList.count() - 1)
                
        except Exception as e:
            print(f"添加历史记录失败: {e}")
    
    def process_received_data(self, data):
        """处理接收到的数据"""
        try:
            # 十六进制显示
            if self.hexDisplayCheck.isChecked():
                display_data = " ".join(f"{b:02X}" for b in data)
            else:
                display_data = data.decode('utf-8', errors='replace')
            
            # 添加时间戳
            if self.timestampCheck.isChecked():
                time_format = self.timeFormatCombo.currentText()
                timestamp = datetime.now().strftime(time_format)
                display_text = f"{timestamp} {display_data}"
            else:
                display_text = display_data
            
            # 添加到接收区
            self.receiveText.moveCursor(QtGui.QTextCursor.End)
            self.receiveText.insertPlainText(display_text)
            
            # 自动滚动
            if self.autoScrollCheck.isChecked():
                self.receiveText.moveCursor(QtGui.QTextCursor.End)
                
        except Exception as e:
            print(f"处理接收数据失败: {e}")
    
    def resend_data(self):
        """重新发送选中的历史记录"""
        selected_items = self.historyList.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要重新发送的记录!")
            return
        
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(self, "警告", "请先打开串口!")
            return
        
        try:
            # 获取原始数据
            data = selected_items[0].data(QtCore.Qt.UserRole)
            self.serial_port.write(data)
            
            # 添加到历史记录顶部
            self.add_to_history(data)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重新发送失败: {str(e)}")
    
    def delete_history(self):
        """删除选中的历史记录"""
        selected_items = self.historyList.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请选择要删除的记录!")
            return
        
        for item in selected_items:
            self.historyList.takeItem(self.historyList.row(item))
    
    def clear_history(self):
        """清空历史记录"""
        self.historyList.clear()
    
    def clear_receive(self):
        """清空接收区"""
        self.receiveText.clear()
    
    def save_receive_data(self):
        """保存接收数据到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存接收数据", "", "文本文件 (*.txt);;所有文件 (*)")
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.receiveText.toPlainText())
                QMessageBox.information(self, "成功", "数据保存成功!")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def format_json(self):
        """格式化JSON数据"""
        try:
            text = self.sendText.toPlainText()
            if text:
                data = json.loads(text)
                formatted = json.dumps(data, indent=4, ensure_ascii=False)
                self.sendText.setPlainText(formatted)
        except json.JSONDecodeError:
            QMessageBox.warning(self, "警告", "不是有效的JSON格式!")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"格式化失败: {str(e)}")
    
    def toggle_timestamp(self, state):
        """切换时间戳显示"""
        self.timeFormatCombo.setEnabled(state == QtCore.Qt.Checked)
    
    def toggle_hex_display(self, state):
        """切换十六进制显示"""
        if state == QtCore.Qt.Checked:
            # 切换到十六进制显示时清空接收区
            self.receiveText.clear()
    
    def hex_string_to_bytes(self, hex_str):
        """将十六进制字符串转换为字节"""
        hex_str = hex_str.strip()
        hex_str = hex_str.replace(" ", "").replace("\n", "").replace("\r", "")
        
        # 验证十六进制字符串
        if not all(c in "0123456789ABCDEFabcdef" for c in hex_str):
            raise ValueError("无效的十六进制字符串")
        
        if len(hex_str) % 2 != 0:
            hex_str = "0" + hex_str
        
        return bytes.fromhex(hex_str)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.close_serial()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局样式
    app.setStyle("Fusion")
    
    # 设置字体
    font = QtGui.QFont()
    font.setFamily("Microsoft YaHei")
    font.setPointSize(10)
    app.setFont(font)
    
    window = SerialTool()
    window.show()
    sys.exit(app.exec_())
