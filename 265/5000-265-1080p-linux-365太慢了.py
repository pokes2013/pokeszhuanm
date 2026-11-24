#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess
import time
from datetime import datetime

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    output_folder = "OK"
    yuan_folder = "source_data"
    log_file = "logs.txt"
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(yuan_folder, exist_ok=True)

    video_suffix = {".mp4", ".mov", ".mkv", ".avi", ".flv", ".wmv", ".m4v"}
    file_list = []
    for name in os.listdir("."):
        full_path = os.path.abspath(name)
        if os.path.isfile(full_path):
            ext = os.path.splitext(name)[1].lower()
            if ext in video_suffix:
                file_list.append(full_path)
    if not file_list:
        print("当前目录没有找到可处理的视频文件")
        return
    print(f"一共找到 {len(file_list)} 个待处理视频\n")

    for src_path in file_list:
        print(f"\n=====开始处理: {src_path} =====")
        start_time = time.time()
        basename_no_ext = os.path.splitext(os.path.basename(src_path))[0]
        temp_out = os.path.join(script_dir, f"{basename_no_ext}_out.mp4")

        # 和你给的命令一模一样，无额外参数
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-i", src_path,
            "-vf", "scale=1920:1080",
            "-c:v", "libx265",
            "-crf", "28",
            "-b:a", "256k",
            temp_out
        ]

        ret = subprocess.run(ffmpeg_cmd, shell=False)
        if ret.returncode != 0:
            print(f"转码失败: {src_path}")
            continue
        print("转换OK")

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


if __name__ == "__main__":
    main()
