import struct

# struct对象可以根据格式化字符串的格式来读写二进制数据
#   s = struct.Struct('fmt')
#   s.pack(v1, v2, ...)   按照fmt格式化字符串的格式打包参数V1, V2   返回字节数组
#   s.pack_into(buffer, offset, v1, v2, ...) 按照fmt格式化字符串的格式打包参数V1, V2, 并将打包的字节写入从offset开始的缓冲buffer中
#   s.unpack()
#   s.unpack_from(buffer, offset=0) 按照fmt格式化字符串从buffer的offset位置开始解包，返回元组，buffer的大小以字节为单位，减去offset后必须至少为格式所需大小
#   struct.calcsize('fmt')
#   获取fmt格式字符串所需字节大小

# 属性
    # format      格式化字符串
    # size        结构体大小

# 可选的格式字符串指示大小端，大小和对齐
    # @ native order       native.size     native alignment默认值      本地大小端配置 本地数据对齐 本地数据大小
    # = native order      std.size        none alignment               本地大小端配置 无数据对齐   标准数据大小
    # < little endian     std.size        none alignment               小端           无数据对齐   标准数据大小
    # > big endian        std.size        none alignment               大端           无数据对齐   标准数据大小
    # ! network     和>功能相同
    # 使用sys.byteorder可获取系统大小端配置

# 格式化字符串
#     python定义了六种基本类型，str, int, float, tuple, array, dict,
# format          c - type                python - type           standard - size
#   x               padbyte                 noparas                         1      xxx
#   c               char                    1字节的bytes                    1
#   b               signed char             int(-128 - -127)                1
#   B               unsigned char           int(0 - 255)                    1       xxx
#   ?               _Bool                   bool(非0 0)                     1
#   h               short                   int                             2
#   H               unsigned short          int                             2       xxx
#   i               int                     int                             4
#   I               unsigned int            int                             4       xxx
#   l               long                    int                             4
#   L               unsigned long           int                             4       xxx
#   q               long long               int                             8
#   Q               unsigned long long      int                             8       xxx
#   n               ssize_t                 int
#   N               size_t                  int
#   e               (7)                     float                           2
#   f               float                   float                           4
#   d               double				    float               			8
#   s               char[]				    bytes
#   p               char                    bytes
#   P               void *				    integer
if __name__ == "__main__":
    print("""分析python中以下数据类型区别 
    可打印字符串
    数值列表
    不可打印字符串
    bytes数组
    """)

    print("可打印字符串与bytes数组:")
    s1 = '12abc'
    print("\t可打印字符                :{} {}   {}".format(type(s1),len(s1),s1))
    b1 = s1.encode('ascii')
    print("\t将可打印字符encode为bytes :{} {}   {}".format(type(b1),len(b1),b1))
    s2 = b1.decode("ascii")
    print("\t将bytes decode为可打印字符:{} {}   {}".format(type(s2), len(s2), s2))

    s3 = str(b1,encoding="ascii")
    print("\t将bytes按ascii编码str化:            {} {}   {}".format(type(s3), len(s3), s3))
    b2 = bytes(s3,encoding="ascii")
    print("\t将str化的bytes再按ascii编码bytes化: {} {}   {}".format(type(b2), len(b2), b2))

    s4 = str(b2)
    print("\t将bytes不提供任何编码str化         :{} {}   {}".format(type(s4), len(s4), s4))
    b3 = bytes(s4,"ascii")
    print("\t将str化的bytes再bytes化            :{} {}   {}".format(type(b3), len(b3), b3))
    s5 = str(b3)
    print("\t将bytes不提供任何编码str化         :{} {}   {}".format(type(s5), len(s5), s5))
    b4 = bytes(s5,"ascii")
    print("\t将str化的bytes再bytes化            :{} {}   {}".format(type(b4), len(b4), b4))

    print("""
    对于bytes转str应使用decode或者str(encoding=)处理
    对于str转bytes应使用encode或者bytes(encoding=")处理
    对于bytes转str不指定编码类型将导致bytes的b标识和引号被转换为str，产生字节码字符串,导致数据长度越来越大，回不去了 
        """)

    print("列表与bytes数组")
    s1 = [1, 2, ord('1'), ord('2')]
    print("\t数值列表              :{} {}   {}".format(type(s1), len(s1), s1))
    b1 = bytes(s1)
    print("\t将数值列表转为bytes   :{} {}   {}".format(type(b1),len(b1),b1))
    s2 = str(b1,encoding="ascii")
    print("\t将bytes按ascii编码str化则可能出现无法显示字符:{} {}   {}".format(type(s2), len(s2), s2))

    print("不同进制的bytes数组与字符串")
    b1 = b'\x31\x32\61\62'#字节码中\后无进制符号默认为8进制
    print("\t原bytes数值其中\\后的数值按8进制解析 :{} {}   {}".format(type(b1),len(b1),b1))
    s1 = b1.decode('ascii')
    print("\t将bytes按ascii编码str化             :{} {}   {}".format(type(s1), len(s1), s1))


    print("\n定义时是否有b标识导致bytes和str区别")
    b1 = (b'\x01\x0212')#字节码
    print("\tbytes数组 :{} {}   {}".format(type(b1), len(b1), b1))
    s1 = '\x01\x0212'
    print("\t字符串    :{} {}   {}".format(type(s1), len(s1), s1))


    print("\n十六进制字符串与字节数组转换")
    #
    print("\n有不可打印字符时")
    s1 = '\x01\x02\x31\x32'
    s2 = b'\x01\x02\x31\x32'
    print(len(s1),s1,type(s1),type(s1[0]))
    print(len(s2),s2,type(s2),type(s2[0]))
    print(bytes(map(ord, s1)))

    print("\n全为可打印字符时")
    s1 = '\x31\x32'
    s2 = b'\x31\x32'
    print(len(s1),s1,type(s1[0]))
    print(len(s2),s2,type(s2[0]))
    print(bytes(map(ord, s1)))
    print( s1[1] =="2")


    # 打包解包
    v = (1, b'good', 1.22)  # 源数据
    s = struct.Struct('I4sf')  # 创建struct对象
    p = s.pack(*v)  # 打包
    u = s.unpack(p)  # 解包
    fmt = s.format  # 结果 b'I4sf'
    size = s.size  # 结果 12表示此格式化字符需要12字节数组来存储

    v = (1, b'good', 1.22)  # 源数据
    s = struct.Struct('>I4sf')  # 创建struct对象
    p = s.pack(*v)  # 打包
    u = s.unpack(p)  # 解包
    fmt = s.format  # 结果 b'I4sf'
    size = s.size  # 结果 12表示此格式化字符需要12字节数组来存储

    buf = bytearray(100)  # 申请一个100字节的字节数组 默认值为0
    s.pack_into(buf, 10, *v)  # 打包数据到buf[10]开始的字节
    ubuf = s.unpack_from(buf, 10)

    vaa = struct.pack('>I', 1255)  # vaa: '\x00\x00\x04\xe7' 1*4=1个字节
    vab = struct.pack('>II', 1255, 23)  # vab: '\x00\x00\x04\xe7\x00\x00\x00\x17' 2*4=8个字节
    vac = struct.pack('>2I?', 1255, 23, True)  # vac: '\x00\x00\x04\xe7\x00\x00\x00\x17\x01' 2*4+1=9个字节

    vaa = struct.pack('>I', 1255)  # vaa: '\x00\x00\x04\xe7'
    vab = struct.pack('>II', 1255, 23)  # vab: '\x00\x00\x04\xe7\x00\x00\x00\x17'
    vaaa = struct.unpack('>I', vaa)  # vaaa: <class 'tuple'>: (1255, )
    vaba = struct.unpack('>II', vab)  # vaba: <class 'tuple'>: (1255, 23)

    import struct
    from ctypes import create_string_buffer

    buf = create_string_buffer(9)
    struct.pack_into(">II", buf, 0, 1, 2)
    struct.pack_into(">?", buf, 8, True)
    # 记录位置
    pos = 0
    # 从buf缓存区中以大端方式从偏移位置pos处解包两个无符号整型数据返回，注意
    # 返回值如果只写一个则返回一个元组，否则你解包几个数据就要写几个返回值。
    val = struct.unpack_from('>II', buf, pos)  # val: <class 'tuple'>: (1, 2)
    val_a, val_b = struct.unpack_from('>II', buf, pos)  # val_a: 1  val_b: 2

    # 重置解包位置
    pos += struct.calcsize('>II')  # pos: 8
    val_c, = struct.unpack_from('>?', buf, pos)  # val_c: True
