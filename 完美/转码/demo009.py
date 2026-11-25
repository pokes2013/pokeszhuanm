
import os

pathss = r"e:\\"
file_list = os.listdir(pathss)
my_dict = {}
kzhan_list = ["mp4", "avi", "wmv", "rmvb", "mov", "mkv"]

for vido_path in file_list:

    ss = vido_path.split(".")[-1].lower()  # 以点为分隔符取扩展名，并统一转为小写
    for kzhan in kzhan_list:
        if ss == kzhan:
            new_vido_path = vido_path.replace(" ", "~")  # 去除字符串空格
            os.rename(vido_path, new_vido_path)  # 去除空格后改名


            videoname_list = new_vido_path.split('.')  # 由于文件名中有点，扩展名中也有点，所有以下两行修复类似 abc-123.hevc.mp4
            del videoname_list[-1]  # 删除最后一个元素.mp4
            notkuozhan_video_name = '.'.join(videoname_list)  # 将list再次以点拼接，并转换成str

            out_videos = notkuozhan_video_name + "_h264" + ".mp4"
            my_dict.setdefault(new_vido_path, out_videos)  # 以键值对写入字典
print(my_dict)



