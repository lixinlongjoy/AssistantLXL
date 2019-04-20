# !/usr/bin/env python
import sys
from time import sleep
import copy

import serial
from serial import Serial
from serial.serialutil import *
from serial.tools import list_ports

import threading

from PyQt5.QtCore import pyqtSignal,QObject

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
# 接收线程中轮询周期 单位秒
rcvPeriod = 0.01
# 波特率列表
suportBandRateList = (300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 56000, 57600, 115200, 230400, 460800, 500000, 576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000)

# 常量，系统特性
if debug == True:
    logging.debug("pyserial版本:{}".format(serial.VERSION))#pyserial版本
    logging.debug("可用波特率:{}".format(suportBandRateList))
    # logging.debug(""(serial.device(0))#串口号与设备名称转换 0--COM1 1-COM2
    # logging.debug("可用波特率:{}".format(Serial.BAUDRATES))
    logging.debug("可用数据位:{}".format(Serial.BAUDRATES))
    logging.debug("可用校验类型:{}".format(Serial.PARITIES))
    logging.debug("可用停止位:{}".format(Serial.STOPBITS))

# 模块函数和属性：
# serial.serial_for_url(url, *args, **kwargs)
# serial.protocol_handler_packages()
# 异常：
# serial.SerialException 基类串口异常 设备无法被发现或者无法被配置
# serial.SerialTimeoutException
# ValueError法配置参数
# TypeError

class userSerial(QObject):
    """
    userSerial类封装了一个serial对象，并对serial对象进行了优化处理
    当接收到数据时触发signalRcv
    当接收异常时触发signalRcvError

    示例
        import userSerial

        sndBuf = bytes(1,2,3,4,5,6)
        com = userSerial(bandrate=9600)
        com.open("com1")
        com.send(sndBuf)
        rcvBuf = com.recv(n)
        com.close()
    """

    # 定义接收信号 当接收到数据时发射此信号
    signalRcv = pyqtSignal(int)
    # 定义接收异常信号 当接收到数据时发射此信号
    signalRcvError = pyqtSignal(str)
    def __init__(self, baudrate=9600, bytesize=Serial.BYTESIZES[-1], parity=Serial.PARITIES[0], stopbits=Serial.STOPBITS[0], timeout=None,writetimeout = None,  rtscts=False,xonxoff=False):#,dsrdtr=False
        """
        初始化
        :param baudrate:
        :param bytesize:
        :param parity:
        :param stopbits:
        :param timeout:
        :param writetimeout:
        :param rtscts:
        :param xonxoff:
        """
        # 实例化一个标准Serial对象
        super().__init__()
        self.port = Serial()
        if debug == True:
            logging.debug("初始化串口对象")
        
        # 定义接收相关的数据
        self.__RcvBuff = bytearray()#接收缓存
        self.__RcvBuffLock = threading.RLock()#接收缓存访问递归锁

        # 配置管理
        # 端口设置可以被读入字典，也可从字典加载设置：
        # d = self.port.getSettingsDict()#
        # self.port.applySettingsDict(d)#应用字典到串口设置
        # if debug == True:
        #     logging.debug(self.port.getSettingsDict())

        # 串口基本配置
        try:
            self.port.baudrate = baudrate
            self.port.bytesize = bytesize
            self.port.parity = parity
            self.port.stopbits =  stopbits
            # 超时配置
            # # None:阻塞，直到接收到期望字节数
            # # 0：非阻塞 立即返回
            # # n： 最多阻塞n秒 直到接收到期望字节数或者超时
            self.port.timeout = timeout
            # # 默认阻塞，除非修改write_timeout参数，参数不同数值含义和timeout一致
            self.port.writeTimeout = writetimeout
            # 流控配置
            # 不支持同时开启XONXOff和RTSCTS
            self.port.rtscts = rtscts
            # self.port.setRTS(0)  # 获取/设置 RTS线状态  可以在Open串口之前先设置
            if rtscts == True:
                self.port.xonxoff = False
            else:
                self.port.xonxoff = xonxoff
        except Exception as e:
            if debug == True:
                logging.error("初始化串口失败:{}".format(e))
            raise Exception(e)

        if debug == True:
            logging.debug("Read超时时间:{}".format(self.port.timeout))  # 读取 数据时超时时间
            logging.debug("Write超时时间:{}".format(self.port.writeTimeout))  # 写超时时间
            logging.debug("Write超时时间:{}".format(self.port.interCharTimeout))  # 字符间超时时间))
            logging.debug("初始化结束，串口基本配置:{}".format(self.port.getSettingsDict()))

    @classmethod
    def getPortsList(cls):
        """
        获取系统端口列表

        :return:可用端口列表
        """
        if debug == True:
            logging.debug("开始扫描可用串口:")
        portsList = []
        # 获取可用端口号
        ports = list(list_ports.comports())
        # 按字母顺序排序并遍历
        for i in sorted(ports):
            # if debug == True:
            #     logging.debug()(i)
            #     logging.debug()(i.pid)
            #     logging.debug()(i.device)
            #     logging.debug()(i.manufacturer)
            # 提取端口号以及端口号名称
            # 将字符串中空格删除，并以第一个“-”做分隔，提取端口号及端口名称
            com, name = str(i).split('-',1)
            # 删除前后空格
            com = com.strip(" ")
            name = name.strip(" ")
            # 将端口号及名称添加到列表
            portsList.append((com,name))
        if debug == True:
            logging.debug("扫描结束,可用串口:{}".format(portsList))
        return portsList

    def open(self,port):
        """
        打开串口 成功打开后开启接收线程

        :param port:com1 com2等类似名称
        :return:
        """
        try:
            if (self.port.isOpen() == False):
                self.port.setPort(port)
                self.port.open()
            else:
                if debug == True:
                    logging.warning("{}-已被打开{}".format(port))
        except Exception as e:
            if debug == True:
                logging.warning("{}-无法打开{}".format(port,e))
            raise Exception(e)
        # 当端口已被打开时执行
        if (self.port.isOpen() ==True):
            if debug == True:
                logging.debug("{}-打开".format(1))
                # 必须在接口打开后访问
                # logging.debug()(self.port.getCTS())  # 获取CTS线状态
                # logging.debug()(self.port.name)  # 设备名称
            # 清除缓冲区
            self.__RcvBuffLock.acquire()
            self.__RcvBuff.clear()
            self.__RcvBuffLock.release()
            # 开启接收线程
            threading.Thread(target=self._recvHandle, args=(),daemon=True).start()
            if debug == True:
                logging.debug("开启接收线程")

    def close(self):
        """
        关闭串口
        :return:
        """
        if self.port.isOpen():
            self.port.close()
            if debug == True:
                logging.debug("{}-已关闭***********".format(self.port.name))
            self.__RcvBuffLock.acquire()
            self.__RcvBuff.clear()
            self.__RcvBuffLock.release()
        return


    def getPortState(self):
        """
        获取端口状态
        :return: True if port is open
                False if port is close
        """
        return self.port.isOpen()

    def getRcvCount(self):
        """
        获取已接收数据量 可用于轮询模式

        """

        if self.port.isOpen():
            self.__RcvBuffLock.acquire()
            count = len(self.__RcvBuff)
            self.__RcvBuffLock.release()
            return count
        else:
            return 0

    def getSndCount(self):
        """
        获取待发送数据量
        """

        if self.port.isOpen():
            return self.port.out_waiting
        else:
            return 0

    # write(data)retrun written size    SerialTimeoutException 发送超时时引发异常
    def send(self, bytesBuf):
        """
        发送函数
        """
        if self.port.isOpen():
            try:
                sndOkCnt = self.port.write(bytes(bytesBuf))
                # 打印发送数据 bytes类型
                if debug == True:
                    logging.debug("Send:{} {}".format(sndOkCnt, bytesBuf))
                return
            except SerialTimeoutException as e:
                if debug == True:
                    logging.error("Send失败-SerialTimeoutException:{}".format(e))
            except SerialException as e:
                if debug == True:
                    logging.error("Send失败-SerialException:{}".format(e))
            except Exception as e:
                if debug == True:
                    logging.error("Send失败-Exception:{}".format(e))
            finally:
                return 0
        else:
            return 0

    def recv(self,count):
        """
        接收函数
        从本地缓冲中读取数据（并非直接从串口缓冲中取数）
        bytesBuf = userSerial.recv(cnt)
        count:期望读取的数据量
            当count<=当前缓冲中数量时，len(bytesBuf) = cnt
            当count> 当前缓冲中数量时，len(bytesBuf) = len(缓冲)
        return:是bytes型对象
        """
        if len(self.__RcvBuff) >= count:
            # 截取部分缓冲中数据
            self.__RcvBuffLock.acquire()
            buf = self.__RcvBuff[:count]
            self.__RcvBuff = self.__RcvBuff[count:]
            self.__RcvBuffLock.release()
        elif len(self.__RcvBuff):
            # 将全部缓冲中数据返回
            self.__RcvBuffLock.acquire()
            buf = copy.deepcopy(self.__RcvBuff)
            self.__RcvBuff.clear()
            self.__RcvBuffLock.release()
        else:
            buf = None
        return buf

    # read(size=1) return bytes
    # com.readline()  # 时需要注意超时
    def _recvHandle(self):
        """
        接收线程
            用于将周期性查询串口设备接收状态并将硬件串口设备接收到的数据转存到本地接收缓冲self.__RcvBuff中
            此线程函数在打开串口时启动
        :return:
        """

        start = 0
        stop = 0
        if debug == True:
            logging.debug("接收线程已启动")
        while (self.port.isOpen()):
            try:
                count = self.port.in_waiting
                if count > 0:
                    self.__RcvBuffLock.acquire()
                    rcv = self.port.read(count)
                    self.__RcvBuff += rcv
                    self.__RcvBuffLock.release()

                    if debug == True:
                        # 以16进制形式打印接收到的数据
                        logging.debug("RcvHEX:{}B,Data:{}".format(count, " ".join(["{:02X}".format(i) for i in rcv])))
                    # # 尝试utf-8解码
                    # try:
                    #     asciiRcv = rcv.decode("utf-8")
                    #     if debug == True:
                    #         # 解码成功则以字符形式打印接收到的数据
                    #         logging.debug("Rcv字符:{}".format(asciiRcv))
                    # except Exception as e:
                    #     if debug == True:
                    #         logging.debug("Rcv字符:utf-8解码失败")

                # 发送当前接收到的数据量
                    self.signalRcv.emit(self.getRcvCount())
            except SerialException as e:
                self.signalRcvError.emit(e.args[0])
                if debug == True:
                    logging.error("Recv失败-SerialException:{}".format(e))
                self.close()
            except Exception as e:
                self.signalRcvError.emit(e.args[0])
                if debug == True:
                    logging.error("Recv失败-Exception:{}".format(e))
                self.close()
            finally:
                pass
            # 睡眠
            sleep(rcvPeriod)
        if debug == True:
            logging.debug("端口关闭，接收线程已结束")

    def flush(self):
        """
        清除串口缓冲区
        :return:
        """
        try:
            if self.port.isOpen():
                # 缓冲管理
                self.port.flush()
                # self.port.flushInput()  # 丢弃接收缓存中的所有数据
                # self.port.flushOutput()  # 终止当前写操作，并丢弃发送缓存中的数据。
                # self.port.reset_input_buffer()
                # self.port.reset_output_buffer()

                # 清除接收缓存
                self.__RcvBuffLock.acquire()
                self.__RcvBuff.clear()
                self.__RcvBuffLock.release()
                if debug == True:
                    logging.error("flush成功")
        except SerialException as e:
            if debug == True:
                logging.error("flush-SerialException:{}".format(e))
        except Exception as e:
            if debug == True:
                logging.error("flush-Exception:{}".format(e))
        finally:
            pass

if __name__ == "__main__":
    com = userSerial(baudrate = 115200,timeout = 0)
    comPortList = userSerial.getPortsList()
    currPort = comPortList[1][0]
    com.open(currPort)
    if(com.getPortState()):
        logging.debug("{}:已打开".format(currPort))
        com.send(bytearray((1,2,3,4,5,6,7,8,9,0)))
        sleep(1)
        logging.debug("Wait for Rcv:")
        cnt = 0
        while(True):
            if com.getRcvCount()>0:
                cnt = 0
                rcvdat = com.recv(com.getRcvCount())
                logging.debug("RcvByteArray:{}".format(rcvdat))
                logging.debug("RcvHex:{}".format(rcvdat.hex()))
                try:
                    asciiRcv = rcvdat.decode("utf-8")
                    logging.debug("Rcv字符:{}".format(asciiRcv))
                    if asciiRcv == "exit":
                        break
                except Exception as e:
                    logging.debug("Rcv是非utf-8")
            else:
                cnt+=1
                if cnt >30:
                    logging.debug("Rcving:")
                    cnt = 0

            sleep(0.1)

        com.close()

        logging.debug("接收完成")
        logging.debug("{}:已关闭".format(currPort))
    else:
        logging.debug("{}:未打开".format(currPort))
