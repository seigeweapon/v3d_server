# FFmpeg 安装说明

为了支持 HEVC (H.265) 编码的视频文件元数据读取，后端需要使用 `ffprobe`（FFmpeg 的一部分）。

## 安装方法

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y ffmpeg
```

### CentOS/RHEL
```bash
sudo yum install -y ffmpeg
# 或者对于较新版本
sudo dnf install -y ffmpeg
```

### macOS
```bash
brew install ffmpeg
```

### 验证安装
```bash
ffprobe -version
```

安装成功后，后端将能够读取 HEVC 编码的视频文件元数据。

