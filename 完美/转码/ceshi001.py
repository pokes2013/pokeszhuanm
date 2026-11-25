
import sys

# print("分辨率：1.720P；2.原始分辨率；3.1080p；4.960*540；5.720*404")

fenbian = input("分辨率：1.720P；2.原始分辨率；3.1080p；4.960*540；5.720*404----------请选择分辨率编号：")

# print("转码速率：1.veryfast；2.slow")

sulu = input("转码速率：1.veryfast；2.slow-----请选择转码速率：")


# print("分辨率：1.720P；2.原始分辨率；3.1080p；4.960*540；5.720*404")
# 1.veryfast；2.slow
if int(fenbian) == 1 and int(sulu)==1:
    print("您选择的分辨率是：720P，转码速率是：veryfast")
    qr = input("确认请按1，退出请按2：")
    if int(qr) == 1:
        print("开始转码")
    else:
        sys.exit()

elif int(fenbian) == 1 and int(sulu)==2:
    print("您选择的分辨率是：720P，转码速率是：slow")
    qr = input("确认请按1，退出请按2：")
    if int(qr) == 1:
        print("开始转码")
    else:
        sys.exit()

elif int(fenbian) == 2 and int(sulu) == 1:
    print("您选择的分辨率是：原始分辨率，转码速率是：veryfast")
    qr = input("确认请按1，退出请按2：")
    if int(qr) == 1:
        print("开始转码")
    else:
        sys.exit()

elif int(fenbian) == 2 and int(sulu) == 2:
    print("您选择的分辨率是：原始分辨率，转码速率是：slow")
    qr = input("确认请按1，退出请按2：")
    if int(qr) == 1:
        print("开始转码")
    else:
        sys.exit()


elif int(fenbian) == 3 and int(sulu) == 1:
    print("您选择的分辨率是：1080p，转码速率是：veryfast")
    qr = input("确认请按1，退出请按2：")
    if int(qr) == 1:
        print("开始转码")
    else:
        sys.exit()

elif int(fenbian) == 3 and int(sulu) == 2:
    print("您选择的分辨率是：1080p，转码速率是：slow")
    qr = input("确认请按1，退出请按2：")
    if int(qr) == 1:
        print("开始转码")
    else:
        sys.exit()

elif int(fenbian) == 4 and int(sulu) == 1:
    print("您选择的分辨率是：960*540，转码速率是：veryfast")
    qr = input("确认请按1，退出请按2：")
    if int(qr) == 1:
        print("开始转码")
    else:
        sys.exit()

elif int(fenbian) == 4 and int(sulu) == 2:
    print("您选择的分辨率是：960*540，转码速率是：slow")
    qr = input("确认请按1，退出请按2：")
    if int(qr) == 1:
        print("开始转码")
    else:
        sys.exit()

elif int(fenbian) == 5 and int(sulu) == 1:
    print("您选择的分辨率是：720*404，转码速率是：veryfast")
    qr = input("确认请按1，退出请按2：")
    if int(qr) == 1:
        print("开始转码")
    else:
        sys.exit()
elif int(fenbian) == 5 and int(sulu) == 2:
    print("您选择的分辨率是：720*404，转码速率是：slow")
    qr = input("确认请按1，退出请按2：")
    if int(qr) == 1:
        print("开始转码")
    else:
        sys.exit()





    if int(sulu) == 1:
        print("您选择的分辨率是：720P，转码速率是：veryfast")
        qr = input("确认请按1，退出请按2：")
        if int(qr) == 1:
            print("开始转码")
        else:
            sys.exit()
    elif int(sulu) == 2:
        print("您选择的分辨率是：720P，转码速率是：slow")
        qr = input("确认请按1，退出请按2：")
        if int(qr) == 1:
            print("开始转码")
        else:
            sys.exit()
    else:
        sys.exit()


elif int(fenbian) == 2:
    pass
elif int(fenbian) == 3:
    pass
elif int(fenbian) == 4:
    pass
elif int(fenbian) == 5:
    pass
