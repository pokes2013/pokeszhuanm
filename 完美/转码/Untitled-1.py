
import os
import subprocess
import time

def get_video(pathss=os.getcwd()):
        """
        遍历当前目录下的视频文件作为输入文件，并且拼接出：输出文件
        :param pathss: 工作目录
        :return: 返回一个字典
        """
        file_list = os.listdir(pathss)
        my_dict = {}
        kzhan_list = ["mp4", "avi", "wmv", "rmvb", "mov", "mkv"]

        for vido_path in file_list:

            ss = vido_path.split(".")[-1].lower()  # 以点为分隔符取扩展名，并统一转为小写
            for kzhan in kzhan_list:
                if ss == kzhan:
                    notkuozhan_video_name = os.path.splitext(vido_path)[0]
                    out_videos = notkuozhan_video_name + "_h264" + ".mp4"
                    my_dict.setdefault(vido_path, out_videos)  # 以键值对写入字典
        print(my_dict)
        return my_dict

zidian = get_video()
for key,value in zidian.items():
    print(key, value)

