#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess
import time
from datetime import datetime

def main():
    # 锁定脚本所在目录，输出文件夹都生成在脚本旁边
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    output_folder = "outfiles"
    yuan_folder = "sourcefiles"
    log_file = "logs.txt"

    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(yuan_folder, exist_ok=True)

    video_suffix = {".mp4", ".mov", ".mkv", ".avi", ".flv", ".wmv", ".m4v"}

    # ==========双模式判断==========
    drag_files = sys.argv[1:]
    if drag_files:
        # 拖拽模式：使用传入的文件
        file_list = []
        for f in drag_files:
            fp = os.path.abspath(f)
            if os.path.isfile(fp):
                file_list.append(fp)
        print(f"【拖拽模式】收到 {len(file_list)} 个文件\n")
    else:
        # 无参数：遍历当前目录视频
        print("【目录扫描模式】未收到拖拽文件，扫描当前目录视频\n")
        file_list = []
        for name in os.listdir("."):
            full_path = os.path.abspath(name)
            if os.path.isfile(full_path):
                ext = os.path.splitext(name)[1].lower()
                if ext in video_suffix:
                    file_list.append(full_path)

    if not file_list:
        print("没有找到待处理视频文件！")
        input("\n按回车退出...")
        return

    print(f"待处理总数量：{len(file_list)}")

    for src_path in file_list:
        print(f"\n=====开始处理: {src_path} =====")
        start_time = time.time()

        dirname = os.path.dirname(src_path)
        basename_no_ext = os.path.splitext(os.path.basename(src_path))[0]
        temp_out = os.path.join(dirname, f"{basename_no_ext}_ok.mp4")

        ffmpeg_cmd = [
            "ffmpeg",
            "-i", src_path,
            "-vcodec", "h264",
            "-preset", "veryfast",
            "-tune:v", "ssim",
            "-qmin", "18",
            "-crf", "19",
            "-maxrate", "1800k",
            "-bufsize", "2000k",
            "-r", "29.97",
            "-vf", "scale=1280:-2",
            "-acodec", "aac",
            "-b:a", "192k",
            "-ac", "2",
            "-y",
            temp_out
        ]

        ret = subprocess.run(ffmpeg_cmd, shell=False)
        if ret.returncode != 0:
            print(f"❌转码失败: {src_path}")
            continue
        print("✅转换OK")

        # 移动源文件
        shutil.move(src_path, os.path.join(yuan_folder, os.path.basename(src_path)))
        shutil.move(temp_out, os.path.join(output_folder, os.path.basename(temp_out)))

        end_time = time.time()
        cost_sec = end_time - start_time
        cost_min = cost_sec / 60

        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"time：{cost_min:.2f} minute\n")
            f.write(f"{src_path}-{date_str}-{time_str}\n")
            f.write("------------------------------------------------------------\n")

        # time.sleep(10*60) # 需要每处理完等待10分钟打开注释

    print("\n====全部任务执行完毕====")
    # Windows防止窗口直接关闭；Linux下运行在终端中，这个input不影响
    input("\n按回车键关闭窗口...")

if __name__ == "__main__":
    main()