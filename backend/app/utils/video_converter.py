import os
import logging
import subprocess

logger = logging.getLogger(__name__)

def get_gop_offsets(file_path) -> tuple[dict[int, int], int]:
    """
    使用ffmpeg库查找视频文件中所有I帧的偏移量

    参数:
        file_path: 视频文件路径

    返回:
        包含所有I帧偏移量的字典，键为帧序号，值为偏移量
    """
    if not os.path.exists(file_path):
        logger.error(f"错误：文件{file_path}不存在")

    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'frame=pict_type,pkt_pos',
        '-of', 'csv=p=0',
        file_path
    ]

    try:
        logger.info(f"执行ffprobe命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        frames = result.stdout.strip().split('\n')
        frames = [line for line in frames if line.strip() != '']
        nframe = len(frames)
        frames = [f"{i},{line}" for i, line in enumerate(frames)]
        iframes = {int(line.split(',')[0]): int(line.split(',')[1]) for line in frames if line.split(',')[2] == 'I'}
        logger.info(iframes)
        return iframes, nframe

    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe命令执行失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        return None, None

    except Exception as e:
        logger.error(f"发生错误: {e}")
        return None, None

def add_header(input_file: str, output_file: str, indices: dict[int, int], nframe: int):
    """构建索引并保存到新文件"""

    with open(output_file, 'wb') as f:
        # 写入魔数标识
        f.write(b'TSGOPIDX')

        # 写入header大小: 魔数、头大小、gop数、帧数、索引表（索引表项：4字节帧索引 + 8字节偏移量）
        header_size = 8 + 4 + 4 + 4 + len(indices) * (4 + 8)
        f.write(header_size.to_bytes(4, byteorder='little'))
        f.write(len(indices).to_bytes(4, byteorder='little'))
        f.write(nframe.to_bytes(4, byteorder='little'))
        for frame_index, offset in indices.items():
            f.write(frame_index.to_bytes(4, byteorder='little'))
            f.write((offset + header_size).to_bytes(8, byteorder='little'))

        # 写入原始TS文件内容
        with open(input_file, 'rb') as ts_file:
            f.write(ts_file.read())

    return output_file

def add_index_header_to_video_file(input_file: str, output_file: str):
    """添加索引头到视频文件"""
    indices, nframe = get_gop_offsets(input_file)
    add_header(input_file, output_file, indices, nframe)

def convert_to_indexed_ts_file(input_file: str, output_file: str):
    """转换视频文件为带索引头的TS流文件"""
    # 用ffmpeg将视频文件转为TS文件
    temp_file = '/tmp/converted.ts'
    cmd = [
        'ffmpeg',
        '-y',  # 自动覆盖输出文件，避免交互询问
        '-i', input_file,
        '-c', 'copy',
        '-f', 'mpegts',
        temp_file
    ]
    # 使用 capture_output=True 捕获输出，避免阻塞
    result = subprocess.run(cmd, capture_output=True, check=True)
    if result.returncode != 0:
        error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else '未知错误'
        logger.error(f"ffmpeg 转换失败: {error_msg}")
        raise RuntimeError(f'ffmpeg 转换失败: {error_msg}')
    # 添加索引头
    add_index_header_to_video_file(temp_file, output_file)