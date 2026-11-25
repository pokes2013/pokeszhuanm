import os
import re

import requests


def html():
    """
    获取网页源代码，写入到yuadaima.txt
    """
    url = input("请输入你的网址:")
    # url = "https://avmoo.online/cn/series/5019cd7b9d64f152"
    # print(url)
    url = url.replace("https", "http")

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
        "Cookie": "your cookie"}

    response = requests.get(url, headers=header)

    if response.status_code == 200:
        html_content = response.text
        # print(html_content)
        with open("yuadaima.txt", 'w', encoding='UTF-8') as fff:
            fff.write(html_content)


def html_duoye(url):
    """
    获取网页源代码，写入到yuadaima.txt
    """
    # url = input("请输入你的网址:")
    # url = "https://avmoo.online/cn/series/5019cd7b9d64f152"
    # print(url)
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


def extract_string_between_symbols(text, start_symbol, end_symbol):
    """
    截取两个字符串之间的字符串
    """


    pattern = f"{start_symbol}(.*?){end_symbol}"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None


def get_duoye_url_list():

    """
    获取多页的url,返回一个列表，使用时请判断是否为空

    """


    aburl_list = []
    com = "https://avmoo.online/"
    # url = "https://avmoo.online/cn/series/6b127c02eff776a4"
    url = input("请输入你的网址：")
    url = url.replace("https", "http")
    # print(url)

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
        "Cookie": "your cookie"}

    response = requests.get(url, headers=header)
    if response.status_code == 200:
        html_content = response.text

        # 页码和章节提取，这里需要注意的是re.findall提取标签之间的内容，没有标签是不行的，返回的结果是一个list
        yema_list = re.findall('<a name="numbar"  href=".*?">.*?</a>', html_content)

        for yema in yema_list:
            # print(yema)
            yema_url = extract_string_between_symbols(yema, '/', '">')
            zhangjie = extract_string_between_symbols(yema, ">", "<")

            aburl = com + yema_url
            aburl_list.append(aburl)
            # print(yema_url)
            # print(zhangjie)
            # print(aburl)
    else:
        print("无法访问")
    return aburl_list




get_duoye_url_list()

if len(get_duoye_url_list()) == 0:
    for url in get_duoye_url_list():
        html_duoye(url)

    pass
else:
    print("只有1页")

    html()

    list_title=[]
    list_vido_info = []
    list_id_any = []
    with open("yuadaima.txt", 'r', encoding='UTF-8') as file:
        # print(file.readline())
        for line in file:
            line = line.rstrip('\n')
            if "<title>" in line:
                title = extract_string_between_symbols(line, "<title>", "</title>")
                list_title.append(title)


            if "<span>" in line:
                # name = extract_string_between_symbols(line, "<span>", "</span>")
                name = extract_string_between_symbols(line, "<span>", "<")
                # name = name.split("<", 1)[0]
                # print(name)
                id = extract_string_between_symbols(line, "<date>", "</date>")
                date = extract_string_between_symbols(line, "/ <date>", "</date></span>")
                id_name = id + "~" + name + "~" + date
                list_vido_info.append(id_name)

                id_pokes = id_name.split("~")[0:1]
                id_pokes = ''.join(id_pokes)
                list_id_any.append(id_pokes)

            # print(id_pokes)





# 写入title的信息
title = ''.join(list_title)
with open("yuadaima-已处理.txt", 'w', encoding='UTF-8') as file:
    # print(title)
    file.write(title)
    file.write("\n" * 2)

# 写入搜索的信息
sousuo = '|'.join(list_id_any)
with open("yuadaima-已处理.txt", 'a', encoding='UTF-8') as file:
    print(sousuo)
    file.write(sousuo)
    file.write("\n"*3)
    file.write("*" * 60)
    file.write("\n" * 3)

# 写入每一行的详细信息
for avinfo in list_vido_info:
    if "【VR】" not in avinfo:
        with open("yuadaima-已处理.txt", 'a', encoding='UTF-8') as file:
            print(avinfo)
            file.write(avinfo+"\n")
