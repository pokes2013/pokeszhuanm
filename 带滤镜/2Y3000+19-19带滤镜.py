import os, sys, time


# 创建和检验目录是否存在，如果存在则跳过，不存在则创建

def floders(floder_name):
    isExists = os.path.exists(floder_name)
    if not isExists:
        os.makedirs(floder_name)


# 过滤视频文件

def vidos(vido_path):
    file_list = os.listdir(vido_path)  # 当前目录所有文件的序列
    vido_hz_list = [".avi", ".flv", ".m4v", ".mkv", ".mp4", ".mov", ".rm", ".rmvb", ".ts", ".vob", ".wmv"]

    full_list = []  # 先新建一个空的列表full_list，用来存放帅选出来的元素
    for vido_hz in vido_hz_list:
        vido_gg_list = [s for s in file_list if vido_hz in s]  # 循环筛选各个后缀的视频列表
        for vido in vido_gg_list:  # 遍历这个列表
            # print(vido)               #打印测试之后出现了重复，例如：abc-999.rm和abc-999.rmvb，因为后缀中都有rm所以同时会被筛选出来
            if vido not in full_list:  # 去重后放入新建的空列表中
                full_list.append(vido)
    return full_list


# 转码前的准备

# 获取当前目录
path = os.getcwd()

# 遍历最终列表full_list得到每个vido文件
for input_vido in vidos(path):
    qianzhui = os.path.splitext(input_vido)[0]  # 这里我们提取文件名，不含扩展名，用于后面输出文件名得格式化
    # print(qianzhui)

    # 文件扩展名得提取
    fg_name = os.path.splitext(input_vido)
    houzhui = fg_name[1]
    # print(houzhui)

    output_vido = qianzhui + "_ok" + ".mp4"
    print(output_vido)

    # 转码

    floders("OK")
    floders("source_data")
    bit = "-qmin 19 -crf 19.1 -maxrate 2500k -bufsize 5000k"  # 码率控制
    vido_filter = "-vf unsharp=5:5:0.06:5:5:0.0,scale=1280:-2"  # 过滤器
    speed = "-preset veryfast"  # 转码速度

    start_time = time.time()
    zhuanma = "ffmpeg -i {} -vcodec h264 {} -tune:v ssim {} -r 29.97 {} {} && move {} OK >nul && move {} source_data>nul" \
        .format(input_vido, speed, bit, vido_filter, output_vido, output_vido, input_vido)  # python调用cmd命令方法转码
    isRUN = os.system(zhuanma)
    print("*" * 100)  # 分割线
    print(path + output_vido + '-转换成功')  # 输出转换成功的提示

    # 记录结束时间
    end_time = time.time()
    took = (end_time - start_time) / 60
    took = int(took)
    took = str(took)
    # print("所需时间:", took,"分钟")

    # 日志系统，日志文件在视频目录中

    file = open("logs.txt", 'a', encoding='UTF-8')
    file.write(input_vido + "\n")
    file.write("所需时间：" + took + "\n")
    file.write("-" * 100 + "\n")
    file.close()

    # 休息5分钟

    time.sleep(300)
#
