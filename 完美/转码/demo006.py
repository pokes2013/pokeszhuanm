
import time
import os
def xiuxi(xiuxi_time=300):
    while xiuxi_time > 0:
        print("程序休息300秒倒计时：", xiuxi_time, "秒")
        xiuxi_time -= 1
        time.sleep(1)
        os.system('cls')


xiuxi()
