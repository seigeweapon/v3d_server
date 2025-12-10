"""
使用 ffprobe 读取视频元数据
"""
import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any


def get_video_metadata_with_ffprobe(file_path: str) -> Dict[str, Any]:
    """
    使用 ffprobe 读取视频元数据
    
    Returns:
        {
            'duration': float,  # 时长（秒）
            'width': int,       # 宽度
            'height': int,      # 高度
            'frame_rate': float, # 帧率
            'frame_count': int,  # 帧数（计算得出）
            'format': str,       # 格式（如 mp4, ts）
        }
    """
    try:
        # 使用 ffprobe 获取视频信息
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            '-select_streams', 'v:0',  # 只选择第一个视频流
            file_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )
        
        data = json.loads(result.stdout)
        
        # 从 format 中获取时长
        duration = float(data.get('format', {}).get('duration', 0))
        
        # 从 streams 中获取视频流信息
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise ValueError('未找到视频流')
        
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        
        # 获取帧率
        frame_rate_str = video_stream.get('r_frame_rate', '0/1')
        if '/' in frame_rate_str:
            num, den = map(int, frame_rate_str.split('/'))
            frame_rate = num / den if den > 0 else 0
        else:
            frame_rate = float(frame_rate_str) if frame_rate_str else 0
        
        # 如果无法获取帧率，尝试从其他字段获取
        if frame_rate <= 0:
            avg_frame_rate_str = video_stream.get('avg_frame_rate', '0/1')
            if '/' in avg_frame_rate_str:
                num, den = map(int, avg_frame_rate_str.split('/'))
                frame_rate = num / den if den > 0 else 0
        
        # 计算帧数
        frame_count = int(duration * frame_rate) if frame_rate > 0 and duration > 0 else 0
        
        # 获取格式
        format_name = data.get('format', {}).get('format_name', '').split(',')[0] or 'mp4'
        
        return {
            'duration': duration,
            'width': width,
            'height': height,
            'frame_rate': frame_rate,
            'frame_count': frame_count,
            'format': format_name,
        }
    except subprocess.TimeoutExpired:
        raise RuntimeError('ffprobe 执行超时')
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'ffprobe 执行失败: {e.stderr}')
    except json.JSONDecodeError as e:
        raise RuntimeError(f'无法解析 ffprobe 输出: {e}')
    except Exception as e:
        raise RuntimeError(f'读取视频元数据失败: {str(e)}')


def get_video_metadata_from_file(file_data: bytes, filename: str) -> Dict[str, Any]:
    """
    从文件数据读取视频元数据
    
    Args:
        file_data: 文件二进制数据
        filename: 文件名（用于确定扩展名）
    
    Returns:
        视频元数据字典
    """
    # 创建临时文件
    suffix = Path(filename).suffix or '.mp4'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_file.write(file_data)
        tmp_path = tmp_file.name
    
    try:
        metadata = get_video_metadata_with_ffprobe(tmp_path)
        return metadata
    finally:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

