import os
import re

import requests

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


def tiqu_yuandaima():
    list_title = []
    list_vido_info = []
    list_id_any = []
    with open("yuadaima.txt", 'r', encoding='UTF-8') as file:
        # print(file.readline())
        for line in file:
            line = line.rstrip('\n')

            if "<title>" in line:
                title = extract_string_between_symbols(line, "<title>", "</title>")
                # print(title)
                list_title.append(title)

            if "<span>" in line:
                name = extract_string_between_symbols(line, "<span>", "<")
                name = name.split("<", 1)[0]
                # print(name)
                id = extract_string_between_symbols(line, "<date>", "</date>")
                date = extract_string_between_symbols(line, "/ <date>", "</date></span>")

                print(name)

                # id_name = id + "~" + name + "~" + date
                # print(id_name)
                # list_vido_info.append(id_name)
                #
                # id_pokes = id_name.split("~")[0:1]
                # id_pokes = ''.join(id_pokes)
                # list_id_any.append(id_pokes)
    #
    #     # 写入title的信息
    # title = ''.join(list_title)
    # with open("yuadaima-已处理.txt", 'w', encoding='UTF-8') as file:
    #     # print(title)
    #     file.write(title)
    #     file.write("\n" * 2)
    #
    # # 写入搜索的信息
    # sousuo = '|'.join(list_id_any)
    # with open("yuadaima-已处理.txt", 'a', encoding='UTF-8') as file:
    #     print(sousuo)
    #     file.write(sousuo)
    #     file.write("\n" * 3)
    #     file.write("*" * 60)
    #     file.write("\n" * 3)
    #
    # # 写入每一行的详细信息
    #
    # for avinfo in list_vido_info:
    #     if "【VR】" not in avinfo:
    #         with open("yuadaima-已处理.txt", 'a', encoding='UTF-8') as file:
    #             print(avinfo)
    #             file.write(avinfo + "\n")


tiqu_yuandaima()