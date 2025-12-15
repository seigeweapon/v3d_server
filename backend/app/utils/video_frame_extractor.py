"""
视频帧提取工具：从视频文件中提取帧并转换为 PNG
"""
import subprocess
import tempfile
import os
from pathlib import Path
from typing import BinaryIO, Optional
import io

def extract_frame_from_video_data(file_data: bytes, filename: str, frame_time: float = 0.0) -> bytes:
    """
    从视频文件数据中提取指定时间点的一帧并返回 PNG 图像的二进制数据。
    使用 ffmpeg 命令行工具，支持所有格式（包括 HEVC）。
    
    Args:
        file_data: 视频文件的二进制数据
        filename: 文件名（用于确定扩展名）
        frame_time: 提取的时间点（秒），默认为 0（第一帧）
    
    Returns:
        PNG 图像的二进制数据
    
    Raises:
        RuntimeError: 如果提取失败
    """
    suffix = Path(filename).suffix or '.mp4'
    input_path = None
    output_path = None
    
    try:
        # 创建临时输入文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as input_tmp_file:
            input_tmp_file.write(file_data)
            input_path = input_tmp_file.name
        
        # 创建临时输出文件路径
        output_path = input_path + ".png"
        
        # 使用 ffmpeg 提取帧
        cmd = [
            'ffmpeg',
            '-y',  # 覆盖输出文件
            '-ss', str(frame_time),  # 跳转到指定时间点
            '-i', input_path,  # 输入文件
            '-vframes', '1',  # 只提取一帧
            '-q:v', '2',  # 质量设置，2表示较高质量
            output_path  # 输出文件
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=60,  # 60秒超时
            check=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg 执行失败: {result.stderr.decode('utf-8', errors='ignore')}")
        
        # 读取 PNG 数据
        with open(output_path, 'rb') as f:
            png_data = f.read()
        
        return png_data
        
    except subprocess.TimeoutExpired:
        raise RuntimeError('ffmpeg 执行超时（60秒）')
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        raise RuntimeError(f'ffmpeg 执行失败: {error_msg}')
    except Exception as e:
        raise RuntimeError(f'提取视频帧失败: {str(e)}')
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

def extract_frame_from_file(file: BinaryIO, filename: str, frame_time: float = 0.0) -> bytes:
    """
    从文件对象中提取帧。
    
    Args:
        file: 文件对象（已打开）
        filename: 文件名
        frame_time: 提取的时间点（秒）
    
    Returns:
        PNG 图像的二进制数据
    """
    file_data = file.read()
    return extract_frame_from_video_data(file_data, filename, frame_time)

