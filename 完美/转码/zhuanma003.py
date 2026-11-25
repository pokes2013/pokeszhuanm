import os
import time


class get_zhuanma:

    def __init__(self, task_name):
        self.task_name = task_name
        print("批次：", task_name)

    def video_scan(self, pathss=os.getcwd()):
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

    def create_directory_if_not_exists(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def zhuanma_code(self, input_video, output_video, speed="veryfast", crf="23", maxrate="2000k", bufsize="3000k",
                     scale_fbl="1280:-2"):
        """
        FFmpeg代码的拼接，并未执行
        默认的分辨率为：scale_fbl=1280:-2,1280是宽度，高度等比例缩放
        使用注意事项：
            input_video 输入文件，是一个绝对路径，所以在使用必须保证文件路径存在
            out_video 输出文件，是一个绝对路径，所以在使用必须保证文件路径存在
            speed 转码速度默认采用最快速度
            crf 视频质量默认23
            maxrate 平均码率默认2000K
            bufsize 振幅码率默认3000K
            scale_fbl=1280:-2,默认的分辨率为1280是宽度，高度等比例缩放

        """

        ffmpeg_code = (
            "ffmpeg -i {input_video} -vcodec h264 -preset {speed} -crf {crf} -maxrate {maxrate} -bufsize {bufsize} -vf scale={scale_fbl} -r 29.97 {output_video}"
            .format(input_video=input_video, speed=speed, crf=crf, maxrate=maxrate, bufsize=bufsize,
                    scale_fbl=scale_fbl,
                    output_video=output_video))

        # print(ffmpeg_code)
        return ffmpeg_code

    def zhuanma_code_source_fbl(self, input_video, output_video, speed="veryfast", crf="23"):
        """
        FFmpeg代码的拼接，源分辨率
        """

        ffmpeg_code = (
            "ffmpeg -i {input_video} -vcodec h264 -preset {speed} -crf {crf} -r 29.97 {output_video}"
            .format(input_video=input_video, speed=speed, crf=crf, output_video=output_video))

        # print(ffmpeg_code)
        return ffmpeg_code


    def video_name_pj(self, video_name):
        notkuozhan_video_name = os.path.splitext(video_name)[0]
        out_videos = notkuozhan_video_name + "_h264" + ".mp4"
        return out_videos

    def cmd_isrun(self, cmd_code):
        # print(cmd_code)
        os.system(cmd_code)

    def xiuxi_sleep(self, xiuxi=600):
        while xiuxi > 0:
            print("程序休息秒倒计时：", xiuxi, "秒")
            xiuxi -= 1
            time.sleep(1)
            os.system('cls')

    def zhuanma_run(self, video_list, speed="veryfast", crf="23", maxrate="2000k", bufsize="3000k",
                    scale_fbl="1280:-2"):

        if_out_dir = "ok"
        self.create_directory_if_not_exists("ok")
        if_source_dir = "source_data"
        self.create_directory_if_not_exists("source_data")

        for input_video in video_list:
            out_videos = self.video_name_pj(input_video)
            cmd_ffmpeg_code = self.zhuanma_code(input_video, out_videos, speed, crf, maxrate, bufsize, scale_fbl)
            # print(cmd_ffmpeg_code)

            # 转码
            self.cmd_isrun(cmd_ffmpeg_code)
            # 移动文件
            self.cmd_isrun("move {} {} >nul".format(out_videos, if_out_dir))
            self.cmd_isrun("move {} {} >nul".format(input_video, if_source_dir))

            self.xiuxi_sleep(3)


# pc1 = get_zhuanma("veryfast_23_2000K_3000K_720p")
#
# vide_list = pc1.video_scan()
# pc1.zhuanma_run(vide_list, "veryfast", "23", "2000k", "3000k", "1280:-2")

pc2 = get_zhuanma("slow_23_sourceFBL")
pc2.zhuanma_code()

# ps: speed=veryfast/slow, crf=23, maxrate=2000k, bufsize=3000k, scale_fbl

