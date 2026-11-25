import os


class video_trans:

    # 遍历视频文件列表
    def video_scan(pathss=os.getcwd()):
        """
             此函数是遍历视频文件，请输入您的路径，遍历出的结果不包含子目录，并生成一个list
        """
        # 当前目录所有文件的序列
        file_list = os.listdir(pathss)
        vido_list = [s for s in file_list if '*' in s]  # 当前目录所有MP4文件

        list_vido_any = []
        # 列表中的字母须小写
        kzhan_list = ["mp4", "avi", "wmv", "rmvb", "mov", "mkv"]

        for vido_path in os.listdir(os.chdir(pathss)):

            # 以点为分隔符，分割文件名和扩展名
            # s为路径+文件名，不含扩展名
            s = vido_path.split(".")
            # ss为扩展名，这里统一使用小写
            ss = s[len(s) - 1].lower()
            for kzhan in kzhan_list:

                if ss == kzhan:
                    list_vido_any.append(vido_path)

        # print(list_vido_any)
        return list_vido_any

    # 将输入文件拼接生成输出文件
    def generate(input_video):
        out_video = os.path.splitext(input_video)[0] + "_h264" + ".mp4"
        return out_video


    # 判断OK文件是否存在
    def create_directory_if_not_exists(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    # 转码函数
    def video_transcoding(input_video, output_video, speed="veryfast", crf="23", maxrate="2000k", bufsize="3000k"):
        """
        使用注意事项：
        input_video 输入文件，是一个绝对路径，所以在使用必须保证文件路径存在
        out_video 输出文件，是一个绝对路径，所以在使用必须保证文件路径存在
        speed 转码速度默认采用最快速度
        crf 视频质量默认23
        maxrate 平均码率默认2000K
        bufsize 振幅码率默认3000K

        :return:

            无
        """

        zhuan = (
            "ffmpeg -i {input_video} -vcodec h264 -preset {speed} -crf {crf} -maxrate {maxrate} -bufsize {bufsize} -vf scale=1280:-2 -r 29.97 {output_video}"
            .format(input_video=input_video, speed=speed, crf=crf, maxrate=maxrate, bufsize=bufsize,
                    output_video=output_video))

        print(zhuan)
        isRun = os.system(zhuan)
        return isRun

    def move_video(source_file, new_path):
        video_trans.create_directory_if_not_exists("ok")  # 判断OK文件是否存在,默认就是OK
        video_trans.create_directory_if_not_exists("source_data")  # 判断source_data文件是否存在,默认就是OK
        os.system("move {source_file} {new_path} >nul".format(source_file=source_file, new_path=new_path))


# 获取当前目录下的视频文件
list_vido_any = video_trans.video_scan()
for input_video in list_vido_any:
    # print(input_video)
    out_videos = video_trans.generate(input_video)  # 拼接out_videos
    confirm = video_trans.video_transcoding(input_video, out_videos)  # 正在转码
    if confirm == 0:  # 判断转码是否成功
        video_trans.move_video(input_video, "ok")
        video_trans.move_video(out_videos, "source_data")
    print("输入文件：{} \n输出文件：{}".format(input_video, out_videos))
    print("*" * 100)
