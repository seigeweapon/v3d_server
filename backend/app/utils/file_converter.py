"""
文件格式转换工具
"""
import os
import tempfile
from pathlib import Path
from typing import BinaryIO, Tuple, Optional
import io

from app.utils.video_frame_extractor import extract_frame_from_video_data
from app.utils.video_converter import convert_to_indexed_ts_file


def convert_background_mp4_to_png(file_data: bytes, filename: str) -> Tuple[bytes, str]:
    """
    将 MP4 背景文件转换为 PNG 图片（提取首帧）。
    
    Args:
        file_data: MP4 文件的二进制数据
        filename: 原始文件名（例如 "cam_1.mp4"）
    
    Returns:
        (png_data, new_filename) 元组，其中 new_filename 是转换后的文件名（例如 "cam_1.png"）
    
    Raises:
        RuntimeError: 如果转换失败
    """
    png_data = extract_frame_from_video_data(file_data, filename, frame_time=0.0)
    
    # 生成新的文件名（将扩展名改为 .png）
    base_name = Path(filename).stem
    new_filename = f"{base_name}.png"
    
    return png_data, new_filename


def convert_video_mp4_to_ts(file_data: bytes, filename: str) -> Tuple[bytes, str]:
    """
    将 MP4 视频文件转换为带索引头的 TS 文件。
    使用 video_converter.py 中的 convert_to_indexed_ts_file 函数。
    
    Args:
        file_data: MP4 文件的二进制数据
        filename: 原始文件名（例如 "cam_1.mp4"）
    
    Returns:
        (ts_data, new_filename) 元组，其中 new_filename 是转换后的文件名（例如 "cam_1.ts"）
    
    Raises:
        RuntimeError: 如果转换失败
    """
    input_path = None
    output_path = None
    
    try:
        # 创建临时输入文件
        suffix = Path(filename).suffix or '.mp4'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as input_tmp_file:
            input_tmp_file.write(file_data)
            input_path = input_tmp_file.name
        
        # 创建临时输出文件路径
        base_name = Path(filename).stem
        output_path = os.path.join(os.path.dirname(input_path), f"{base_name}.ts")
        
        # 使用 video_converter 转换
        convert_to_indexed_ts_file(input_path, output_path)
        
        # 读取 TS 数据
        with open(output_path, 'rb') as f:
            ts_data = f.read()
        
        # 生成新的文件名
        new_filename = f"{base_name}.ts"
        
        return ts_data, new_filename
        
    except Exception as e:
        raise RuntimeError(f'转换视频文件失败: {str(e)}')
    finally:
        # 清理临时文件
        if input_path and os.path.exists(input_path):
            try:
                os.unlink(input_path)
            except Exception:
                pass
        if output_path and os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except Exception:
                pass

