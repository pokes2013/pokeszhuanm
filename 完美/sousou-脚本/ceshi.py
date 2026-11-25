import requests
import os
from urllib.parse import urlparse

def download_image(url, save_path):
    """
    下载图片并保存到指定路径。‌

    :param url: 图片的URL
    :param save_path: 图片保存的完整路径（‌包括文件名）‌
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 如果请求返回了不成功的状态码，‌则抛出HTTPError异常

        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # 过滤掉keep-alive新发送的空包
                    file.write(chunk)

        print(f'图片已保存到 {save_path}')
    except requests.RequestException as e:
        print(f'下载图片时发生错误：‌{e}')

def batch_download_images(urls, save_dir):
    """
    批量下载图片。‌

    :param urls: 包含图片URL的列表
    :param save_dir: 保存图片的目录
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)  # 如果目录不存在，‌则创建目录

    for index, url in enumerate(urls, start=1):
        # 解析URL以获取文件名（‌这里假设它是URL路径的最后一部分）‌
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)

        # 如果文件名为空（‌可能是URL的特殊情况）‌，‌则使用默认名称
        if not filename:
            filename = f'image_{index}.jpg'

        # 构造完整的保存路径
        save_path = os.path.join(save_dir, filename)

        # 调用download_image函数下载图片
        download_image(url, save_path)

# # 示例图片URL列表
# image_urls = [
#     'https://example.com/path/to/your/image1.jpg',
#     'https://example.com/another/image2.png',
#     # ... 添加更多图片URL
# ]

# # 指定保存图片的目录
# save_directory = 'downloaded_images'

# # 调用函数批量下载图片
# batch_download_images(image_urls, save_directory)



jpg_list = ['https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091pl.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-1.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-2.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-3.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-4.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-5.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-6.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-7.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-8.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-9.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-10.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-11.jpg', 'https://jp.netcdn.space/digital/video/ipzz00091/ipzz00091-12.jpg']

batch_download_images(jpg_list,"ipz-091")