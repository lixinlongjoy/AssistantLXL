
if __name__ == "__main__":

    import re

    print("十六进制字符串转bytes数组")
    s1 = "abcdef1234567890"
    print(len(s1), s1)
    s2 = bytes.fromhex(s1)
    print("bytes.fromhex():",len(s2),s2)
    s3 = s2.hex()
    print(".hex():",s3)
    s4 = " ".join([hex(i)[2:] for i in s2])
    print( '" ".join([hex(i)[2:] for i in s2]\n\t',s4)

    print("十六进制字符串转bytes数组")
    s1 = "ab cd ef 12 34 56 78 90"
    print(len(s1), s1)
    s2 = bytes().fromhex(s1)
    print(len(s2), s2)

    print("十六进制字符串转Bytes数组")
    s1 = "ab cd ef 12 34 56 7 90"
    print(len(s1), s1)

    try:
        s2 = bytes().fromhex(s1)
        print(len(s2), s2)
    except ValueError as e:
        print('\tfromhex转换出错：',e)
        print(len(e.args))
        for i in e.args:
            print("\t",i)
        # 使用re模块从args中筛选出错误位置
        # patt = r"position (.*)$"
        patt = r"position (\d*)$"
        patt = r"\d+"
        patton = re.compile(patt)
        reObj = patton.search(e.args[0])
        print("\treObj:{}".format(reObj))
        if (reObj != None):
            print("\treObj.span:", reObj.span())
            print("\treObj.start:", reObj.start())
            print("\treObj.end:", reObj.end())
            print("\treObj.pos:", reObj.pos)
            print("\treObj.endpos:", reObj.endpos)
            print("\treObj.lastindex:", reObj.lastindex)
            print("\treObj.lastgroup:", reObj.lastgroup)
            print("\treObj.string:", reObj.string)
            print("\treObj.groupdict:", reObj.groupdict())
            print("\treObj.group() : ", reObj.group())
            if reObj.lastindex != None:
                for i in range(reObj.lastindex + 1):
                    print("\treObj.group({}):{}".format(i, reObj.group(i)))
                    print("\treObj.span({}):{}".format(i, reObj.span(i)))
                    print("\treObj.start({}):{}".format(i, reObj.start(i)))
                    print("\treObj.end({}):{}".format(i, reObj.end(i)))
            if reObj.lastindex != None:
                for i in range(2):
                    print("\treObj.groups({}):{}".format(i, reObj.groups(i)))
        print()
