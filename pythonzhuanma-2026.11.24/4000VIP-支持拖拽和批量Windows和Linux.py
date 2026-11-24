#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拖拽转码：1080p H.264 压缩，源文件归档到 source_data/，成品放入 OK/。

==================================================================
运行方式
==================================================================
Windows：
    双击脚本            → 扫描脚本所在目录的视频，逐个转码
    拖拽文件到脚本上    → 只处理拖入的文件

Linux：
    ./transcode.py                  → 扫描脚本所在目录的视频
    ./transcode.py a.mp4 b.mkv      → 只处理参数指定的文件

==================================================================
启动流程
==================================================================
1. 检测 Python 第三方依赖（当前无，留空；将来加包走阿里云 pip 源）
2. 检测 ffmpeg / ffprobe，缺失时自动安装（Windows: winget；Ubuntu: apt + 阿里云源）
3. 准备 OK/、source_data/ 目录，确定日志路径
4. 确定待处理文件列表（有参数用参数，无参数扫脚本目录）
5. 逐个文件处理：
   - 处理前实时检查三处磁盘剩余空间 >= 5G，不足则记日志并中断整个循环
   - 转码 → 校验 → 原子改名 → 移动源文件/成品
   - 写日志（成功/失败/空间不足）

==================================================================
日志格式
==================================================================
成功：开始时间 | 文件名 | 时长 | 转换前大小 | 耗时 | 转码成功 | 转换后大小
失败：开始时间 | 文件名 | 转码失败
空间不足：开始时间 | 文件名 | 转码失败（空间不足）
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


# ==================================================================
#                          配  置  区
# 想改参数，全部在这个区里改，不用动下面的函数
# ==================================================================

OUTPUT_FOLDER = "OK"           # 成品输出目录（相对脚本目录）
SOURCE_FOLDER = "source_data"  # 源文件归档目录（相对脚本目录）
LOG_FILE = "logs.txt"          # 日志文件名
MIN_FREE_GB = 5.0              # 每个文件处理前要求的最小剩余空间（GB）

# 视为视频的扩展名（小写，比较时会统一转小写，所以 .MP4/.Mkv 也能识别）
VIDEO_EXTS = {
    ".mp4", ".mkv", ".mov", ".avi", ".flv",
    ".wmv", ".webm", ".m4v", ".ts", ".mpg", ".mpeg",
}

# 脚本所在目录。所有产物（OK/、source_data/、logs.txt）都以它为准，
# 而不是 Path.cwd()——Windows 双击时 cwd 有时不是脚本目录。
BASE_DIR = Path(__file__).resolve().parent

# 日志文件最终路径，main() 里探测后赋值；None 表示降级到 stderr
LOG_PATH: Optional[Path] = None

# ------------------------------------------------------------------
# ffmpeg 转码参数
# ------------------------------------------------------------------
# 这里是"要转成什么样"的全部控制点，改完保存即可。
#
# 参数速查：
#   -vcodec  视频编码器：h264 / libx265 / h264_nvenc(N卡) / h264_qsv(Intel)
#   -preset  速度档位：ultrafast > superfast > veryfast > fast > medium
#            越靠前越快但体积越大；veryfast 是速度/压缩率平衡点
#   -crf     画质：越小越清晰体积越大。18≈无损 19=默认 23=网盘 26=存档
#   -r       强制帧率。★ 注意：不是"保持原帧率"，会改源帧率
#            原 bat 遗留，可能导致 29.97fps 音画不同步、60fps 变卡
#            建议删掉这一项，让 ffmpeg 沿用源帧率
#   -vf      scale=1920:-2 是"宽度拉到1920，高按比例取偶数"
#            ★ 竖屏视频会被放大，改成下面的"竖屏安全版"更稳妥
#   -c:a     音频编码。当前未指定，行为不固定
#            明确写 -c:a aac -b:a 192k 更可控
# ------------------------------------------------------------------
FFMPEG_ARGS = [
    "-vcodec", "h264",          # H.264 编码
    "-preset", "veryfast",      # 编码速度档
    "-crf", "19",
    "-maxrate", "1800k",
    "-bufsize", "2000k",
    "-vf", "scale=1280:-2",     # 宽度拉到 1920，高按比例
    # 竖屏安全版替代下面这行（把上面那行 -vf 注释掉，换这行）：
    # "-vf", "scale='if(gt(iw,ih),1920,-2)':'if(gt(iw,ih),-2,1920)'",
    # 明确音频编码，把下面两项取消注释（放在 -vf 之后即可）：
    # "-c:a", "aac", "-b:a", "192k",
]


# ==================================================================
#                     依 赖 检 测 与 安 装
# ==================================================================

# 阿里云 pip 源
ALIYUN_PIP_INDEX = "https://mirrors.aliyun.com/pypi/simple/"
ALIYUN_PIP_HOST = "mirrors.aliyun.com"

# 阿里云 Ubuntu 源模板，{codename} 用 lsb_release -cs 填充（jammy/focal/noble…）
ALIYUN_UBUNTU_SOURCES = """\
deb https://mirrors.aliyun.com/ubuntu/ {codename} main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ {codename}-updates main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ {codename}-backports main restricted universe multiverse
deb https://mirrors.aliyun.com/ubuntu/ {codename}-security main restricted universe multiverse
"""

# 本脚本需要的第三方 pip 包。
# 当前只用标准库，所以为空。将来加依赖就填这里，例如 ["requests", "tqdm"]，
# 启动时会自动用阿里云源安装缺失的包。
REQUIRED_PIP_PACKAGES: list = []


def ensure_pip_packages(packages=None) -> bool:
    """
    检测并自动安装缺失的 Python 包，使用阿里云源。
    返回 True 表示全部就绪（包括原本就没有依赖的情况）。
    """
    if packages is None:
        packages = REQUIRED_PIP_PACKAGES
    if not packages:
        return True                         # 当前无第三方依赖，直接通过

    import importlib.util
    missing = [p for p in packages if importlib.util.find_spec(p) is None]
    if not missing:
        print(f"Python 依赖已就绪：{', '.join(packages)}")
        return True

    print(f"缺失 Python 包：{', '.join(missing)}，使用阿里云源安装...")
    cmd = [
        sys.executable, "-m", "pip", "install",
        "-i", ALIYUN_PIP_INDEX,
        "--trusted-host", ALIYUN_PIP_HOST,
        *missing,
    ]
    print("执行：" + " ".join(cmd))
    try:
        ret = subprocess.run(cmd).returncode
    except FileNotFoundError:
        print("找不到 pip，请手动执行上面的命令。")
        return False
    if ret != 0:
        print("pip 安装失败，请检查网络。")
        return False

    # 安装后再验证一遍，防止装到别的 Python 环境
    still = [p for p in missing if importlib.util.find_spec(p) is None]
    if still:
        print(f"安装后仍检测不到：{', '.join(still)}")
        return False
    print("Python 依赖安装完成。")
    return True


def _run(cmd: list, desc: str = "") -> int:
    """执行一条命令，打印命令行和描述，返回 returncode。"""
    if desc:
        print(desc)
    print("执行：" + " ".join(cmd))
    try:
        return subprocess.run(cmd).returncode
    except FileNotFoundError:
        print(f"命令不存在：{cmd[0]}")
        return -1


def _is_root() -> bool:
    """是否 root 用户（仅 POSIX 有 geteuid）。"""
    if sys.platform.startswith("win"):
        return False
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def _sudo_wrap(cmd: list) -> list:
    """非 root 且系统有 sudo 时，给命令加 sudo 前缀。"""
    if _is_root():
        return cmd
    sudo = shutil.which("sudo")
    return [sudo] + cmd if sudo else cmd


def _has_sudo_n() -> bool:
    """
    免密 sudo 是否可用。
    双击运行场景下不能卡在密码输入，必须先确认这一点。
    """
    sudo = shutil.which("sudo")
    if not sudo:
        return False
    try:
        return subprocess.run(
            [sudo, "-n", "true"], capture_output=True
        ).returncode == 0
    except Exception:
        return False


def _get_ubuntu_codename() -> str:
    """获取 Ubuntu 代号，如 jammy / focal / noble。失败返回空串。"""
    try:
        out = subprocess.run(
            ["lsb_release", "-cs"], capture_output=True, text=True
        ).stdout.strip()
        if out:
            return out
    except Exception:
        pass
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("VERSION_CODENAME="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return ""


def _install_ffmpeg_apt() -> bool:
    """
    Ubuntu/Debian 用阿里云临时源安装 ffmpeg。
    临时源写在 /tmp 下，通过 apt-get -o 指定，不改系统 /etc/apt/sources.list。
    """
    # 双击运行场景下不能卡在 sudo 密码，必须 root 或免密 sudo 才自动装
    if not (_is_root() or _has_sudo_n()):
        print("自动安装 ffmpeg 需要 root 或免密 sudo。")
        print("请手动执行：sudo apt-get install -y ffmpeg")
        return False

    codename = _get_ubuntu_codename()
    if not codename:
        print("无法确定 Ubuntu 版本代号，改用系统默认源。")
        if _run(_sudo_wrap(["apt-get", "update"]), "apt-get update") != 0:
            return False
        return _run(
            _sudo_wrap(["apt-get", "install", "-y", "ffmpeg"]),
            "apt-get install ffmpeg",
        ) == 0

    # 生成临时阿里云 sources.list，不改系统原文件
    tmp_sources = Path(tempfile.gettempdir()) / "aliyun-ubuntu-sources.list"
    tmp_sources.write_text(
        ALIYUN_UBUNTU_SOURCES.format(codename=codename), encoding="utf-8"
    )

    # 通过 -o 参数让本次 apt-get 只用这个临时源
    opts = [
        "-o", f"Dir::Etc::sourcelist={tmp_sources}",
        "-o", "Dir::Etc::sourceparts=-",
        "-o", "APT::Get::List-Cleanup=0",
    ]
    if _run(
        _sudo_wrap(["apt-get", *opts, "update"]),
        "apt-get update（阿里云源）",
    ) != 0:
        print("阿里云源 update 失败，尝试系统默认源。")
        if _run(_sudo_wrap(["apt-get", "update"])) != 0:
            return False
        return _run(
            _sudo_wrap(["apt-get", "install", "-y", "ffmpeg"]),
            "apt-get install ffmpeg",
        ) == 0

    return _run(
        _sudo_wrap(["apt-get", *opts, "install", "-y", "ffmpeg"]),
        "apt-get install ffmpeg（阿里云源）",
    ) == 0


def _install_ffmpeg_windows() -> bool:
    """Windows：通过 winget 安装 ffmpeg。"""
    winget = shutil.which("winget")
    if not winget:
        print("未找到 winget，无法自动安装 ffmpeg。")
        print("请从 https://www.gyan.dev/ffmpeg/builds/ 下载解压，")
        print("把解压后的 bin 目录加入系统 PATH。")
        return False
    return _run(
        [
            winget, "install", "Gyan.FFmpeg",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ],
        "通过 winget 安装 ffmpeg",
    ) == 0


def _install_ffmpeg_linux() -> bool:
    """Linux：优先 apt-get（Ubuntu/Debian），其他发行版给出提示。"""
    if shutil.which("apt-get"):
        return _install_ffmpeg_apt()
    if shutil.which("dnf") or shutil.which("yum"):
        print("检测到 RPM 系发行版，请手动安装 ffmpeg：")
        print("  sudo dnf install -y ffmpeg   # 或 sudo yum install -y ffmpeg")
        print("（本脚本自动安装仅支持 Ubuntu/Debian）")
        return False
    print("无法识别包管理器，请手动安装 ffmpeg 并加入 PATH。")
    return False


def ensure_ffmpeg() -> bool:
    """
    检测 ffmpeg / ffprobe 是否可用，缺失时尝试自动安装。
    返回 True 表示两个命令都能用。
    """
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg and ffprobe:
        print(f"ffmpeg ：{ffmpeg}")
        print(f"ffprobe：{ffprobe}")
        return True

    missing = []
    if not ffmpeg:
        missing.append("ffmpeg")
    if not ffprobe:
        missing.append("ffprobe")
    print(f"缺失外部命令：{', '.join(missing)}")

    if sys.platform.startswith("win"):
        ok = _install_ffmpeg_windows()
    elif sys.platform.startswith("linux"):
        ok = _install_ffmpeg_linux()
    else:
        print(f"当前平台 {sys.platform} 不支持自动安装，请手动安装。")
        return False

    if not ok:
        return False

    # 安装后再查一次（winget 有时需要新会话才更新 PATH）
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg and ffprobe:
        print(f"ffmpeg 安装成功：{ffmpeg}")
        return True

    print("安装命令已执行，但当前会话仍检测不到 ffmpeg。")
    print("请关闭本窗口重新打开，或检查 PATH。")
    return False


# ==================================================================
#                        通  用  工  具
# ==================================================================

def ensure_folder(folder: Path) -> None:
    """目录不存在则创建，存在则打印提示。"""
    if folder.exists():
        print(f"{folder.name}目录存在")
    else:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"{folder.name}创建成功")


def wait_exit() -> None:
    """
    结尾等待回车。
    EOFError 保护：让管道/后台运行（stdin 不可交互）不会崩。
    """
    try:
        input("按回车退出...")
    except EOFError:
        pass


def resolve_log_path() -> Optional[Path]:
    """
    依次尝试脚本目录 → 用户数据目录 → 系统临时目录，
    返回第一个可写的日志路径；全部不可写返回 None。
    """
    candidates = [
        BASE_DIR / LOG_FILE,
        Path.home() / ".local" / "share" / "transcode" / LOG_FILE,
        Path(tempfile.gettempdir()) / f"transcode_{LOG_FILE}",
    ]
    for c in candidates:
        try:
            c.parent.mkdir(parents=True, exist_ok=True)
            with open(c, "a", encoding="utf-8"):
                pass
            return c
        except OSError:
            continue
    return None


def write_log(line: str) -> None:
    """
    追加一行日志。
    日志路径不可用或写入失败时降级到 stderr，不中断转码。
    """
    if LOG_PATH is None:
        print("[日志无法写入] " + line, file=sys.stderr)
        return
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as e:
        print(f"[日志写入失败 {e}] " + line, file=sys.stderr)


def unique_path(folder: Path, name: str) -> Path:
    """
    folder/name 已存在时，依次尝试 name_1、name_2…… 返回第一个不存在的路径。
    用于避免覆盖 OK/、source_data/、源目录里的同名文件。
    """
    p = folder / name
    if not p.exists():
        return p
    stem, suffix = p.stem, p.suffix
    i = 1
    while True:
        p = folder / f"{stem}_{i}{suffix}"
        if not p.exists():
            return p
        i += 1


def size_gb(path: Path) -> float:
    """文件大小，单位 GB。"""
    return path.stat().st_size / (1024 ** 3)


def duration_minutes(path: Path):
    """
    用 ffprobe 读时长（分钟）。读不到返回 None，日志里写"未知"。
    """
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return float(out) / 60
    except Exception:
        return None


def fmt_elapsed(seconds: float) -> str:
    """秒数格式化为"X分Y秒"或"Y秒"。"""
    total = int(seconds)
    m, s = divmod(total, 60)
    return f"{m}分{s}秒" if m else f"{s}秒"


def check_space(paths, min_gb: float = MIN_FREE_GB) -> bool:
    """
    检查 paths 中每个路径所在磁盘的实时剩余空间。
    全部 >= min_gb 返回 True；任意一个不足或查询失败返回 False。

    ★ 关键：这是实时查询，调用一次查一次，不是任务启动时的快照。
      配合主循环，做到"每个文件处理前都查一遍"。
    """
    for p in paths:
        try:
            free_gb = shutil.disk_usage(p).free / (1024 ** 3)
        except OSError as e:
            print(f"无法检测 {p} 所在磁盘空间：{e}")
            return False
        if free_gb < min_gb:
            print(f"可用空间不足：{p} 所在磁盘仅 {free_gb:.2f}G < {min_gb:.0f}G")
            return False
    return True


# ==================================================================
#                        目  录  扫  描
# ==================================================================

def scan_dir(base: Path, exclude: set[Path]) -> list[Path]:
    """
    扫描 base 下一层的视频文件（不递归）。
    - 扩展名比较时统一转小写，.MP4/.Mkv 也能识别；
    - 去掉尾随空格和点，兼容 "a.mp4 " 和 "a.mp4." 这类不规范命名；
    - exclude 里的路径（OK/、source_data/）跳过，防止把成品当源文件。
    """
    found = []
    try:
        entries = sorted(base.iterdir())
    except OSError as e:
        print(f"无法读取目录 {base}：{e}")
        return found

    exts = tuple(VIDEO_EXTS)  # endswith 接受元组
    for p in entries:
        if not p.is_file():
            continue
        # 大小写归一 + 去尾随空格/点后再判断扩展名
        name_lower = p.name.lower().strip().rstrip(".")
        if not name_lower.endswith(exts):
            continue
        try:
            if p.resolve() in exclude:
                continue
        except OSError:
            continue
        found.append(p)
    return found


# ==================================================================
#                          转  码
# ==================================================================

def transcode(src: Path, output_dir: Path, source_dir: Path):
    """
    转码单个文件。

    成功返回成品最终路径（可能在 OK/ 里被改名为 xxx_ok_1.mp4）；
    失败返回 None，并保证：源文件未动、临时文件已清理。

    步骤：
    1. 临时文件先写在源目录（同分区 rename 是原子的）
    2. ffmpeg 转码到临时文件
    3. 校验返回码 + 文件存在 + 非 0 字节
    4. 临时文件 → 源目录里的最终名（原子改名）
    5. 源文件 → source_data/（重名加序号）
    6. 成品 → OK/（重名加序号）
    """
    # 临时文件放源目录，前缀点表示隐藏，.part 表示未完成
    tmp = src.with_name(f".{src.stem}_ok.part.mp4")
    # 源目录里的最终名，unique_path 避免覆盖上次残留的 _ok.mp4
    final_dst = unique_path(src.parent, f"{src.stem}_ok.mp4")

    # 组装命令：ffmpeg -y -i 源文件 <FFMPEG_ARGS> 临时文件
    cmd = ["ffmpeg", "-y", "-i", str(src), *FFMPEG_ARGS, str(tmp)]
    print("执行：" + " ".join(cmd))

    try:
        ret = subprocess.run(cmd).returncode
    except FileNotFoundError:
        # ffmpeg 不在 PATH（正常不会走到，ensure_ffmpeg 已检测）
        print("找不到 ffmpeg，请确认已安装并加入 PATH。")
        return None
    except BaseException:
        # Ctrl+C / 被 kill 时也要清理临时文件，再原样抛
        tmp.unlink(missing_ok=True)
        raise

    # 返回码非 0、文件不存在、0 字节，都按失败处理
    if ret != 0 or not tmp.exists() or tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        print(f"转码失败，已清理临时文件：{src}")
        return None

    print("转换OK")

    # 临时文件 → 源目录里的最终名（同分区，原子改名）
    tmp.replace(final_dst)

    # 源文件 → source_data/，同名自动加序号，不覆盖
    dst_src = unique_path(source_dir, src.name)
    shutil.move(str(src), str(dst_src))

    # 成品 → OK/，同名自动加序号，不覆盖
    out_final = unique_path(output_dir, final_dst.name)
    shutil.move(str(final_dst), str(out_final))

    return out_final


# ==================================================================
#                          日  志
# ==================================================================

def log_success(
    start_dt: datetime,
    src_name: str,
    dur,
    size_before: float,
    elapsed: float,
    size_after: float,
) -> None:
    """
    成功日志：
    开始时间 | 文件名 | 时长 | 转换前大小 | 耗时 | 转码成功 | 转换后大小
    """
    line = " | ".join([
        start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        src_name,
        f"{dur:.1f}分钟" if dur is not None else "未知",
        f"{size_before:.2f}G",
        fmt_elapsed(elapsed),
        "转码成功",
        f"{size_after:.2f}G",
    ])
    write_log(line)
    print("日志：" + line)


def log_fail(
    start_dt: datetime, src_name: str, reason: Optional[str] = None
) -> None:
    """
    失败日志：开始时间 | 文件名 | 转码失败[（原因）]
    reason 为空时写"转码失败"；传"空间不足"时写"转码失败（空间不足）"。
    """
    status = "转码失败" if not reason else f"转码失败（{reason}）"
    line = " | ".join([
        start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        src_name,
        status,
    ])
    write_log(line)
    print("日志：" + line)


# ==================================================================
#                        主  流  程
# ==================================================================

def main() -> None:
    global LOG_PATH

    # ------------------------------------------------------------------
    # ① 依赖检测：Python 包（当前为空，将来加包走阿里云源）
    # ------------------------------------------------------------------
    if not ensure_pip_packages():
        print("Python 依赖未就绪，退出。")
        wait_exit()
        return

    # ------------------------------------------------------------------
    # ② 依赖检测：ffmpeg / ffprobe（winget / apt 阿里云源）
    # ------------------------------------------------------------------
    if not ensure_ffmpeg():
        print("ffmpeg 未就绪，退出。")
        wait_exit()
        return

    output_dir = BASE_DIR / OUTPUT_FOLDER
    source_dir = BASE_DIR / SOURCE_FOLDER

    # ------------------------------------------------------------------
    # ③ 自检：脚本不能放在 OK/ 或 source_data/ 里，
    #    否则扫描会捞到自己的产物，无限套娃
    # ------------------------------------------------------------------
    for reserved in (output_dir, source_dir):
        if BASE_DIR == reserved or reserved in BASE_DIR.parents:
            print(f"错误：脚本不能放在 {reserved.name}/ 目录中运行。")
            wait_exit()
            return

    # ------------------------------------------------------------------
    # ④ 确定待处理文件列表
    #    有参数：只处理参数里的文件（拖拽 / 命令行传参）
    #    无参数：扫描脚本目录（双击 / ./transcode.py）
    # ------------------------------------------------------------------
    files = [Path(p) for p in sys.argv[1:] if p.strip()]
    auto_scan = not files

    if auto_scan:
        exclude = {output_dir.resolve(), source_dir.resolve()}
        files = scan_dir(BASE_DIR, exclude)
        if not files:
            print(f"未传入文件，且 {BASE_DIR} 下没有找到可转码的视频。")
            wait_exit()
            return
        print(f"未传入文件，扫描 {BASE_DIR} 得到 {len(files)} 个视频：")
        for f in files:
            print("  " + f.name)
        print()

    # ------------------------------------------------------------------
    # ⑤ 准备目录、确定日志路径
    # ------------------------------------------------------------------
    ensure_folder(output_dir)
    ensure_folder(source_dir)

    LOG_PATH = resolve_log_path()
    if LOG_PATH is None:
        print("警告：日志无法写入任何位置，将输出到 stderr。", file=sys.stderr)

    processed = 0
    aborted = False

    # ------------------------------------------------------------------
    # ⑥ 逐个文件处理
    # ------------------------------------------------------------------
    for raw in files:
        src = raw.resolve()
        if not src.is_file():
            print(f"跳过（不是文件）：{src}")
            continue

        start_dt = datetime.now()

        # --------------------------------------------------------------
        # 每个文件处理前，实时检查三处磁盘剩余空间 >= 5G
        # output_dir：成品最终落盘处
        # src.parent：临时文件 .xxx.part.mp4 落盘处
        # source_dir：源文件移入处（跨盘 move 会占目标盘空间）
        # 任意一处不足 → 记"转码失败（空间不足）" → break 中断整个循环
        # --------------------------------------------------------------
        if not check_space([output_dir, src.parent, source_dir], MIN_FREE_GB):
            try:
                log_fail(start_dt, src.name, reason="空间不足")
            except Exception as e:
                print(f"日志写入失败：{e}")
            print("可用空间不足，中断整个任务。")
            processed += 1
            aborted = True
            break

        t0 = time.time()

        # --------------------------------------------------------------
        # 读源文件信息（失败不影响转码，日志里写 0/未知）
        # --------------------------------------------------------------
        try:
            size_before = size_gb(src)
            dur = duration_minutes(src)
        except Exception as e:
            print(f"读取源文件信息失败：{src} -> {e}")
            size_before = 0.0
            dur = None

        # --------------------------------------------------------------
        # 转码
        # --------------------------------------------------------------
        try:
            out = transcode(src, output_dir, source_dir)
        except KeyboardInterrupt:
            print("\n用户中断，退出。")
            sys.exit(130)
        except Exception as e:
            print(f"转码出错：{src} -> {e}")
            out = None

        elapsed = time.time() - t0

        # --------------------------------------------------------------
        # 写日志：成功/失败分开。
        # 日志本身写入失败只打 stderr，不误判为转码失败。
        # --------------------------------------------------------------
        if out is not None:
            try:
                size_after = size_gb(out)
            except Exception:
                size_after = 0.0
            try:
                log_success(
                    start_dt, src.name, dur, size_before, elapsed, size_after
                )
            except Exception as e:
                print(f"日志写入失败：{e}")
        else:
            try:
                log_fail(start_dt, src.name)
            except Exception as e:
                print(f"日志写入失败：{e}")

        processed += 1

    # ------------------------------------------------------------------
    # ⑦ 汇总
    # ------------------------------------------------------------------
    if aborted:
        remaining = len(files) - processed
        print(f"因空间不足中断：已处理 {processed} 个，剩余 {remaining} 个未处理。")
    else:
        print(f"全部处理完毕，共 {processed} 个文件。")

    wait_exit()


if __name__ == "__main__":
    main()
