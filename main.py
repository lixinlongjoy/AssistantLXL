import time
import os
import re
import logging

from PyQt5 import QtCore,QtGui
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QApplication,QDialog,QMainWindow

from comSerialWidget import  Ui_Form
from userSerial import *

# 调试相关功能定义
# LOG_FORMAT = "%(asctime)s>%(levelname)s>%(process)d>%(processName)s>%(thread)d>%(thread)s>%(module)s>%(lineno)d>%(funcName)s>%(message)s"
# DATE_FORMAT = "%y-%m-%d %H:%M:%S,"
# DATE_FORMAT = "%y-%m-%d %H:%M:%S %p"
LOG_FORMAT = "%(asctime)s>%(levelname)s>PID:%(process)d %(thread)d>%(module)s>%(funcName)s>%(lineno)d>%(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, )
# logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, )

class userMain(QMainWindow,Ui_Form):
# class userMain(QMainWindow, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        logging.debug("初始化主程序:")
        # 初始化串口对象
        self.__comBoxPortBuf = ""#当前使用的串口号
        self.comPortList = []#系统可用串口号
        self.com = userSerial(baudrate=115200, timeout=0)
        self.__update_comboBoxPortList()#更新串口设备
        # 非PyQt控件无法支持自动信号与槽函数连接，必须手动进行
        self.com.signalRcv.connect(self.on_com_signalRcv)

        # 更新波特率
        self.__update_comboBoxBandRateList()

        self.__rcvAsciiHex = True#接收ASCII模式
        self.__sndAsciiHex = True#发送ASCII模式
        self.__rcvRecordTime = False#接收记录时间
        self.__rcvAutoCLRF = False#接收自动换行
        self.__sndAutoCLRF = False#发送追加换行
        self.__txPeriodEnable = False#周期发送使能
        # 设置lineEditPeriod的输入有效范围
        self.lineEditPeriodMs.setValidator(QIntValidator(0,99999999))
        self.__txPeriod = int(self.lineEditPeriodMs.text())#周期长度ms

        # 设置发送区字符有效输入范围
        # 正则表达式限制
        # r"^-?(90|[1-8]?\d(\.\d{1,4})?)$"  匹配-90至90之间，小数点后一至四位小数的输入限制
        # r(^-?180$)|(^-?1[0-7]\d$)|(^-?[1-9]\d$)|(^-?[1-9]$)|^0$");
        # self.textEditSend.setValidator(QIntValidator(0,99999999))
        self.textEditSendLastTxt = self.textEditSend.toPlainText()

        logging.debug("当前系统可用端口:{}".format(self.comPortList))
        logging.debug("初始化主程序完成")

# 串口配置相关
    def __update_comboBoxPortList(self):
        # 获取可用串口号列表
        newportlistbuf = userSerial.getPortsList()
        if self.__comBoxPortBuf == "" or  newportlistbuf != self.comPortList:
            self.comPortList = newportlistbuf
            # 初始化上次使用的串口号信息
            if self.__comBoxPortBuf =="":
                self.__comBoxPortBuf = self.comPortList[0][1]

            if len(self.comPortList) > 0:
                # 将串口号列表更新
                self.comboBoxPort.setEnabled(False)
                self.comboBoxPort.clear()
                self.comboBoxPort.addItems([self.comPortList[i][1] for i in range(len(self.comPortList))])

                seq = 0
                for i in self.comPortList:
                    if i[1] == self.__comBoxPortBuf:
                        self.comboBoxPort.setCurrentIndex(seq)
                        break
                    seq+=1

                self.comboBoxPort.setEnabled(True)
                logging.debug("更新可用串口列表")
            else:
                self.comboBoxPort.setEnabled(False)
                self.comboBoxPort.clear()
                self.__comBoxPortBuf = ""
                self.comboBoxPort.addItem("无可用串口设备")
                logging.warning("更新可用串口列表：无可用串口设备")
        else:
            logging.debug("更新可用串口列表：列表未发生变化")

    # self.comboBoxPort.activated[str].connect(self.onActivated)
    # self.comboBoxPort.enterEventSignal.connect(self.on_comboBoxPort_enterEventSignal)
    # def on_comboBoxPort_activated(self,text):#选中组合框中任意一个项目时触发
    def on_comboBoxPort_currentIndexChanged(self, text):#选中组合框中与当前不同的项目时触发
        if isinstance(text,int):
            logging.debug("更换选中串口号:{}".format(text))
        if isinstance(text,str):
            logging.debug("更换选中串口名称:{}".format(text))
            if(text != ""):
                # 切换串口前，如果当前为已打开端口则关闭端口
                if self.com.getPortState() == True:
                    self.on_pushButtonOpen_toggled(False)
                self.__comBoxPortBuf = text
    # 鼠标移入控件事件
    def on_comboBoxPort_enterEventSignal(self):
        self.__update_comboBoxPortList()
        logging.debug("鼠标移入comboBoxPort控件，即将更新串口列表")

    # 波特率
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
    def on_comboBoxBand_currentIndexChanged(self,text):
        # if isinstance(text,str):
        #         if text.isalnum():
        try:
            self.com.port.baudrate = (int(text))
            logging.debug("更新波特率:{}".format(self.com.port.baudrate))
        except Exception as e:
            logging.error("更新波特率:{}".format(e))

    # # 数据位
    def _update_radioButtonDataBit(self,bit,checked):
        if checked == True:
            try:
                self.com.port.bytesize = bit
                logging.debug("更新数据位:{}".format(self.com.port.bytesize))
            except Exception as e:
                logging.error("更新数据位:{}".format(e))
        else:
            try:
                logging.debug("取消此数据位:{}".format(self.com.port.bytesize))
            except Exception as e:
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
                self.com.port.parity = parity
                logging.debug("更新校验:{}".format(self.com.port.parity))
            except Exception as e:
                logging.error("更新校验:{}".format(e))
        else:
            try:
                logging.debug("取消此校验:{}".format(self.com.port.parity))
            except Exception as e:
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
    #     print("流控stateChanged",checked)
    def on_checkBoxFlowCtrl_toggled(self,checked):
        try:
            self.com.port.rtscts = checked
            logging.debug("更新流控开关:{}".format(self.com.port.rtscts))
        except Exception as e:
            logging.error("更新流控开关失败:{}".format(e))

    # # 停止位
    def _update_radioButtonStop(self,stop,checked):
        if checked == True:
            try:
                self.com.port.stopbits = stop
                logging.debug("更新停止位:{}".format(self.com.port.stopbits))
            except Exception as e:
                logging.error("更新停止位:{}".format(e))
        else:
            try:
                logging.debug("取消此停止位:{}".format(self.com.port.stopbits))
            except Exception as e:
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
    #     print("pushButtonOpen:pressed")
    def on_pushButtonOpen_toggled(self,checked):
        logging.debug("pushButtonOpen:Toggle{}".format(checked))
        if checked ==True:
        #  打开指定串口
            portBuf = ""
            seq = 0
            for i in self.comPortList:
                if i[1] == self.__comBoxPortBuf:
                    portBuf  = i[0]
                    break
                seq+=1
            if (portBuf != ""):
                try:
                    if True == self.com.open(portBuf):
                        logging.debug("端口{}已打开".format(portBuf))
                        self.pushButtonOpen.setText("关闭")

                        # 在userSerial类中已经实现了接收完成signalRcv信号机制，无需启动线程刷屏，只需将信号关联到对应的槽函数即可
                        # # 开启接收线程刷屏
                        # threading.Thread(target=self.__textBrowserReceiveRefresh, args=(), daemon=True).start()
                    else:
                        logging.warning("端口{}未成功打开".format(portBuf))
                        self.__pushButtonOpen_State_Reset()
                except Exception as e:
                    logging.error("端口{}打开出错".format(e))
            else:
                logging.debug("无可用串口")
                self.__pushButtonOpen_State_Reset()
        else:
        #  关闭当前打开的串口
            if self.com.getPortState() == True:
                self.com.port.close()
                logging.debug("端口{}已关闭".format(self.__comBoxPortBuf))
            self.__pushButtonOpen_State_Reset()

    def __pushButtonOpen_State_Reset(self):
        self.pushButtonOpen.setText("打开")
        self.pushButtonOpen.setChecked(False)


# 串口接收设置
#     # ASCII接收显示
# #     self.radioButtonRxAscii
    def on_radioButtonRxAscii_toggled(self,checked):
        if checked == True:
            self.__rcvAsciiHex = True
            self.checkBoxRxRecordTime.setEnabled(True)
            self.checkBoxRxAutoCLRF.setEnabled(not self.__rcvRecordTime)
            logging.debug("更新接收模式:ASCII")
        else:
            logging.debug("取消接收模式:ASCII")

#     # 记录时间
#     self.checkBoxRxRecordTime
    def on_checkBoxRxRecordTime_toggled(self,checked):
        self.__rcvRecordTime = checked
        # 如果选择记录时间，则禁止接收自动换行的配置
        self.checkBoxRxAutoCLRF.setEnabled(not checked)
        # 选择接收记录时间则在文本浏览器中追加行 便于格式对齐
        if checked == True:
            self.textBrowserReceive.append("")
        logging.debug("更新记录接收时间:{}".format(checked))
#     # 自动换行
#     self.checkBoxRxAutoCLRF
    def on_checkBoxRxAutoCLRF_toggled(self,checked):
        self.__rcvAutoCLRF = checked
        # 选择接收自动换行则在文本浏览器中追加行 便于格式对齐
        if checked == True:
            self.textBrowserReceive.append("")
        logging.debug("更新接收自动换行:{}".format(checked))

#     # Hex接收显示
#     self.radioButtonRxHex
    def on_radioButtonRxHex_toggled(self,checked):
        if checked == True:
            self.__rcvAsciiHex = False
            # Hex接收时将记录时间和自动换行禁止
            self.checkBoxRxRecordTime.setEnabled(False)
            self.checkBoxRxAutoCLRF.setEnabled(False)
            logging.debug("更新接收模式:Hex")
        else:
            logging.debug("取消接收模式:Hex")


# 串口发送设置
#     # ASCII发送
#     self.radioButtonTxAscii
    def on_radioButtonTxAscii_toggled(self,checked):
        if checked == True:
            self.__sndAsciiHex = True
            # 设置自动换行使能
            self.checkBoxTxAutoCRLF.setEnabled(True)
            logging.debug("更新发送模式:ASCII")
        else:
            logging.debug("取消发送模式:ASCII")
#     # ASCII发送时自动追加回车换行
#     self.checkBoxTxAutoCRLF
    def on_checkBoxTxAutoCRLF_toggled(self,checked):
        self.__sndAutoCLRF = checked
        logging.debug("更新发送自动换行:{}".format(checked))
#     # Hex发送
#     self.radioButtonTxHex
    def on_radioButtonTxHex_toggled(self,checked):
        if checked == True:
            self.__sndAsciiHex = False
            # 设置自动换行禁能
            self.checkBoxTxAutoCRLF.setEnabled(False)
            logging.debug("更新发送模式:Hex")
        else:
            logging.debug("取消发送模式:Hex")
#     # 周期发送使能
#     self.checkBoxTxPeriodEnable
    def on_checkBoxTxPeriodEnable_toggled(self,checked):
        self.__txPeriodEnable = checked
        logging.debug("更新周期发送设置:{}".format(checked))
#     # 发送周期
#     self.lineEditPeriodMs
    def on_lineEditPeriodMs_textChanged(self,text):
        if(text != ""  and  text  != "0"):
            self.lineEditPeriodMs.setText((self.lineEditPeriodMs.text().lstrip('0')))
            self.__txPeriod = int(text)
        else:
            self.lineEditPeriodMs.setText("0")
        logging.debug("更新周期发送时间设置:{} {}".format(text,self.__txPeriod))


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
        logging.debug("串口接收:{}".format(count))

        buf = self.com.recv(count)
        if buf != None:
            logging.debug("原始数据:{}".format(buf))
            # 判断接收模式
            if self.__rcvAsciiHex == True:
            # ASCII接收模式
                if self.__rcvRecordTime == True:  # 接收记录时间
                    currTime = time.time()
                    mSec = int(1000*(currTime-int(currTime)))
                    self.textBrowserReceive.insertPlainText("{}.{:03d}: ".format(time.strftime("%H:%M:%S"),mSec))
                try:
                    buf = buf.decode("utf-8")
                    self.textBrowserReceive.insertPlainText(buf)
                    logging.debug("ASCII:{}".format(buf))
                    if self.__rcvAutoCLRF == True or self.__rcvRecordTime == True:  # 接收自动换行
                        self.textBrowserReceive.insertPlainText("\r\n")
                except Exception as e:
                    self.textBrowserReceive.append("\r\n---解码失败!---\r\n")
                    logging.error("串口接收解码解码失败:{}".format(e))
                    # 使用re模块从args中筛选出错误位置
                    patt = r"position (\d+)$"
                    patton = re.compile(patt)
                    reObj = patton.search(e.args[0])
                    # print("\treObj:{}".format(reObj))
                    if (reObj != None):
                        if reObj.lastindex != None:
                            for i in range(reObj.lastindex + 1):
                                logging.error("\t出错位置:{}".format(i, reObj.group(i)))
            else:
            #  Hex接收模式
                # 将接收到的bytes数组buf的每个元素转换为两个Hex字符，并以空格连接成字符串strHexBuf，并在尾部添加一个额外的空格
                hexBuf = ["{:02x}".format(i) for i in buf]
                strHexBuf = ' '.join(hexBuf)+' '
                # 将数据插入到文本浏览器中
                self.textBrowserReceive.insertPlainText(strHexBuf)
        else:
            logging.error("串口接收异常:应接收{},实际未读取到任何数据".format(count))

#     # 发送编辑区
#     self.textEditSend

    def on_textEditSend_textChanged(self):
        txt = self.textEditSend.toPlainText()
        if self.textEditSendLastTxt != txt:
            print(txt)
            patt = r"[0-9a-fA-F ]+"
            pattern = re.compile(patt)
            reObj = pattern.match(txt)
            print(reObj)

            if reObj != None:
                self.textEditSendLastTxt = reObj.group()
                if txt != self.textEditSendLastTxt:
                    self.textEditSend.setText(self.textEditSendLastTxt)
                    self.textEditSend.moveCursor(self.textEditSend.textCursor().End)
            else:
                self.textEditSend.clear()
                self.textEditSendLastTxt = ""
        # else:
        #     print("未发生改变")
#     发送历史区
#     self.comboBoxSndHistory

#     # 发送按钮
#     self.pushButtonSend
    def on_pushButtonSend_pressed(self):
#       查询发送区中是否有可用数据
        txt = self.textEditSend.toPlainText()
        if txt != "":
#       判断当前发送模式时
            logging.debug("原始发送数据:{}".format(txt))
            if self.__sndAsciiHex == True:  # 发送ASCII模式
                # 发送追加换行
                if self.__sndAutoCLRF == True:
                    txt+="\r\n"
                # 判断周期发送
                if self.__txPeriodEnable == True:  # 周期发送使能
                    logging.debug("启动定时器，以{}时间间隔发送".format(self.__txPeriod))
                else:
                #     单次发送  端口已被打开时开始发送
                    if self.com.getPortState() ==True:
                        buf = txt.encode("utf-8")
                        self.com.send(buf)
                        logging.debug("ASCII:{}".format(buf))
            else:
                # Hex模式发送
                try:
                    buf = bytes.fromhex(txt)
                    logging.debug("Hex:{}".format("abc"))

                    if self.com.getPortState() ==True:
                        self.com.send(buf)
                        logging.debug("ASCII:{}".format(buf))

                except Exception as e:
                    logging.error("串口发送编码失败:{}".format(e))
                    # 使用re模块从args中筛选出错误位置
                    patt = r"position (\d+)$"
                    patton = re.compile(patt)
                    reObj = patton.search(e.args[0])
                    # print("\treObj:{}".format(reObj))
                    if (reObj != None):
                        if reObj.lastindex != None:
                            for i in range(reObj.lastindex + 1):
                                logging.error("\t出错位置:{}".format(reObj.group(i)))
        else:
            logging.warning("发送区无有效数据")
#     # 清除记录按钮
#     self.pushButtonClear
    def on_pushButtonClear_pressed(self):
        self.textBrowserReceive.clear()
        self.textEditSend.clear()
        logging.debug("清除接收区以及发送区")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = userMain()
    win.show()
    app.exec_()
