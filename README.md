# SerialAssistantLXL
使用python3.6+pyserial+pyqt5实现的串口调试助手

- 支持串口ascii/Hex收发方式

# 2019-7-24
- 新增专用于更新设备列表的按键，取消移入串口设备列表窗体自动更新设备列表功能（此功能系统调用时执行时间不稳定，时长时短，可能导致软件卡死）

# 2019-4-23
- 增加userSerial中接收缓存限制，如果缓存数据超长，截取最新部分
- 修正在串口接收数量统计时错误
- 修改userSerial.recv函数返回值错误，当未接收到数据时，返回空的bytes()而非None
- 修正当textBrowserReceive调用insertPlainText函数时，如果界面有文本被选中，新插入内容将替换被选中内容的问题
    - 方法：在需要调用insertPlainText的函数开始，先将光标位置移动到文本结尾，然后再调用insertPlainText()
```
self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)    #将坐标移动到文本结尾，
self.textBrowserReceive.insertPlainText(strHexBuf)
```
- 修正配置停止位导致界面崩溃
    - 问题原因：调用实例方法时传入了self导致
    ```
    self._update_radioButtonStop(self,serial.STOPBITS_ONE, checked)
    更改为:
    self._update_radioButtonStop(serial.STOPBITS_ONE, checked)
    ```
# 2019-4-24
- 增加图标
- 增加菜单栏及菜单项（未实现底层操作）

# 2019-4-25
- 增加双语功能

# 2019-4-26
- 增加置顶功能
- 调试置顶功能时发现自动关闭了主窗口，需要使用show()显示
- 使用toggled方式时正常，但使用triggered方式时界面挂了，增加槽函数装饰器后恢复正常
    ```
    @QtCore.pyqtSlot(bool)# 槽函数最好加装饰器，否则可能导致异常发生
    def on_actionAlwaysOnTop_triggered(self,checked):
    # def on_actionAlwaysOnTop_toggled(self,checked):
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint,checked)
        if not self.isVisible():
            self.show()
    ```
# 2019-4-27
- 加入Dock和TabWidget元素 待测试效果