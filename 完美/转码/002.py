import os
import subprocess


def zhuanmacode(fbl, input_video, output_video):
    if fbl == 0:
        cmd = (
            "ffmpeg -i {input_video} -vcodec h264 -preset veryfast -crf 23 -maxrate 2000k -bufsize 3000k -r 29.97 {output_video}".
            format(input_video=input_video, output_video=output_video))
        print("原始分辨率:", cmd)
        subprocess.run(cmd)
    elif fbl == 960:
        cmd = (
            "ffmpeg -i {input_video} -vcodec h264 -preset veryfast -crf 23 -maxrate 1300k -bufsize 3000k -vf scale=960:540 -r 29.97 {output_video}".
            format(input_video=input_video, output_video=output_video))
        print("960P:", cmd)
        subprocess.run(cmd)
    elif fbl == 2000:
        cmd = (
            "ffmpeg -i {input_video} -vcodec h264 -preset veryfast -crf 23 -maxrate 1300k -bufsize 3000k -vf scale=1280:720 -r 29.97 {output_video}".
            format(input_video=input_video, output_video=output_video))
        print("960P:", cmd)
        subprocess.run(cmd)
    elif fbl == 3000:
        cmd = (
            "ffmpeg -i {input_video} -vcodec h264 -preset veryfast -crf 22 -maxrate 2000k -bufsize 3000k -vf scale=1280:720 -r 29.97 {output_video}".
            format(input_video=input_video, output_video=output_video))
        print("3000_720p:", cmd)
        subprocess.run(cmd)
    elif fbl == 4000:
        cmd = (
            "ffmpeg -i {input_video} -vcodec h264 -preset slow -qcomp 0.5 -psy-rd 0.3:0 -aq-mode 2 -aq-strength 0.8 -r 29.97 {output_video}".
            format(input_video=input_video, output_video=output_video))
        print("4000超清_720p:", cmd)
        subprocess.run(cmd)
    else:
        print("输入有误")


def video_scan(pathss=os.getcwd()):
    """
         此函数是遍历视频文件，请输入您的路径，遍历出的结果不包含子目录，并生成一个list
    """
    # 当前目录所有文件的序列
    file_list = os.listdir(pathss)
    vido_list = [s for s in file_list if '*' in s]  # 当前目录所有文件

    list_vido_any = []
    # 列表中的字母须小写
    kzhan_list = ["mp4", "avi", "wmv", "rmvb", "mov", "mkv"]

    for vido_path in os.listdir(os.chdir(pathss)):

        # 以点为分隔符，分割文件名和扩展名; s为路径+文件名，不含扩展名
        s = vido_path.split(".")
        # ss为扩展名，这里统一使用小写
        ss = s[len(s) - 1].lower()
        for kzhan in kzhan_list:
            if ss == kzhan:
                list_vido_any.append(vido_path)

    print(list_vido_any)
    return list_vido_any


def video_name_pj(video_name):
    notkuozhan_video_name = os.path.splitext(video_name)[0]
    out_videos = notkuozhan_video_name + "_h264" + ".mp4"
    return out_videos


def move_file(inputvideo, outvideos):
    if not os.path.exists("ok"):
        os.makedirs("ok")
    if not os.path.exists("source_data"):
        os.makedirs("source_data")

    os.system("move {} {} >nul".format(inputvideo, 'source_data'))
    os.system("move {} {} >nul".format(outvideos, 'ok'))

for video in video_scan():
    outvideo = video_name_pj(video)
    zhuanmacode(0, video, outvideo)
    move_file(video,outvideo)




# ffmpeg -i input.mp4 -vcodec h264 -preset slow -crf 23 -maxrate 2000k -bufsize 3000k -vf scale=1280:-2 -r 29.97 output.mp4

