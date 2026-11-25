#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检测与安装模块。可独立运行，也可被主脚本 import。

独立运行：
    python install_deps.py          # 检测并安装缺失依赖
    python install_deps.py --check  # 只检测不安装

被调用：
    from install_deps import ensure_all_deps
    if not ensure_all_deps():
        sys.exit(1)

安装源：
    - pip 包：阿里云 PyPI 镜像
    - ffmpeg：
        Windows  → winget install Gyan.FFmpeg
        Ubuntu   → apt-get + 阿里云临时源（不改系统 sources.list）
        其他     → 打印手动安装指引
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ==================== 配置 ====================

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

# 需要的第三方 pip 包。当前只用标准库，为空。
# 将来加依赖填这里，例如 ["requests", "tqdm"]，启动时自动用阿里云源装。
REQUIRED_PIP_PACKAGES: list = []

# 需要的外部命令
REQUIRED_COMMANDS = ["ffmpeg", "ffprobe"]


# ==================== pip 包 ====================

def ensure_pip_packages(packages=None) -> bool:
    """检测并自动安装缺失的 Python 包，使用阿里云源。"""
    if packages is None:
        packages = REQUIRED_PIP_PACKAGES
    if not packages:
        return True

    import importlib.util
    missing = [p for p in packages if importlib.util.find_spec(p) is None]
    if not missing:
        print(f"[pip] 依赖已就绪：{', '.join(packages)}")
        return True

    print(f"[pip] 缺失：{', '.join(missing)}，使用阿里云源安装...")
    cmd = [
        sys.executable, "-m", "pip", "install",
        "-i", ALIYUN_PIP_INDEX,
        "--trusted-host", ALIYUN_PIP_HOST,
        *missing,
    ]
    print("[pip] 执行：" + " ".join(cmd))
    try:
        ret = subprocess.run(cmd).returncode
    except FileNotFoundError:
        print("[pip] 找不到 pip，请手动执行上面的命令。")
        return False
    if ret != 0:
        print("[pip] 安装失败，请检查网络。")
        return False

    still = [p for p in missing if importlib.util.find_spec(p) is None]
    if still:
        print(f"[pip] 安装后仍检测不到：{', '.join(still)}")
        return False
    print("[pip] 安装完成。")
    return True


# ==================== 外部命令 ====================

def _run(cmd: list, desc: str = "") -> int:
    if desc:
        print(desc)
    print("[cmd] 执行：" + " ".join(cmd))
    try:
        return subprocess.run(cmd).returncode
    except FileNotFoundError:
        print(f"[cmd] 命令不存在：{cmd[0]}")
        return -1


def _is_root() -> bool:
    if sys.platform.startswith("win"):
        return False
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def _sudo_wrap(cmd: list) -> list:
    if _is_root():
        return cmd
    sudo = shutil.which("sudo")
    return [sudo] + cmd if sudo else cmd


def _has_sudo_n() -> bool:
    """免密 sudo 是否可用。双击运行场景下不能卡在密码输入。"""
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
    """Ubuntu/Debian 用阿里云临时源安装 ffmpeg，不改系统 sources.list。"""
    if not (_is_root() or _has_sudo_n()):
        print("[ffmpeg] 自动安装需要 root 或免密 sudo。")
        print("[ffmpeg] 请手动执行：sudo apt-get install -y ffmpeg")
        return False

    codename = _get_ubuntu_codename()
    if not codename:
        print("[ffmpeg] 无法确定 Ubuntu 代号，改用系统默认源。")
        if _run(_sudo_wrap(["apt-get", "update"]), "[ffmpeg] apt-get update") != 0:
            return False
        return _run(
            _sudo_wrap(["apt-get", "install", "-y", "ffmpeg"]),
            "[ffmpeg] apt-get install ffmpeg",
        ) == 0

    tmp_sources = Path(tempfile.gettempdir()) / "aliyun-ubuntu-sources.list"
    tmp_sources.write_text(
        ALIYUN_UBUNTU_SOURCES.format(codename=codename), encoding="utf-8"
    )
    print(f"[ffmpeg] 临时阿里云源：{tmp_sources}")

    opts = [
        "-o", f"Dir::Etc::sourcelist={tmp_sources}",
        "-o", "Dir::Etc::sourceparts=-",
        "-o", "APT::Get::List-Cleanup=0",
    ]
    if _run(
        _sudo_wrap(["apt-get", *opts, "update"]),
        "[ffmpeg] apt-get update（阿里云源）",
    ) != 0:
        print("[ffmpeg] 阿里云源 update 失败，尝试系统默认源。")
        if _run(_sudo_wrap(["apt-get", "update"])) != 0:
            return False
        return _run(
            _sudo_wrap(["apt-get", "install", "-y", "ffmpeg"]),
            "[ffmpeg] apt-get install ffmpeg",
        ) == 0

    return _run(
        _sudo_wrap(["apt-get", *opts, "install", "-y", "ffmpeg"]),
        "[ffmpeg] apt-get install ffmpeg（阿里云源）",
    ) == 0


def _install_ffmpeg_windows() -> bool:
    winget = shutil.which("winget")
    if not winget:
        print("[ffmpeg] 未找到 winget，无法自动安装。")
        print("[ffmpeg] 请从 https://www.gyan.dev/ffmpeg/builds/ 下载解压，")
        print("[ffmpeg] 把 bin 目录加入系统 PATH。")
        return False
    return _run(
        [
            winget, "install", "Gyan.FFmpeg",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ],
        "[ffmpeg] 通过 winget 安装",
    ) == 0


def _install_ffmpeg_linux() -> bool:
    if shutil.which("apt-get"):
        return _install_ffmpeg_apt()
    if shutil.which("dnf") or shutil.which("yum"):
        print("[ffmpeg] 检测到 RPM 系发行版，请手动安装：")
        print("  sudo dnf install -y ffmpeg   # 或 sudo yum install -y ffmpeg")
        return False
    print("[ffmpeg] 无法识别包管理器，请手动安装 ffmpeg 并加入 PATH。")
    return False


def ensure_commands(commands=None, auto_install: bool = True) -> bool:
    """
    检测外部命令，缺失且 auto_install=True 时尝试自动安装。
    """
    if commands is None:
        commands = REQUIRED_COMMANDS

    paths = {c: shutil.which(c) for c in commands}
    missing = [c for c, p in paths.items() if not p]

    if not missing:
        for c, p in paths.items():
            print(f"[cmd] {c}：{p}")
        return True

    print(f"[cmd] 缺失：{', '.join(missing)}")
    if not auto_install:
        return False

    if sys.platform.startswith("win"):
        ok = _install_ffmpeg_windows()
    elif sys.platform.startswith("linux"):
        ok = _install_ffmpeg_linux()
    else:
        print(f"[cmd] 当前平台 {sys.platform} 不支持自动安装。")
        return False

    if not ok:
        return False

    # 安装后再查一次（winget 有时需要新会话才更新 PATH）
    paths = {c: shutil.which(c) for c in commands}
    missing = [c for c, p in paths.items() if not p]
    if missing:
        print(f"[cmd] 安装命令已执行，但仍检测不到：{', '.join(missing)}")
        print("[cmd] 请关闭本窗口重新打开，或检查 PATH。")
        return False

    print(f"[cmd] 安装成功：{', '.join(commands)}")
    return True


# ==================== 统一入口 ====================

def ensure_all_deps(
    check_only: bool = False,
    pip_packages=None,
    commands=None,
) -> bool:
    """
    检测（并可选安装）所有依赖。
    返回 True 表示全部就绪。

    check_only=True 时只检测不安装，适合 CI 或自检。
    """
    print("=" * 60)
    print("依赖检测" + ("（仅检测）" if check_only else ""))
    print("=" * 60)

    ok_pip = ensure_pip_packages(pip_packages)
    if not ok_pip:
        return False

    ok_cmd = ensure_commands(commands, auto_install=not check_only)
    if not ok_cmd:
        return False

    print("=" * 60)
    print("依赖全部就绪")
    print("=" * 60)
    return True


# ==================== 独立运行 ====================

if __name__ == "__main__":
    check_only = "--check" in sys.argv
    ok = ensure_all_deps(check_only=check_only)
    if not ok:
        print("\n依赖未就绪，请按上面的提示处理。")
        try:
            input("按回车退出...")
        except EOFError:
            pass
        sys.exit(1)
    if not check_only:
        print("\n依赖已就绪，可以运行主脚本了。")
    else:
        print("\n检测通过。")
    try:
        input("按回车退出...")
    except EOFError:
        pass