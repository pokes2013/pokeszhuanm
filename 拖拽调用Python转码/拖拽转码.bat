@echo off
chcp 65001 >nul
:: 调用同目录下 transcode.py，把所有拖拽传入的文件全部传给python脚本
python transcode.py %*

echo.
echo ======================================
echo 脚本执行结束
echo 按回车键关闭窗口
pause >nul