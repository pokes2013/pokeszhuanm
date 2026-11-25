# url = "https://avmoo.online/cn/movie/79eda1e38cf394de"
# url = "https://www.cnblogs.com/pokess/p/17068458.html"


import os
import time

import requests


# 下面是OK的

def html(url):
    if os.path.exists("yuadaima.txt"):
        os.remove("yuadaima.txt")

    # url = input("请输入你的网址:")


    url = url.replace("https", "http")

    header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
            "Cookie": "your cookie"}

    response = requests.get(url, headers=header)

        if response.status_code == 200:
            html_content = response.text
            # print(html_content)
            with open("yuadaima.txt", 'a', encoding='UTF-8') as fff:
                fff.write(html_content)

        time.sleep(1)


html("https://avmoo.online/cn/series/6b127c02eff776a4")
