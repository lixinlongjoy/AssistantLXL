# 调试相关功能定义
import logging
# LOG_FORMAT = "%(asctime)s>%(levelname)s>%(process)d>%(processName)s>%(thread)d>%(thread)s>%(module)s>%(lineno)d>%(funcName)s>%(message)s"
# DATE_FORMAT = "%y-%m-%d %H:%M:%S,"
# DATE_FORMAT = "%y-%m-%d %H:%M:%S %p"
__LOG_FORMAT = "%(asctime)s>%(levelname)s>PID:%(process)d %(thread)d>%(module)s>%(funcName)s>%(lineno)d>%(message)s"
logging.basicConfig(level=logging.DEBUG, format=__LOG_FORMAT, )
# logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, )

# 是否打印调试信息标志
debug = False

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import pyqtSignal,QObject

# 自定义QComboBox的子类
class userComboBox(QComboBox):#,object
    '''
    自定义QComboBox的子类
    重构enterEvent方法
    创建enterEventSignal
    在发生enterEvent事件时触发信号enterEventSignal
    '''

    # 定义鼠标移动到空间区域内发射的信号
    enterEventSignal = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__()
    # 当鼠标移动进入空间范围时触发信号
    def enterEvent(self, *args, **kwargs):
        if debug == True:
            logging.debug("发生enterEvent，触发enterEventSignal")
        self.enterEventSignal.emit()
        super().enterEvent( *args, **kwargs)

if __name__ == "__main__":
    print(issubclass(QComboBox, QObject))
    print(issubclass(userComboBox,QObject))