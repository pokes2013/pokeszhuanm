#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频批量转码工具（字典驱动版 · 菜单选档）
========================================================================
用途
    扫描「当前工作目录」下所有视频文件，逐个用 ffmpeg 转成 H.264 的 MP4。
    成品统一放进 ok\\，源文件统一挪进 source_data\\，方便你整批删除源文件。
    内核仍是"字典"思路：先建立 {源文件: 成品文件} 的映射，再按映射逐个处理。
    每个视频处理完都会在 log.csv 追加一行：开始时间、视频时长（分钟）、
    结束时间、实际耗时（分钟）、状态（转码成功/失败）、文件名。
    开跑前还会检查当前分区剩余空间：按「视频个数 × 2.5 GB」估算，
    不够就报警并直接终止，避免转到一半把盘写满；每次检查的结论
    （时间、剩余空间、需预留多少、是否通过）也会在 log.csv 里记一行。

依赖
    python 3.7+ 、ffmpeg（必须已加入系统环境变量 PATH）。

用法
    把本脚本和视频放在同一个目录，然后在该目录执行：
        python 通过字典_转码完美.py
    启动后按数字键选档位（0 / 1 / 2 / 3 / 4 / 5），按空格键退出。
    选定后自动开始批量转码，全部结束后再按空格键关闭。

与原版的关系
    在原「通过字典_转码完美」的基础上：
    · 档位改为启动时菜单选择，参数表见 PROFILES；
    · 修掉了路径含空格时 ffmpeg 打不开文件、成品同名覆盖、失败仍搬运源文件
      等问题；所有编码参数仍写在参数表里，一眼可查。
========================================================================
"""

import csv          # 用于按 CSV 规则写日志（自动处理逗号/引号转义）
import os           # 仅在清屏时用（os.system("cls")）
import re           # 从 ffmpeg 输出里提取视频时长
import shutil       # 用于查找 ffmpeg、移动文件
import subprocess   # 用于调用 ffmpeg（列表参数，路径含空格/中文也安全）
import sys          # 用于返回退出码、判断是否在真实终端
import time         # 用于统计耗时、批次间隔
import unicodedata  # 用于计算中文的显示宽度，保证菜单列对齐
from datetime import datetime            # 用于日志里的起止时间
from pathlib import Path                 # 统一用 Path 处理路径，避免拼接错误

# ======================== 档位参数表 ========================
# 菜单显示与 ffmpeg 参数都从这张表来，改参数只改这里，不会出现
# "菜单写一套、实际跑另一套"的情况。
#   label   : 菜单上显示的名字
#   crf     : 画质（数值越小越清晰、体积越大）
#   maxrate : 码率上限；None 表示只按 crf 走，不设上限
#   scale   : 输出分辨率；None 表示保持原始分辨率
#   bufsize : 可选，覆盖全局 BUFSIZE；写 None 表示该档不加 bufsize
#   （不写 bufsize = 用下面的全局默认值）
PROFILES = {
    "0": {"label": "原始分辨率", "crf": "23", "maxrate": "2000k", "scale": None},
    "1": {"label": "VIP720P",   "crf": "20", "maxrate": "2000k", "scale": "1280:-2"},
    "2": {"label": "720P",      "crf": "23", "maxrate": "2000k", "scale": "1280:-2"},
    # 3 号：码率上限 1500k，缓冲压到 200k（约束很紧，画面复杂时糊得明显）
    "3": {"label": "960P",      "crf": "23", "maxrate": "1500k", "scale": "960:-2", "bufsize": "200k"},
    # 4 号码率上限 3000k，缓冲必须不小于上限，故本档用 3000k 而不是全局 2000k
    "4": {"label": "1080P",     "crf": "22", "maxrate": "3000k", "scale": "1920:-2", "bufsize": "3000k"},
    # 5 号：码率上限 1500k，缓冲压到 200k
    "5": {"label": "low720P",   "crf": "23", "maxrate": "1500k", "scale": "1280:-2", "bufsize": "200k"},
}

# 成品文件名后缀：原名 + "_h264" + ".mp4"
OUT_SUFFIX = "_h264"

# 日志文件名（建在当前工作目录下，CSV 格式，每个视频追加一行）
LOG_FILE = "log.csv"

# 磁盘兜底：每个视频按 2.5 GB 预留空间（宁可多算，不够就直接拦下来）
EST_GB_PER_VIDEO = 2.5

# 成品的存放目录（建在脚本所在目录下）
OUT_DIR = "ok"

# 源文件的归档目录（建在脚本所在目录下）
SRC_DIR = "source_data"

# 每处理完一个视频后的休息秒数。原版这里实际只停 1 秒；
# 若需要给机器散热，把它改成 300（即 5 分钟）即可。
REST_SECONDS = 1

# 认作视频的扩展名（统一转小写后比较）
VIDEO_EXT = {".mp4", ".avi", ".wmv", ".rmvb", ".mov", ".mkv"}

# 所有档位共用的固定参数（preset 沿用原脚本的 veryfast，帧率沿用 29.97）
PRESET = "veryfast"
FRAME_RATE = "29.97"
BUFSIZE = "2000k"    # 全局默认码率缓冲；单档可覆盖，或用 "bufsize": None 关掉

# ========================== 工具函数 ==========================


def clear_screen():
    """在真实终端里清屏；输出被重定向（如管道）时不做任何事。"""
    if sys.stdout.isatty() and os.name == "nt":
        os.system("cls")


def read_key() -> str:
    """
    读入用户的一次按键，返回单个字符。
    Windows 真终端下用 msvcrt 读单键（按下即响应，不用回车）；
    无法读单键时退化为读一行，空行按"空格"处理。
    """
    if os.name == "nt" and sys.stdin is not None and sys.stdin.isatty():
        try:
            import msvcrt                       # 仅 Windows 可用
            return msvcrt.getwch()              # 读一个字符，不等待回车
        except Exception:                       # 极端情况下退回读一行
            pass

    try:
        line = input().strip()                  # 读整行并去掉首尾空白
    except EOFError:                            # 输入流已结束，视同退出
        return " "
    return line if line else " "                # 空行按空格键处理


def display_width(text: str) -> int:
    """
    计算字符串占用的终端显示宽度。
    中文/全角字符算 2 列，英文数字算 1 列——否则菜单用 <10 补空格会错位。
    :param text: 待测量的文本
    """
    width = 0
    for ch in text:
        # W=全角，F=全角变体，这两类在终端里占两列
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad(text: str, width: int) -> str:
    """
    按「显示宽度」右侧补空格，让同列文字对齐。
    :param text: 原文
    :param width: 目标显示宽度
    """
    return text + " " * max(0, width - display_width(text))


def print_menu():
    """打印档位菜单，内容全部由 PROFILES 生成。"""
    print("\n=============== 请选择转码档位 ===============")
    for key, profile in PROFILES.items():                          # 按编号顺序输出
        bits = [f"crf {profile['crf']}"]                           # 画质这一项必有
        if profile["maxrate"]:                                     # 有码率上限才显示
            bits.append(f"maxrate {profile['maxrate']}")
        if profile["scale"]:                                       # 有分辨率才显示
            bits.append(profile["scale"])
        detail = "  ".join(bits)                                   # 拼成一行参数摘要
        print(f"  {key}   {pad(profile['label'], 12)}{detail}")
    print("------------------------------------------------")
    print("  按对应数字键选择档位，按空格键退出")


def choose_quality():
    """
    显示菜单并等待用户选档。
    :return: 档位编号字符串（"0"/"1"/"2"/"4"/"5"）；用户按空格返回 None
    """
    while True:
        print_menu()                                    # 显示菜单
        key = read_key()                                # 等一个按键

        if key == " ":                                  # 空格 = 退出
            print("已退出，未做任何转码。")
            return None

        if key in PROFILES:                             # 合法档位
            print(f"\n已选择档位：{key}  {PROFILES[key]['label']}")
            return key

        if key in ("\r", "\n"):                         # 误按回车，直接重绘菜单
            continue

        keys = " / ".join(PROFILES)                     # 从参数表取可选编号，避免写死
        print(f"\n无效选择「{key}」，请输入 {keys}，或按空格退出。")
        time.sleep(0.6)                                 # 让提示停留一下再刷新
        clear_screen()                                  # 清屏后重新显示菜单


def wait_space():
    """等用户按空格（或回车）后结束，避免双击运行时窗口一闪而过。"""
    print("\n按空格键退出...")
    while read_key() not in (" ", "\r", "\n"):    # 空格、回车、EOF 都算退出
        pass


def unique_path(target: Path) -> Path:
    """
    返回一个「一定不存在」的目标路径，保证不覆盖任何已有文件。
    例如 ok/abc_h264.mp4 已存在，则依次尝试 abc_h264_1.mp4、_2 ……
    :param target: 期望使用的路径
    :return: 未被占用的路径
    """
    if not target.exists():                     # 目标不存在，直接用
        return target

    stem = target.stem                          # 不含扩展名的文件名
    suffix = target.suffix                      # 扩展名（含点）
    parent = target.parent                      # 所在目录
    index = 1                                   # 冲突序号，从 1 开始递增
    while True:
        candidate = parent / f"{stem}_{index}{suffix}"   # 拼出候选名
        if not candidate.exists():              # 找到空位
            return candidate
        index += 1                              # 继续往后找


def check_ffmpeg() -> bool:
    """
    检查 ffmpeg 是否可用。
    :return: 可用返回 True，缺失返回 False
    """
    exe = shutil.which("ffmpeg")                # 在 PATH 中查找 ffmpeg
    if exe:
        print(f"ffmpeg 已就绪：{exe}")
        return True

    print("❌ 未找到 ffmpeg，请先安装并把 ffmpeg 加入系统环境变量 PATH。")
    return False


def format_size(num_bytes: float) -> str:
    """
    把字节数格式化成好读的 GB / MB。
    :param num_bytes: 字节数
    """
    gb = num_bytes / 1024 ** 3                            # 换算成 GB
    if gb >= 1:
        return f"{gb:.2f} GB"
    return f"{num_bytes / 1024 ** 2:.0f} MB"


def check_disk_space(root: Path, video_count: int, log_path: Path) -> bool:
    """
    转码前的磁盘兜底：当前目录所在分区剩余空间是否够本次转码用。
    估算口径：视频个数 × EST_GB_PER_VIDEO（默认每个 2.5 GB），宁可多算。
    检查结果（含日期时间）会写进 log.csv。
    :param root: 工作目录（决定检查哪个分区）
    :param video_count: 待转码视频个数
    :param log_path: log.csv 的完整路径
    :return: True 空间够用；False 不够（同时打印报警内容）
    """
    usage = shutil.disk_usage(str(root))                  # 当前目录所在分区
    free_bytes = usage.free                               # 剩余可用空间
    need_bytes = int(video_count * EST_GB_PER_VIDEO * 1024 ** 3)   # 需要预留的空间

    passed = free_bytes >= need_bytes                     # 是否够用
    append_disk_log(log_path, passed, free_bytes, need_bytes, video_count)  # 结论记到日志

    if passed:                                            # 空间足够
        print(f"磁盘检查：剩余 {format_size(free_bytes)}，"
              f"本次需预留 {format_size(need_bytes)}"
              f"（{video_count} 个视频 × {EST_GB_PER_VIDEO} GB）")
        return True

    # 空间不够：报警并返回 False，由调用方终止转码
    print("\n❌ 磁盘空间不足，已终止转码，未做任何处理：")
    print(f"   当前分区剩余：{format_size(free_bytes)}")
    print(f"   本次需要预留：{format_size(need_bytes)}"
          f"（{video_count} 个视频 × {EST_GB_PER_VIDEO} GB）")
    print(f"   还差：{format_size(need_bytes - free_bytes)}")
    print("   请先清理该分区空间，或把视频分批处理后再运行。")
    return False


def scan_videos(root: Path) -> dict:
    """
    扫描目录下的视频文件，建立「源文件 → 成品文件」的字典。
    :param root: 工作目录
    :return: {Path(源文件): Path(成品文件)}
    """
    mapping = {}                                          # 结果字典
    for entry in sorted(root.iterdir()):                  # 按文件名排序，顺序可预期
        if not entry.is_file():                           # 跳过子目录
            continue
        if entry.suffix.lower() not in VIDEO_EXT:         # 跳过非视频
            continue
        out_name = entry.stem + OUT_SUFFIX + ".mp4"       # 成品命名规则
        mapping[entry] = root / out_name                  # 记录映射
    return mapping


def build_command(quality: str, src: Path, dst: Path) -> list:
    """
    按所选档位拼出 ffmpeg 的参数列表。
    用列表而不是字符串，路径里有空格、中文、括号都无需再加引号，
    从根本上避免「文件名带空格转码就失败」。
    :param quality: 档位编号，必须是 PROFILES 里的键
    :param src: 源文件
    :param dst: 成品文件
    :return: 可直接交给 subprocess 的参数列表
    """
    profile = PROFILES.get(quality)                        # 取出该档位的参数
    if profile is None:                                    # 档位不存在时明确报错
        raise ValueError(f"未知档位 {quality}，只能是 {list(PROFILES)}")

    # 公共头：preset + 画质 crf
    body = ["-preset", PRESET, "-crf", profile["crf"]]
    if profile["maxrate"]:                                 # 该档设了码率上限
        body += ["-maxrate", profile["maxrate"]]
    bufsize = profile.get("bufsize", BUFSIZE)              # 未写则用全局 BUFSIZE
    if bufsize:                                            # 纯 crf 档可不加缓冲
        body += ["-bufsize", bufsize]
    if profile["scale"]:                                   # 该档需要缩放分辨率
        body += ["-vf", f"scale={profile['scale']}"]
    body += ["-r", FRAME_RATE]                             # 帧率，沿用原脚本

    # -y 表示不询问直接写；成品名已保证不重复，这里只是防御性写法
    return ["ffmpeg", "-y", "-i", str(src), "-vcodec", "h264"] + body + [str(dst)]


# ========================== 日志 ==========================

# 表头只在 log.csv 首次创建时写一次；逗号分隔，文件名含逗号/引号会自动转义，可直接双击用 Excel 打开
LOG_HEADER = ["类型", "开始时间", "视频时长(分钟)", "结束时间",
              "耗时(分钟)", "状态", "文件名", "备注"]


def parse_video_minutes(stderr_text: str):
    """
    从 ffmpeg 的输出里抓 Duration 行，换算成分钟。
    :param stderr_text: ffmpeg 的 stderr 全文
    :return: 视频时长（分钟，float）；抓不到返回 None
    """
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", stderr_text or "")
    if not match:                                        # 坏文件等情况拿不到时长
        return None
    hours = int(match.group(1))                          # 小时
    minutes = int(match.group(2))                        # 分
    seconds = float(match.group(3))                      # 秒（可能带小数）
    return (hours * 3600 + minutes * 60 + seconds) / 60  # 统一换算成分钟


def write_log_row(log_path: Path, row: list):
    """
    往 log.csv 追加一行。文件不存在时先建文件、写 BOM 和表头。
    用 csv.writer 写，文件名里带逗号/引号也能正确转义。
    写日志失败只提示，不影响主流程。
    :param log_path: log.csv 的完整路径
    :param row: 与 LOG_HEADER 列数一致的字段列表
    """
    is_new = not log_path.exists()                       # 首次创建才写表头
    try:
        # newline="" 是 csv 模块的硬要求，否则 Windows 下会多出空行
        with log_path.open("a", encoding="utf-8", newline="") as fh:
            if is_new:
                fh.write("\ufeff")                       # BOM 只写这一次，Excel 打开不乱码
                csv.writer(fh).writerow(LOG_HEADER)
            csv.writer(fh).writerow(row)
    except OSError as exc:                               # 磁盘满/占用等异常
        print(f"⚠️ 日志写入失败：{exc}")


def append_log(log_path: Path, start_dt: datetime, video_min, end_dt: datetime,
               cost_sec: float, status: str, name: str):
    """
    往 log.csv 追加一条转码记录：
    开始时间、视频时长、结束时间、耗时、状态、文件名。
    """
    dur_text = f"{video_min:.2f}" if video_min is not None else "未知"
    write_log_row(log_path, [
        "视频",                                          # 记录类型
        start_dt.strftime("%Y-%m-%d %H:%M:%S"),          # 开始转码时间
        dur_text,                                        # 视频本身的长度（分钟）
        end_dt.strftime("%Y-%m-%d %H:%M:%S"),            # 结束时间
        f"{cost_sec / 60:.2f}",                          # 本次转码实际耗时（分钟）
        status,                                          # 转码成功 / 转码失败
        name,                                            # 文件名
        "",                                              # 备注留空
    ])


def append_disk_log(log_path: Path, passed: bool, free_bytes: float,
                    need_bytes: float, video_count: int):
    """
    把本次「磁盘空间检查」的结果写进 log.csv，带日期时间。
    :param passed: 检查是否通过
    """
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "通过" if passed else "不足，已终止"
    detail = (f"剩余 {format_size(free_bytes)}，需预留 {format_size(need_bytes)}"
              f"（{video_count} 个视频 × {EST_GB_PER_VIDEO} GB）")
    if not passed:                                       # 不足时把缺口也记下来
        detail += f"，还差 {format_size(need_bytes - free_bytes)}"
    write_log_row(log_path, [
        "磁盘检查",                                      # 记录类型
        stamp,                                           # 检查时间
        "",                                              # 视频时长（此类型不适用）
        "",                                              # 结束时间（此类型不适用）
        "",                                              # 耗时（此类型不适用）
        status,                                          # 通过 / 不足，已终止
        "",                                              # 文件名（此类型不适用）
        detail,                                          # 剩余 / 需预留 / 缺口
    ])


def transcode_one(src: Path, dst: Path, quality: str, log_path: Path):
    """
    转码单个文件，成功返回实际使用的成品路径，失败返回 None。
    无论成功失败，都会往 log.csv 追加一条记录。
    ffmpeg 的输出被捕获后按需显示，避免每个视频刷屏几十行。
    :param src: 源文件
    :param dst: 期望的成品路径（函数内部会自动去重）
    :param quality: 档位编号
    :param log_path: log.csv 的完整路径
    """
    real_dst = unique_path(dst)                            # 拿一个不会被占用的名字
    cmd = build_command(quality, src, real_dst)            # 拼命令
    start_dt = datetime.now()                              # 开始时间（写日志用）

    proc = subprocess.run(                                 # 同步执行并捕获输出
        cmd,
        capture_output=True,                               # 不直接往控制台刷
        text=True,                                         # 以文本形式返回
        encoding="utf-8",                                  # 固定编码
        errors="replace",                                  # 有乱码字符也不中断
    )

    end_dt = datetime.now()                                # 结束时间
    cost_sec = (end_dt - start_dt).total_seconds()         # 本次实际耗时（秒）
    video_min = parse_video_minutes(proc.stderr)           # 视频本身长度（分钟）

    if proc.returncode != 0:                               # ffmpeg 返回非 0 即失败
        print(f"❌ 转码失败：{src.name}")
        # 过滤掉版本横幅与编译配置这类噪声，只留真正的报错行
        noise = ("ffmpeg version", "  built with", "  configuration:",
                 "  libav", "  libsw", "  libpost")
        lines = [ln for ln in (proc.stderr or "").splitlines()
                 if ln.strip() and not ln.startswith(noise)]
        if lines:
            print("\n".join(lines[-15:]))                  # 只回显末尾 15 行
        if real_dst.exists():                              # 删掉残缺成品，避免污染 ok 目录
            real_dst.unlink()
        append_log(log_path, start_dt, video_min, end_dt,      # 失败也要留记录
                   cost_sec, "转码失败", src.name)
        return None

    # 成功：从 ffmpeg 输出里挑出那行统计信息（含 video: / audio:）
    for line in (proc.stderr or "").splitlines():
        if "video:" in line and "audio:" in line:
            print("   " + line.strip())

    print(f"✅ 转换完成：{src.name} → {real_dst.name}（耗时 {cost_sec:.1f} 秒）")
    append_log(log_path, start_dt, video_min, end_dt,          # 成功记录
               cost_sec, "转码成功", src.name)
    return real_dst


# ========================== 主流程 ==========================


def main() -> int:
    """
    批量处理入口。
    :return: 0 正常结束；1 环境不满足；2 有文件转码失败；3 磁盘空间不足
    """
    if not check_ffmpeg():                                 # 先确认依赖，缺了就退出
        return 1

    quality = choose_quality()                             # 菜单选档
    if quality is None:                                    # 选了空格 = 退出
        return 0

    root = Path.cwd()                                      # 工作目录 = 脚本被执行的目录
    videos = scan_videos(root)                             # 建立字典

    if not videos:                                         # 一个视频都没找到
        exts = "、".join(sorted(e.lstrip(".") for e in VIDEO_EXT))
        print(f"当前目录没有视频文件。（支持的扩展名：{exts}）")
        wait_space()                                       # 让窗口停一下，别闪退
        return 0

    print(f"待处理视频 {len(videos)} 个，档位 {quality} {PROFILES[quality]['label']}\n")

    log_path = root / LOG_FILE                             # 日志文件：当前目录下的 log.csv

    # 转码前的磁盘兜底检查：空间不够就直接终止，避免转一半写满盘
    if not check_disk_space(root, len(videos), log_path):
        wait_space()                                       # 留着窗口让用户看清报警
        return 3                                           # 3 = 磁盘空间不足

    out_dir = root / OUT_DIR                               # 成品目录
    src_dir = root / SRC_DIR                               # 源文件目录
    out_dir.mkdir(exist_ok=True)                           # 不存在就创建
    src_dir.mkdir(exist_ok=True)

    ok_count = 0                                           # 成功计数
    fail_count = 0                                         # 失败计数
    total_start = time.time()                              # 总计时起点

    for index, (src, dst) in enumerate(videos.items(), start=1):
        size_mb = src.stat().st_size / 1024 / 1024         # 源文件体积（MB）
        print(f"[{index}/{len(videos)}] {src.name}（{size_mb:.1f} MB）")

        real_dst = transcode_one(src, dst, quality, log_path)   # 转码（内部会写日志）
        if real_dst is None:                               # 失败：源文件原地保留，方便排查
            fail_count += 1
            continue

        # 先归档成品，再归档源文件；两者都用 unique_path，绝不覆盖已有文件
        shutil.move(str(real_dst), str(unique_path(out_dir / real_dst.name)))
        shutil.move(str(src), str(unique_path(src_dir / src.name)))
        ok_count += 1

        if REST_SECONDS > 0 and index < len(videos):       # 最后一个不必再等
            time.sleep(REST_SECONDS)

    total_cost = time.time() - total_start                 # 总耗时

    print("\n==== 全部任务执行完毕 ====")
    print(f"成功 {ok_count} 个，失败 {fail_count} 个，总耗时 {total_cost / 60:.1f} 分钟")
    print(f"成品目录：{out_dir}")
    print(f"源文件目录：{src_dir}")
    print(f"日志文件：{log_path}")

    wait_space()                                           # 和菜单同一个退出键
    return 0 if fail_count == 0 else 2                     # 交给系统/调用方判断结果


if __name__ == "__main__":                                 # 只有直接运行时才执行
    try:
        code = main()                                      # 跑主流程
    except KeyboardInterrupt:                              # Ctrl+C 也能干净退出
        print("\n已中断。")
        code = 130
    sys.exit(code)
