from PyQt5.QtWidgets import QWidget,QComboBox
from PyQt5.QtCore import pyqtSignal
import time

# 自定义信号必须是QObject的子类
class userComboBox(QComboBox):#,object
    # 信号定义必须在__init__函数外
    enterEventSignal = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__()
    # 当鼠标移动进入空间范围时触发信号
    def enterEvent(self, *args, **kwargs):
        self.enterEventSignal.emit()