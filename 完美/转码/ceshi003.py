

import ffmpeg

# 转换视频格式
ffmpeg.input('PBD-336-A.-H265~裁剪~合集_002.mp4') \
    .output('output.mp4') \
    .run()

# # 截取视频的一部分
# ffmpeg.input('input.mp4') \
#     .trim(20, 10) \
#     .output('output.mp4') \
#     .run()