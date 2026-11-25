import os

def get_video(pathss = os.getcwd()):
    """
    遍历当前目录下的视频文件作为输入文件，并且拼接出：输出文件
    :param pathss: 工作目录
    :return: 返回一个字典
    """
    file_list = os.listdir(pathss)
    my_dict = {}
    kzhan_list = ["mp4", "avi", "wmv", "rmvb", "mov", "mkv"]

    for vido_path in file_list:
        ss = vido_path.split(".")[-1].lower()   # 以点为分隔符取扩展名，并统一转为小写
        for kzhan in kzhan_list:
            if ss == kzhan:
                videoname_list = vido_path.split('.')   #由于文件名中有点，扩展名中也有点，所有以下两行修复类似 abc-123.hevc.mp4
                del videoname_list[-1]      #删除最后一个元素.mp4
                notkuozhan_video_name = '.'.join(videoname_list)  #将list再次以点拼接，并转换成str
                out_videos = notkuozhan_video_name + "_h264" + ".mp4"
                my_dict.setdefault(vido_path, out_videos)   #以键值对写入字典
    #
    print(my_dict)
    return my_dict

get_video(pathss=r"e:\\")

