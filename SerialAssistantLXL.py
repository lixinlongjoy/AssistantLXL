# 调试相关功能定义
import logging
# LOG_FORMAT = "%(asctime)s>%(levelname)s>%(process)d>%(processName)s>%(thread)d>%(thread)s>%(module)s>%(lineno)d>%(funcName)s>%(message)s"
# DATE_FORMAT = "%y-%m-%d %H:%M:%S,"
# DATE_FORMAT = "%y-%m-%d %H:%M:%S %p"
__LOG_FORMAT = "%(asctime)s>%(levelname)s>PID:%(process)d %(thread)d>%(module)s>%(funcName)s>%(lineno)d>%(message)s"
logging.basicConfig(level=logging.DEBUG, format=__LOG_FORMAT, )
# logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, )

# 是否打印调试信息标志
debug = True
if debug==True:
    logging.debug("进入主程序，开始导入包...")

import time
from time import sleep
import os
import sys
import re
import codecs
import threading

from PyQt5 import QtCore,QtGui
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QApplication,QDialog,QMainWindow,QMessageBox,QComboBox,QLabel

# 配置
# 统计线程周期
periodStatistics = 1

from comSerialWidget import  Ui_SerialAssistantLXL
import serial
from userSerial import userSerial,suportBandRateList


def userCodecsReplaceError(error):
    """
    字符编解码异常处理 直接将错误字节替代为"*E*"
    :param error: UnicodeDecodeError实例
    :return:
    """
    if not isinstance(error, UnicodeDecodeError):
        raise error

    return ("*E*", error.start + 1)

def userCodecsError(error):
    """
    字符编解码异常处理 暂缓+替代
    Error handler for surrogate escape decoding.

    Should be used with an ASCII-compatible encoding (e.g., 'latin-1' or 'utf-8').
    Replaces any invalid byte sequences with surrogate code points.

    As specified in https://docs.python.org/2/library/codecs.html#codecs.register_error.
    """
    # We can't use this with UnicodeEncodeError; the UTF-8 encoder doesn't raise
    # an error for surrogates. Instead, use encode.
    if not isinstance(error, UnicodeDecodeError):
        raise error
    # print(error)
    # print(error.start)
    # print(error.end)
    # print(error.encoding)
    # print(error.object)
    # print(error.reason)
    # 引发异常 待继续接收更多数据后再尝试解码处理
    if error.end - error.start <= 3:
        raise error
    # 从出错位置开始到所处理数据结束，如果数据长度>=5,则第一个字节必然是错误字节，而非未完整接收
    # 此时直接将第一个字节使用*E*代替，并返回下一个字节索引号
    else:
        return ("*E*", error.start + 1)

# 添加自定义解码异常处理handler
codecs.register_error("userCodecsReplaceError",userCodecsReplaceError)
codecs.register_error("userCodecsError",userCodecsError)


class userMain(QMainWindow,Ui_SerialAssistantLXL):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        if debug == True:
            logging.debug("初始化主程序:")

        # 初始化串口对象
        self.__comBoxPortBuf = ""#当前使用的串口号
        self.__comPortList = []#系统可用串口号
        self.__com = userSerial(baudrate=115200, timeout=0)#实例化串口对象
        # 非PyQt控件无法支持自动信号与槽函数连接，必须手动进行
        self.__com.signalRcv.connect(self.on_com_signalRcv)
        self.__com.signalRcvError.connect(self.on_com_signalRcvError)

        self.__update_comboBoxPortList()#更新系统支持的串口设备并更新端口组合框内容
        self.__update_comboBoxBandRateList()# 更新波特率组合框内容

        self.__rcvAsciiHex = True#接收ASCII模式
        self.__rcvRecordTime = False#接收记录时间
        self.__rcvAutoCLRF = False#接收自动换行
        self.__rcvAsciiBuf = bytearray()# 接收缓冲 用于字符接收模式时解决一个字符的字节码被分两批接收导致的解码失败问题
        self.__rcvTotal = 0
        self.__rcvTotalLast = 0

        self.__sndAsciiHex = True#发送ASCII模式
        self.__sndAutoCLRF = False#发送追加换行
        self.__txPeriodEnable = False#周期发送使能
        self.__sndTotal = 0
        self.__sndTotalLast = 0

        self.lineEditPeriodMs.setValidator(QIntValidator(0,99999999))# 周期发送时间间隔验证器
        self.__txPeriod = int(self.lineEditPeriodMs.text())#周期长度ms

        # self.comboBoxSndHistory.setInsertPolicy(QComboBox.InsertAtBottom)

        # 设置发送区字符有效输入范围
        # r"^-?(90|[1-8]?\d(\.\d{1,4})?)$"  匹配-90至90之间，小数点后一至四位小数的输入限制
        # r(^-?180$)|(^-?1[0-7]\d$)|(^-?[1-9]\d$)|(^-?[1-9]$)|^0$");
        # self.textEditSend.setValidator(QIntValidator(0,99999999))
        self.__textEditSendLastHex = self.textEditSend.toPlainText()#Hex模式时 发送编辑区上次Hex字符串备份，用于使用re验证输入有效性
        self.__periodSendBuf = bytearray()#周期发送时 发送数据缓存

        # 获取状态栏对象
        self.__status = self.statusBar

        # 在状态栏增加接收总数 接收速率 发送总数 发送速率的标签
        self.__NullLabel = QLabel("NULL")
        self.__rcvTotalLabel = QLabel("接收总数:")
        self.__rcvTotalValueLabel = QLabel()
        self.__rcvSpeedLabel = QLabel("接收速率:")
        self.__rcvSpeedValueLabel = QLabel()
        self.__sndTotalLabel = QLabel("发送总数:")
        self.__sndTotalValueLabel = QLabel()
        self.__sndSpeedLabel = QLabel("发送速率:")
        self.__sndSpeedValueLabel = QLabel()

        # 右下角窗口尺寸调整符号
        self.__status.setSizeGripEnabled(False)
        # status.isSizeGripEnabled()
        # status.setSizeGripEnabled(True)
        # 每个单元之间小竖线 分隔不同控件，
        # 将状态栏所有Item边框宽度设置为0
        self.__status.setStyleSheet("QStatusBar.item{border:10px}")
        # 非永久信息 一般信息显示，在最左边，通过addWIdget insertWidget插入
        # 通过此方法添加必要时会被更改和覆盖
        inter = 5
        self.__status.addWidget(self.__NullLabel, inter)
        self.__status.addWidget(self.__rcvTotalLabel, inter)
        self.__status.addWidget(self.__rcvTotalValueLabel, inter)
        self.__status.addWidget(self.__rcvSpeedLabel, inter)
        self.__status.addWidget(self.__rcvSpeedValueLabel, inter)
        self.__status.addWidget(self.__sndTotalLabel, inter)
        self.__status.addWidget(self.__sndTotalValueLabel, inter)
        self.__status.addWidget(self.__sndSpeedLabel, inter)
        self.__status.addWidget(self.__sndSpeedValueLabel, inter)

        if debug == True:
            logging.debug("当前系统可用端口:{}".format(self.__comPortList))
            logging.debug("初始化主程序完成")

# 串口配置相关
#     更新系统支持的串口设备并更新端口组合框内容
    def __update_comboBoxPortList(self):
        start = time.time()
        # 获取可用串口号列表
        newportlistbuf = userSerial.getPortsList()
        if self.__comBoxPortBuf == "" or  newportlistbuf != self.__comPortList:
            self.__comPortList = newportlistbuf

            if len(self.__comPortList) > 0:
                # 将串口号列表更新到组合框
                self.comboBoxPort.setEnabled(False)
                self.comboBoxPort.clear()
                self.comboBoxPort.addItems([self.__comPortList[i][1] for i in range(len(self.__comPortList))])

                # self.__comBoxPortBuf为空值 默认设置为第一个串口
                if self.__comBoxPortBuf == "":
                    self.__comBoxPortBuf = self.__comPortList[0][1]
                else:
                    # 遍历当前列表 查找是否上次选定的串口在列表中出现，如果出现则选中上次选定的串口
                    seq = 0
                    for i in self.__comPortList:
                        if i[1] == self.__comBoxPortBuf:
                            self.comboBoxPort.setCurrentIndex(seq)
                            break
                        seq+=1
                    # 全部遍历后发现上次选定串口无效时，设置第一个串口
                    else:
                        self.__comBoxPortBuf = self.__comPortList[0][1]

                self.comboBoxPort.setEnabled(True)
                if debug == True:
                    logging.debug("更新可用串口列表")
            else:
                self.comboBoxPort.setEnabled(False)
                self.comboBoxPort.clear()
                self.__comBoxPortBuf = ""
                self.comboBoxPort.addItem("无可用串口设备")
                # self.comboBoxPort.setEnabled(True)
                if debug == True:
                    logging.warning("更新可用串口列表：无可用串口设备")
        else:
            if debug == True:
                logging.debug("更新可用串口列表：列表未发生变化")

        stop = time.time()
        if debug == True:
            logging.debug("更新串口列表时间{}s".format(stop-start))

    # self.comboBoxPort.activated[str].connect(self.onActivated)  # 手动触发时启动
    # self.comboBoxPort.enterEventSignal.connect(self.on_comboBoxPort_enterEventSignal)
    # def on_comboBoxPort_currentIndexChanged(self, text):#选中组合框中与当前不同的项目时触发
    def on_comboBoxPort_activated(self, text):# 手动触发时启动
        if isinstance(text,int):
            if debug == True:
                logging.debug("更换选中串口号:{}".format(text))
        if isinstance(text,str):
            if debug == True:
                logging.debug("更换选中串口名称:{}".format(text))
            if(text != ""):
                # 切换串口前，如果当前为已打开端口则关闭端口
                if self.__com.getPortState() == True:
                    self.on_pushButtonOpen_toggled(False)
                self.__comBoxPortBuf = text

    # 鼠标移入控件事件
    def on_comboBoxPort_enterEventSignal(self):
        if debug == True:
            logging.debug("鼠标移入comboBoxPort控件，即将更新串口列表")
        self.__update_comboBoxPortList()

    # def on_comboBoxPort_dropdown(self,event):
    #     print(event)
    #
    # def on_comboBoxPort_mousePressEvent(event):
    #     print(event)

    # 更新波特率组合框
    def __update_comboBoxBandRateList(self):
        # 将串口号列表更新
        self.comboBoxBand.setEnabled(False)
        self.comboBoxBand.clear()
        self.comboBoxBand.addItems([str(i) for i in suportBandRateList])
        # 设置默认波特率
        self.comboBoxBand.setCurrentText("115200")
        # print(self.comboBoxBand.currentIndex())
        self.comboBoxBand.setEnabled(True)

    # self.comboBoxBand
    # def on_comboBoxBand_currentIndexChanged(self,text):
    def on_comboBoxBand_activated(self, text):
        if isinstance(text,str):
            try:
                self.__com.port.baudrate = (int(text))
                if debug == True:
                    logging.debug("更新波特率:{}".format(self.__com.port.baudrate))
            except Exception as e:
                if debug == True:
                    logging.error("更新波特率:{}".format(e))

    # # 数据位
    def _update_radioButtonDataBit(self,bit,checked):
        if checked == True:
            try:
                self.__com.port.bytesize = bit
                if debug == True:
                    logging.debug("更新数据位:{}".format(self.__com.port.bytesize))
            except Exception as e:
                if debug == True:
                    logging.error("更新数据位:{}".format(e))
        else:
            try:
                if debug == True:
                    logging.debug("取消此数据位:{}".format(self.__com.port.bytesize))
            except Exception as e:
                if debug == True:
                    logging.error("取消此数据位:{}".format(e))

    # self.radioButtonData8Bit
    # self.radioButtonData7Bit
    # self.radioButtonData6Bit
    # self.radioButtonData5Bit
    def on_radioButtonData8Bit_toggled(self,checked):
        self._update_radioButtonDataBit(serial.EIGHTBITS, checked)
    def on_radioButtonData7Bit_toggled(self,checked):
        self._update_radioButtonDataBit(serial.SEVENBITS, checked)
    def on_radioButtonData6Bit_toggled(self,checked):
        self._update_radioButtonDataBit(serial.SIXBITS, checked)
    def on_radioButtonData5Bit_toggled(self,checked):
        self._update_radioButtonDataBit(serial.FIVEBITS,checked)

    # # 校验位
    def _update_radioButtonParity(self,parity,checked):
        if checked == True:
            try:
                self.__com.port.parity = parity
                if debug == True:
                    logging.debug("更新校验:{}".format(self.__com.port.parity))
            except Exception as e:
                if debug == True:
                    logging.error("更新校验:{}".format(e))
        else:
            try:
                if debug == True:
                    logging.debug("取消此校验:{}".format(self.__com.port.parity))
            except Exception as e:
                if debug == True:
                    logging.error("取消此校验:{}".format(e))

    # self.radioButtonParityNone
    # self.radioButtonParityEven
    # self.radioButtonParityOdd
    # self.radioButtonParityMark
    # self.radioButtonSpace
    def on_radioButtonParityNone_toggled(self,checked):
        self._update_radioButtonParity(serial.PARITY_NONE,checked)
    def on_radioButtonParityEven_toggled(self,checked):
        self._update_radioButtonParity(serial.PARITY_EVEN,checked)
    def on_radioButtonParityOdd_toggled(self,checked):
        self._update_radioButtonParity(serial.PARITY_ODD,checked)
    def on_radioButtonParityMark_toggled(self,checked):
        self._update_radioButtonParity(serial.PARITY_MARK,checked)
    def on_radioButtonSpace_toggled(self,checked):
        self._update_radioButtonParity(serial.PARITY_SPACE,checked)

    # # 流控
    # self.checkBoxFlowCtrl
    # def on_checkBoxFlowCtrl_stateChanged(self,checked):
    def on_checkBoxFlowCtrl_toggled(self,checked):
        try:
            self.__com.port.rtscts = checked
            if debug == True:
                logging.debug("更新流控开关:{}".format(self.__com.port.rtscts))
        except Exception as e:
            if debug == True:
                logging.error("更新流控开关失败:{}".format(e))

    # # 停止位
    def _update_radioButtonStop(self,stop,checked):
        if checked == True:
            try:
                self.__com.port.stopbits = stop
                if debug == True:
                    logging.debug("更新停止位:{}".format(self.__com.port.stopbits))
            except Exception as e:
                if debug == True:
                    logging.error("更新停止位:{}".format(e))
        else:
            try:
                if debug == True:
                    logging.debug("取消此停止位:{}".format(self.__com.port.stopbits))
            except Exception as e:
                if debug == True:
                    logging.error("取消此停止位:{}".format(e))

    # self.radioButtonStop1Bit
    # self.radioButtonStop1_5Bit
    # self.radioButtonStop2Bit
    def on_radioButtonStop1Bit_toggled(self,checked):
        self._update_radioButtonStop(self, serial.STOPBITS_ONE, checked)
    def on_radioButtonStop2Bit_toggled(self,checked):
        self._update_radioButtonStop(self, serial.STOPBITS_TWO, checked)
    def on_radioButtonStop1_5Bit_toggled(self,checked):
        self._update_radioButtonStop(self,serial.STOPBITS_ONE_POINT_FIVE, checked)

    # # 打开/关闭开关
    # self.pushButtonOpen
    # def on_pushButtonOpen_pressed(self):
    def on_pushButtonOpen_toggled(self,checked):
        if debug == True:
            logging.debug("pushButtonOpen:Toggle{}".format(checked))
        if checked ==True:
        #  打开指定串口
            portBuf = ""
            # 在端口列表中搜索当前串口名称对应的端口号
            seq = 0
            for i in self.__comPortList:
                if i[1] == self.__comBoxPortBuf:
                    portBuf  = i[0]
                    break
                seq+=1
            if (portBuf != ""):
                try:
                    self.__com.open(portBuf)
                    if debug == True:
                        logging.debug("端口{}已打开".format(portBuf))
                    self.pushButtonOpen.setText("关闭")

                    # 在userSerial类中已经实现了接收完成signalRcv信号机制，无需启动线程刷屏，只需将信号关联到对应的槽函数即可
                    # # 开启接收线程刷屏
                    # threading.Thread(target=self.__textBrowserReceiveRefresh, args=(), daemon=True).start()
                    # 开启统计线程
                    threading.Thread(target=self.periodUpdateStatistics, args=(), daemon=True).start()

                except Exception as e:
                    self.__NullLabel.setText(e.args[0].args[0])
                    if debug == True:
                        logging.error("端口{}打开出错".format(e))

            else:
                if debug == True:
                    logging.debug("无可用串口")
                self.__pushButtonOpen_State_Reset()
        else:
        #  关闭当前打开的串口
            if self.__com.getPortState() == True:
                self.__com.port.close()
                if debug == True:
                    logging.debug("端口{}已关闭".format(self.__comBoxPortBuf))
            else:
                if debug == True:
                    logging.debug("端口{}未打开".format(self.__comBoxPortBuf))
            self.__pushButtonOpen_State_Reset()

    def __pushButtonOpen_State_Reset(self):
        self.pushButtonOpen.setText("打开")
        # 设置Checked状态会导致on_pushButtonOpen_toggled触发
        self.pushButtonOpen.setChecked(False)


# 串口接收设置
#     # ASCII接收显示
# #     self.radioButtonRxAscii
    def on_radioButtonRxAscii_toggled(self,checked):
        if checked == True:
            self.__rcvAsciiBuf = bytearray()#切换为Ascii接收模式时清空接收缓存
            self.__rcvAsciiHex = True
            # 在ascii模式下使能记录时间和自动换行功能
            self.checkBoxRxRecordTime.setEnabled(True)
            self.checkBoxRxAutoCLRF.setEnabled(not self.__rcvRecordTime)
            if debug == True:
                logging.debug("更新接收模式:ASCII")
        else:
            if debug == True:
                logging.debug("取消接收模式:ASCII")

#     # 记录时间
#     self.checkBoxRxRecordTime
    def on_checkBoxRxRecordTime_toggled(self,checked):
        self.__rcvRecordTime = checked
        # 如果选择记录时间，则禁止接收自动换行的配置
        self.checkBoxRxAutoCLRF.setEnabled(not checked)
        # 选择接收记录时间则在文本浏览器中追加行 便于格式对齐
        if checked == True:
            # 接收文本浏览器换行
            self.textBrowserReceive.append("")
        if debug == True:
            logging.debug("更新记录接收时间:{}".format(checked))
#     # 自动换行
#     self.checkBoxRxAutoCLRF
    def on_checkBoxRxAutoCLRF_toggled(self,checked):
        self.__rcvAutoCLRF = checked
        # 选择接收自动换行则在文本浏览器中追加行 便于格式对齐
        if checked == True:
            self.textBrowserReceive.append("")
        if debug == True:
            logging.debug("更新接收自动换行:{}".format(checked))

#     # Hex接收显示
#     self.radioButtonRxHex
    def on_radioButtonRxHex_toggled(self,checked):
        if checked == True:
            self.__rcvAsciiHex = False
            # Hex接收时将记录时间和自动换行禁止
            self.checkBoxRxRecordTime.setEnabled(False)
            self.checkBoxRxAutoCLRF.setEnabled(False)
            if debug == True:
                logging.debug("更新接收模式:Hex")
        else:
            if debug == True:
                logging.debug("取消接收模式:Hex")

# 串口发送设置
#     # ASCII发送
#     self.radioButtonTxAscii
    def on_radioButtonTxAscii_toggled(self,checked):
        if checked == True:
            self.__sndAsciiHex = True
            # 设置自动换行使能
            self.checkBoxTxAutoCRLF.setEnabled(True)
            if debug == True:
                logging.debug("更新发送模式:ASCII")
        else:
            if debug == True:
                logging.debug("取消发送模式:ASCII")
#     # ASCII发送时自动追加回车换行
#     self.checkBoxTxAutoCRLF
    def on_checkBoxTxAutoCRLF_toggled(self,checked):
        self.__sndAutoCLRF = checked
        if debug == True:
            logging.debug("更新发送自动换行:{}".format(checked))
#     # Hex发送
#     self.radioButtonTxHex
    def on_radioButtonTxHex_toggled(self,checked):
        if checked == True:
            self.__sndAsciiHex = False
            # 设置自动换行禁能
            self.checkBoxTxAutoCRLF.setEnabled(not checked)
            if debug == True:
                logging.debug("更新发送模式:Hex")
        else:
            if debug == True:
                logging.debug("取消发送模式:Hex")
#     # 周期发送使能
#     self.checkBoxTxPeriodEnable
    def on_checkBoxTxPeriodEnable_toggled(self,checked):
        self.__txPeriodEnable = checked
        if debug == True:
            logging.debug("更新周期发送使能:{}".format(checked))
#     # 发送周期
#     self.lineEditPeriodMs
    def on_lineEditPeriodMs_textChanged(self,text):
        if (text != "" and text != "0"):#
            # 当text是0时，lstrip("0")将导致字符串结果是""
            self.lineEditPeriodMs.setText((self.lineEditPeriodMs.text().lstrip('0')))
            self.__txPeriod = int(text)
        else:#空或者0
            self.lineEditPeriodMs.setText("0")
            self.__txPeriod = 0
        if debug == True:
            logging.debug("更新周期发送时间设置:text-->{}  period-->{}".format(text, self.__txPeriod))

#     #接收显示区
#     self.textBrowserReceive
#     def __textBrowserReceiveRefresh(self):
    def on_textBrowserReceive_textChanged(self):
        """
        文本浏览器textChanged槽函数
            文本浏览器中文本改变时将光标移动到末尾
        :return:
        """
        self.textBrowserReceive.moveCursor(self.textBrowserReceive.textCursor().End)

    # self.com.signalRcv
    # 非PyQt控件无法支持自动信号与槽函数连接，必须手动进行
    def on_com_signalRcv(self,count):
        if debug == True:
            logging.debug("串口接收:{}".format(count))

        buf = self.__com.recv(count)
        self.__rcvTotal += len(buf)
        if buf != None:
            if debug == True:
                logging.debug("原始数据:{}".format(buf))

            # 判断接收模式
            if self.__rcvAsciiHex == True:
            # ASCII接收模式
                if self.__rcvRecordTime == True:  # 接收记录时间
                    currTime = time.time()
                    mSec = int(1000*(currTime-int(currTime)))
                    self.textBrowserReceive.insertPlainText("{}.{:03d}: ".format(time.strftime("%H:%M:%S"),mSec))

                # 接收处理方式一 ASCII接收模式下 对单次 self.com.recv进行解码 当由于本次接收数据与上次或者下次数据包的连接处非右不完整字符的字节码导致的解码失败时，调用ingore 错误处理handler（忽略错误字节）或者自定义的userCodecsReplaceError(将错误字节替换成*E*)
                # try:
                #     buf = buf.decode("utf-8",errors="ignore")
                #     buf = buf.decode("utf-8",errors="userCodecsReplaceError")
                #     self.textBrowserReceive.insertPlainText(buf)
                #     if debug == True:
                #         logging.debug("ASCII:{}".format(buf))
                #     if self.__rcvAutoCLRF == True or self.__rcvRecordTime == True:  # 接收自动换行
                #         self.textBrowserReceive.insertPlainText("\r\n")
                # except Exception as e:
                #     self.textBrowserReceive.append("\r\n---解码失败!---\r\n")
                #     if debug == True:
                #         logging.error("串口接收解码解码失败:{}".format(e))

                # 接收处理方式二 将接收的数据放入缓冲中，按照可解码的长度进行解码，剩余无法解码部分判断是否超过了3字节，依次，保留供下次接收到新数据后使用
                # 将接收到的新数据保存到缓冲中
                self.__rcvAsciiBuf += buf
                try:
                    txt = self.__rcvAsciiBuf.decode("utf-8",errors="userCodecsError")
                    self.textBrowserReceive.insertPlainText(txt)
                    if debug == True:
                        logging.debug("ASCII:{}".format(txt))
                    if self.__rcvAutoCLRF == True or self.__rcvRecordTime == True:  # 接收自动换行
                        self.textBrowserReceive.insertPlainText("\r\n")
                    # 正确解码时 清空接收缓冲
                    self.__rcvAsciiBuf = bytearray()
                except Exception as e:
                    if debug == True:
                        logging.error("串口接收解码解码失败:{},需要尝试部分解码".format(e))
                    # 如果错误位置在第三个字符之后，执行部分解码
                    if e.start >= 3:
                        # 部分解码
                        bufPart = self.__rcvAsciiBuf[:e.start]
                        self.__rcvAsciiBuf = self.__rcvAsciiBuf[e.start:]
                        txt = bufPart.decode("utf-8", errors="userCodecsError")
                        self.textBrowserReceive.insertPlainText(txt)
                        if debug == True:
                            logging.debug("ASCII:{}".format(txt))
                        if self.__rcvAutoCLRF == True or self.__rcvRecordTime == True:  # 接收自动换行
                            self.textBrowserReceive.insertPlainText("\r\n")
                    # else:
                    #     self.textBrowserReceive.append("\r\n---等待下次接收!---\r\n")
                    #     if debug == True:
                    #         logging.error("等待下次接收:{}".format(e))
            else:
            #  Hex接收模式
                # 将接收到的bytes数组buf的每个元素转换为两个Hex字符，并以空格连接成字符串strHexBuf，并在尾部添加一个额外的空格
                # hexBuf = ["{:02x}".format(i) for i in buf]
                # strHexBuf = ' '.join(hexBuf)+' '
                hexBuf = buf.hex()
                strHexBuf = ""
                for i in range(len(hexBuf)//2):
                    strHexBuf += hexBuf[i*2:i*2+2]
                    strHexBuf += " "

            # 将数据插入到文本浏览器中
                self.textBrowserReceive.insertPlainText(strHexBuf)
        else:
            if debug == True:
                logging.error("串口接收异常:应接收{},实际未读取到任何数据".format(count))

    def on_com_signalRcvError(self,txt):
        if debug == True:
            logging.error("串口异常关闭:{}".format(txt))
        #
        self.on_pushButtonOpen_toggled(False)
        # 更新串口列表
        self.__update_comboBoxPortList()

        pass
#     # 发送编辑区
#     self.textEditSend
    def on_textEditSend_textChanged(self):
        # 如果是Hex发送模式 使用正则过滤输入信息
        if self.__sndAsciiHex == False:
            currHex = self.textEditSend.toPlainText()
            # 对比当前内容与上次内容差别
            if self.__textEditSendLastHex != currHex:
                # 匹配所有16进制字符和空格
                patt = r"[0-9a-fA-F ]+"
                pattern = re.compile(patt)
                reObj = pattern.match(currHex)

                if reObj != None:
                    self.__textEditSendLastHex = reObj.group()
                    self.textEditSend.setText(self.__textEditSendLastHex)
                    self.textEditSend.moveCursor(self.textEditSend.textCursor().End)
                else:# 无效输入 清除输入区
                    # 必须先清除上次内容记录，然后调用self.textEditSend.clear()
                    # 因为调用此方法立即导致再次进入on_textEditSend_textChanged槽函数执行操作，如果未清除上次内容记录，对比后再次发现两次内容差别，执行模式匹配后，再次清除输入区，最后会产生无限循环
                    self.__textEditSendLastHex = ""
                    self.textEditSend.clear()
        # 字符串发送模式不限制数据
        else:
            pass

#     发送历史区
#     self.comboBoxSndHistory
#     def on_comboBoxSndHistory_currentIndexChanged(self, text):
        # self.textEditSend.setText(text)
        # self.textEditSend.moveCursor(self.textEditSend.textCursor().End)
    def on_comboBoxSndHistory_activated(self, text):
        if isinstance(text,str):
            self.textEditSend.setText(text)
            self.textEditSend.moveCursor(self.textEditSend.textCursor().End)

#     # 发送按钮
#     self.pushButtonSend
    def on_pushButtonSend_toggled(self,checked):
        if debug == True:
            logging.debug("pushButtonSend:Toggle{}".format(checked))
        if checked == True:
            # 判断串口状态
            if self.__com.getPortState() == True:
        #       查询发送区中是否有可用数据
                txt = self.textEditSend.toPlainText()
                if txt != "":
                    if debug == True:
                        logging.debug("原始发送数据:{}".format(txt))

                    # 添加到发送历史
                    self.comboBoxSndHistory.insertItem(0,txt)
                    self.comboBoxSndHistory.setCurrentIndex(0)
        #       判断当前发送模式时
                    if self.__sndAsciiHex == True:  # 发送ASCII模式
                        # 发送追加换行
                        if self.__sndAutoCLRF == True:
                            txt+="\r\n"

                        buf = txt.encode("utf-8")
                        if debug == True:
                            logging.debug("utf-8编码字节数组:{}".format(buf))

                        # 判断周期发送
                        if self.__txPeriodEnable == True:  # 周期发送使能
                            self.__periodSendBuf = buf
                            self.pushButtonSend.setText("停止")
                            threading.Thread(target=self.periodSendThread, args=(), daemon=True).start()

                        else:
                        # 单次发送  端口已被打开时开始发送
                            self.__com.send(buf)
                            self.__sndTotal+=len(buf)
                            self.__pushButtonSend_State_Reset()
                    else:
                        # Hex模式发送
                        try:
                            buf = bytes.fromhex(txt)
                            if debug == True:
                                logging.debug("16进制数据:{}".format(buf))

                            # 判断周期发送
                            if self.__txPeriodEnable == True:  # 周期发送使能
                                self.__periodSendBuf = buf
                                self.pushButtonSend.setText("停止")
                                threading.Thread(target=self.periodSendThread, args=(), daemon=True).start()
                            else:
                                # 单次发送  端口已被打开时开始发送
                                self.__com.send(buf)
                                self.__sndTotal += len(buf)
                                self.__pushButtonSend_State_Reset()
                        except Exception as e:
                            self.__pushButtonSend_State_Reset()
                            if debug == True:
                                logging.error("串口发送16进制转换失败:{}".format(e))
                            # 使用re模块从args中筛选出错误位置
                            patt = r"position (\d+)$"
                            patton = re.compile(patt)
                            reObj = patton.search(e.args[0])
                            # print("\treObj:{}".format(reObj))
                            if (reObj != None):
                                if reObj.lastindex > 0:
                                    errIndex = int(reObj.group(1))
                                    if debug == True:
                                        logging.error("\t出错位置:{}".format(errIndex))
                                    # 提示当前输入数据不符合Hex字符串格式要求
                                    reply = QMessageBox.question(self,'Hex字符串格式异常','第{}个字符不符合Hex字符串格式要求,请重新输入'.format(errIndex))
                else:
                    if debug == True:
                        logging.warning("发送区无有效数据")
                    self.__pushButtonSend_State_Reset()
            else:
                if debug == True:
                    logging.debug("串口未打开")
                self.__pushButtonSend_State_Reset()
        else:
            self.__pushButtonSend_State_Reset()

    def __pushButtonSend_State_Reset(self):
        self.pushButtonSend.setText("发送")
        self.pushButtonSend.setChecked(False)

    def periodSendThread(self):
        start =0
        stop =  0
        if self.__periodSendBuf != None:
            if debug == True:
                logging.debug("周期发送线程开启")

            while self.__txPeriodEnable and self.pushButtonSend.isChecked()==True and self.__com.getPortState() == True:
                # start = time.time()
                # print("睡眠时间:{}".format(start - stop))
                self.__com.send(self.__periodSendBuf)
                # stop =time.time()
                # print("发送时间:{}".format(stop-start))
                self.__sndTotal += len(self.__periodSendBuf)
                if debug == True:
                    logging.debug("周期发送:{}".format(self.__periodSendBuf))
                if self.__txPeriod > 0:
                    sleep(self.__txPeriod/1000)
            if debug == True:
                logging.debug("周期发送发送")

    def periodUpdateStatistics(self):
        while self.__com.getPortState() == True:
            sndSpeed = (self.__sndTotal-self.__sndTotalLast)//periodStatistics
            rcvSpeed = (self.__rcvTotal-self.__rcvTotalLast)//periodStatistics
            self.__rcvTotalValueLabel.setText("{:^d}".format(self.__rcvTotal))
            self.__rcvSpeedValueLabel.setText("{:^.0f}".format(rcvSpeed))
            self.__sndTotalValueLabel.setText("{:^d}".format(self.__sndTotal))
            self.__sndSpeedValueLabel.setText("{:^.0f}".format(sndSpeed))

            # 更新历史记录
            self.__sndTotalLast = self.__sndTotal
            self.__rcvTotalLast = self.__rcvTotal
            sleep(periodStatistics)

#     # 清除记录按钮
#     self.pushButtonClear
    def on_pushButtonClear_pressed(self):
        self.textBrowserReceive.clear()
        self.textEditSend.clear()
        self.__rcvTotal = 0
        self.__rcvTotalLast = 0
        self.__sndTotal = 0
        self.__sndTotalLast = 0

        if debug == True:
            logging.debug("清除接收区以及发送区")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = userMain()
    win.show()
    app.exec_()
