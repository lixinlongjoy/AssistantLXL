# 本节开始问题提到过，一条日志信息对应的是一个事件的发生，而一个事件通常需要包括以下几个内容：
#     事件发生时间
#     事件发生位置
#     事件的严重程度--日志级别
#     事件内容
#
# 上面这些都是一条日志记录中可能包含的字段信息，当然还可以包括一些其他信息，如进程ID、进程名称、线程ID、线程名称等。日志格式就是用来定义一条日志记录中包含那些字段的，且日志格式通常都是可以自定义的。
# 2. logging模块的使用方式介绍
#
# logging模块提供了两种记录日志的方式：
#
#     第一种方式是使用logging提供的模块级别的函数
#     第二种方式是使用Logging日志系统的四大组件
#
# 其实，logging所提供的模块级别的日志记录函数也是对logging日志系统相关类的封装而已。
# logging模块定义的模块级别的常用函数
# 函数 	说明
# logging.debug(msg, *args, **kwargs) 	创建一条严重级别为DEBUG的日志记录
# logging.info(msg, *args, **kwargs) 	创建一条严重级别为INFO的日志记录
# logging.warning(msg, *args, **kwargs) 	创建一条严重级别为WARNING的日志记录
# logging.error(msg, *args, **kwargs) 	创建一条严重级别为ERROR的日志记录
# logging.critical(msg, *args, **kwargs) 	创建一条严重级别为CRITICAL的日志记录
# logging.log(level, *args, **kwargs) 	创建一条严重级别为level的日志记录
# logging.basicConfig(**kwargs) 	对root logger进行一次性配置
#
# 其中logging.basicConfig(**kwargs)函数用于指定“要记录的日志级别”、“日志格式”、“日志输出位置”、“日志文件的打开模式”等信息，其他几个都是用于记录各个级别日志的函数。
# logging模块的四大组件
# 组件 	说明
# loggers 	提供应用程序代码直接使用的接口
# handlers 	用于将日志记录发送到指定的目的位置
# filters 	提供更细粒度的日志过滤功能，用于决定哪些日志记录将会被输出（其它的日志记录将会被忽略）
# formatters 	用于控制日志信息的最终输出格式
#
#     说明： logging模块提供的模块级别的那些函数实际上也是通过这几个组件的相关实现类来记录日志的，只是在创建这些类的实例时设置了一些默认值。

# 只有级别大于或等于日志记录器指定级别的日志记录才会被输出，小于该级别的日志记录将会被丢弃。



# 3. logging.basicConfig()函数说明
#
# 该方法用于为logging日志系统做一些基本配置，方法定义如下：
#
# logging.basicConfig(**kwargs)
#
# 该函数可接收的关键字参数如下：
# 参数名称 	描述
# filename 	指定日志输出目标文件的文件名，指定该设置项后日志信心就不会被输出到控制台了
# filemode 	指定日志文件的打开模式，默认为'a'。需要注意的是，该选项要在filename指定时才有效
# format 	指定日志格式字符串，即指定日志输出时所包含的字段信息以及它们的顺序。logging模块定义的格式字段下面会列出。
# datefmt 	指定日期/时间格式。需要注意的是，该选项要在format中包含时间字段%(asctime)s时才有效
# level 	指定日志器的日志级别
# stream 	指定日志输出目标stream，如sys.stdout、sys.stderr以及网络stream。需要说明的是，stream和filename不能同时提供，否则会引发 ValueError异常
# style 	Python 3.2中新添加的配置项。指定format格式字符串的风格，可取值为'%'、'{'和'$'，默认为'%'
# handlers 	Python 3.3中新添加的配置项。该选项如果被指定，它应该是一个创建了多个Handler的可迭代对象，这些handler将会被添加到root logger。需要说明的是：filename、stream和handlers这三个配置项只能有一个存在，不能同时出现2个或3个，否则会引发ValueError异常。
# 4. logging模块定义的格式字符串字段
#
# 我们来列举一下logging模块中定义好的可以用于format格式字符串中字段有哪些：
# 字段/属性名称 	使用格式 	描述
# asctime 	%(asctime)s 	日志事件发生的时间--人类可读时间，如：2003-07-08 16:49:45,896
# created 	%(created)f 	日志事件发生的时间--时间戳，就是当时调用time.time()函数返回的值
# relativeCreated 	%(relativeCreated)d 	日志事件发生的时间相对于logging模块加载时间的相对毫秒数（目前还不知道干嘛用的）
# msecs 	%(msecs)d 	日志事件发生事件的毫秒部分
# levelname 	%(levelname)s 	该日志记录的文字形式的日志级别（'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'）
# levelno 	%(levelno)s 	该日志记录的数字形式的日志级别（10, 20, 30, 40, 50）
# name 	%(name)s 	所使用的日志器名称，默认是'root'，因为默认使用的是 rootLogger
# message 	%(message)s 	日志记录的文本内容，通过 msg % args计算得到的
# pathname 	%(pathname)s 	调用日志记录函数的源码文件的全路径
# filename 	%(filename)s 	pathname的文件名部分，包含文件后缀
# module 	%(module)s 	filename的名称部分，不包含后缀
# lineno 	%(lineno)d 	调用日志记录函数的源代码所在的行号
# funcName 	%(funcName)s 	调用日志记录函数的函数名
# process 	%(process)d 	进程ID
# processName 	%(processName)s 	进程名称，Python 3.1新增
# thread 	%(thread)d 	线程ID
# threadName 	%(thread)s 	线程名称
if __name__ == "__main__":
    import logging
    import sys
    LOG_FORMAT = "%(asctime)s>%(levelname)s>%(process)d>>%(processName)s>%(thread)d>%(thread)s%(module)s>%(lineno)d>%(funcName)s>>>>%(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S %p"
    # LOG基础配置
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT )

    logging.info((__file__, sys._getframe().f_lineno, sys._getframe().f_code.co_name, "info"))
    logging.debug("This is a debug log")
    logging.info("This is a info log")
    logging.warning("This is a warning log")
    logging.error("This is a error log")
    logging.critical("This is a critical log")
    # 打印当前文件名， 行号， 函数名
    print(__file__, sys._getframe().f_lineno, sys._getframe().f_code.co_name)
    # logging.log(logging.WARNING,"This is a warning log")
    pass