# !/usr/bin/env python
import sys
# import os
from time import sleep
import serial
from serial import Serial
from serial.serialutil import *
from serial.tools import list_ports
import threading
import copy
from PyQt5.QtCore import pyqtSignal,QObject

# 调试相关功能定义
import logging
# LOG_FORMAT = "%(asctime)s>%(levelname)s>%(process)d>%(processName)s>%(thread)d>%(thread)s>%(module)s>%(lineno)d>%(funcName)s>%(message)s"
# DATE_FORMAT = "%y-%m-%d %H:%M:%S,"
# DATE_FORMAT = "%y-%m-%d %H:%M:%S %p"
LOG_FORMAT = "%(asctime)s>%(levelname)s>PID:%(process)d %(thread)d>%(module)s>%(funcName)s>%(lineno)d>%(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, )
# logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, )

# 波特率列表
suportBandRateList = (300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 38400, 56000, 57600, 115200, 230400, 460800, 500000, 576000, 921600, 1000000, 1152000, 1500000, 2000000, 2500000, 3000000, 3500000, 4000000)

# 常量，系统特性
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

# 创建信号对象的类必须继承QObject
class userSerial(QObject):
    # 信号定义必须是类成员，而不是实例成员 即必须在类中直接定义，而不是在成员函数中定义
    signalRcv = pyqtSignal(int)
    # 初始化后必须通过open函数，
    def __init__(self, baudrate=9600, bytesize=Serial.BYTESIZES[-1], parity=Serial.PARITIES[0], stopbits=Serial.STOPBITS[0], timeout=None,writetimeout = None,  rtscts=False,xonxoff=False):#,dsrdtr=False
        # 实例化一个标准Serial对象
        super().__init__()
        self.port = Serial()
        logging.debug("初始化串口对象")
        
        # 定义接收相关的数据
        self.__RcvBuff = bytearray()
        self.__RcvBuffLock = threading.RLock()

        # 配置管理
        # 端口设置可以被读入字典，也可从字典加载设置：
        # d = self.port.getSettingsDict()#
        # self.port.applySettingsDict(d)#应用字典到串口设置
        # logging.debug(self.port.getSettingsDict())

        # 串口基础配置
        try:
            self.port.baudrate = baudrate
            self.port.bytesize = bytesize
            self.port.parity = parity
            self.port.stopbits =  stopbits
            # 超时配置
            self.port.timeout = timeout
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
            logging.error("初始化串口失败:{}".format(e))

        logging.debug("Read超时时间:{}".format(self.port.timeout))  # 读取 数据时超时时间
        # # None:阻塞，直到接收到期望字节数
        # # 0：非阻塞 立即返回
        # # n： 最多阻塞n秒 直到接收到期望字节数或者超时
        logging.debug("Write超时时间:{}".format(self.port.writeTimeout))  # 写超时时间
        # # 默认阻塞，除非修改write_timeout参数，参数不同数值含义和timeout一致
        logging.debug("Write超时时间:{}".format(self.port.interCharTimeout))  # 字符间超时时间))

        logging.debug("初始化结束，串口基本配置:{}".format(self.port.getSettingsDict()))
    # 获取端口列表
    @classmethod
    def getPortsList(cls):
        logging.debug("开始扫描可用串口:")
        portsList = []
        # 获取可用端口号
        ports = list(list_ports.comports())
        # 按字母顺序排序并遍历
        for i in sorted(ports):
            # logging.debug()(i)
            # logging.debug()(i.pid)
            # logging.debug()(i.device)
            # logging.debug()(i.manufacturer)
            # 提取端口号以及端口号名称
            # 将字符串中空格删除，并以第一个“-”做分隔，提取端口号及端口名称
            com, name = str(i).split('-',1)
            # 删除前后空格
            com = com.strip(" ")
            name = name.strip(" ")
            # 将端口号及名称添加到列表
            portsList.append((com,name))
        logging.debug("扫描结束,可用串口:{}".format(portsList))
        return portsList

    def open(self,port):
        try:
            if (self.port.isOpen() == False):
                self.port.setPort(port)
                self.port.open()
            else:
                logging.warning("{}-已被打开{}".format(port))
        except Exception as e:
            logging.warning("{}-无法打开{}".format(port,e))
            return False
        # 当端口已被打开时执行
        if (self.port.isOpen() ==True):
            logging.debug("{}-打开".format(1))
            # 必须在接口打开后访问
            # logging.debug()(self.port.getCTS())  # 获取CTS线状态
            # logging.debug()(self.port.name)  # 设备名称

            # 开启接收线程
            threading.Thread(target=self._recvHandle, args=(),daemon=True).start()
            logging.debug("开启接收线程")
        return True

    def close(self):
        if self.port.isOpen():
            self.port.close()
            logging.debug("{}-已关闭***********".format(self.port.name))
            self.__RcvBuffLock.acquire()
            self.__RcvBuff.clear()
            self.__RcvBuffLock.release()
        return

    def getPortState(self):
        return self.port.isOpen()

    def getRcvCount(self):
        if self.port.isOpen():
            self.__RcvBuffLock.acquire()
            count = len(self.__RcvBuff)
            self.__RcvBuffLock.release()
            return count
        else:
            return 0

    def getSndCount(self):
        if self.port.isOpen():
            return self.port.out_waiting
        else:
            return 0

    # 收发访问
    # read(size=1) return bytes
    # write(data)retrun written size    SerialTimeoutException 发送超时时引发异常
    # com.readline()  # 时需要注意超时
    def send(self,byte):
        if self.port.isOpen():
            try:
                logging.debug("Send成功:".format(byte))
                return self.port.write(bytes(byte))
            except SerialException as e:
                logging.error("Send失败-SerialException:{}".format(e))
            except Exception as e:
                logging.error("Send失败-Exception:{}".format(e))
            finally:
                return 0
        else:
            return 0

    def recv(self,count):
        # try:
        #     return self.port.read(count)
        # except portNotOpenError as e:
        #     logging.debug()(e)
        if len(self.__RcvBuff) >= count:
            self.__RcvBuffLock.acquire()
            buf = self.__RcvBuff[:count]
            self.__RcvBuff = self.__RcvBuff[count:]
            self.__RcvBuffLock.release()
        elif len(self.__RcvBuff):
            self.__RcvBuffLock.acquire()
            buf = copy.deepcopy(self.__RcvBuff)
            self.__RcvBuff.clear()
            self.__RcvBuffLock.release()
        else:
            buf = None
        return buf

    def _recvHandle(self):
        logging.debug("接收线程已启动")
        while (self.port.isOpen()):
            try:
                count = self.port.in_waiting
                if count > 0:
                    self.__RcvBuffLock.acquire()
                    rcv = self.port.read(count)
                    self.__RcvBuff += rcv
                    self.__RcvBuffLock.release()

                    logging.debug("成功接收:{}".format(count))
                    logging.debug(("RcvHEX:", " ".join(["{:02X}".format(i) for i in rcv])))
                    try:
                        asciiRcv = rcv.decode("utf-8")
                        logging.debug("Rcv字符:{}".format(asciiRcv))
                    except Exception as e:
                        logging.debug("Rcv字符:utf-8解码失败")

                # 发送当前接收到的数据量
                    self.signalRcv.emit(self.getRcvCount())
            except SerialException as e:
                logging.error("Recv失败-SerialException:{}".format(e))
            except Exception as e:
                logging.error("Recv失败-Exception:{}".format(e))
            finally:
                pass
            # 睡眠10ms
            sleep(0.01)
        logging.debug("端口关闭，接收线程已结束")

    def flush(self):
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
                logging.error("Flush成功")
        except SerialException as e:
            logging.error("Recv失败-SerialException:{}".format(e))
        except Exception as e:
            logging.error("Recv失败-Exception:{}".format(e))
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

        logging.debug("接收完成")
        com.close()
        logging.debug("{}:已关闭".format(currPort))
    else:
        logging.debug("{}:未打开".format(currPort))