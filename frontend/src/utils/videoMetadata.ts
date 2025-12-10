/**
 * 读取视频文件的元数据
 * @param file 视频文件
 * @returns Promise<{ duration: number, videoWidth: number, videoHeight: number, frameRate?: number }>
 */
export function getVideoMetadata(file: File): Promise<{
  duration: number
  videoWidth: number
  videoHeight: number
  frameRate?: number
}> {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    const url = URL.createObjectURL(file)
    let timeoutId: ReturnType<typeof setTimeout> | null = null
    let resolved = false

    console.log(`开始读取视频元数据: ${file.name}, 大小: ${(file.size / 1024 / 1024).toFixed(2)}MB`)

    const cleanup = () => {
      if (timeoutId) {
        clearTimeout(timeoutId)
        timeoutId = null
      }
      URL.revokeObjectURL(url)
    }

    const handleSuccess = () => {
      if (resolved) return
      resolved = true
      cleanup()

      console.log('视频元数据加载成功:', {
        duration: video.duration,
        videoWidth: video.videoWidth,
        videoHeight: video.videoHeight,
        readyState: video.readyState,
      })

      // 检查元数据是否有效
      if (!video.duration || isNaN(video.duration) || video.duration <= 0) {
        console.error('视频时长无效:', video.duration)
        reject(new Error('无法获取视频时长，视频文件可能已损坏或格式不支持'))
        return
      }

      if (!video.videoWidth || !video.videoHeight || video.videoWidth <= 0 || video.videoHeight <= 0) {
        console.error('视频分辨率无效:', video.videoWidth, video.videoHeight)
        reject(new Error('无法获取视频分辨率，视频文件可能已损坏或格式不支持'))
        return
      }

      // 尝试获取帧率（不是所有浏览器都支持）
      let frameRate: number | undefined
      try {
        // @ts-ignore - 某些浏览器可能有这个属性
        if (video.getVideoPlaybackQuality) {
          const quality = video.getVideoPlaybackQuality()
          if (quality.totalVideoFrames && video.duration) {
            frameRate = quality.totalVideoFrames / video.duration
            console.log('获取到帧率:', frameRate)
          }
        }
      } catch (e) {
        // 忽略错误，帧率是可选的
        console.debug('无法获取帧率:', e)
      }

      resolve({
        duration: video.duration,
        videoWidth: video.videoWidth,
        videoHeight: video.videoHeight,
        frameRate: frameRate || undefined,
      })
    }

    const handleError = (error: any) => {
      if (resolved) return
      resolved = true
      cleanup()
      
      const errorMessage = error?.message || error?.toString() || '未知错误'
      const errorCode = video.error?.code
      const errorMessage_detail = video.error?.message
      let errorDetail = ''
      
      console.error('视频加载错误:', {
        errorCode,
        errorMessage: errorMessage_detail,
        readyState: video.readyState,
        networkState: video.networkState,
        file: file.name,
        fileSize: file.size,
        fileType: file.type,
      })
      
      if (errorCode !== undefined && errorCode !== null) {
        switch (errorCode) {
          case 1: // MEDIA_ERR_ABORTED
            errorDetail = '视频加载被中止'
            break
          case 2: // MEDIA_ERR_NETWORK
            errorDetail = '网络错误导致视频加载失败'
            break
          case 3: // MEDIA_ERR_DECODE
            errorDetail = '视频解码失败，文件可能已损坏或编码格式不支持（可能是H.265/HEVC等）'
            break
          case 4: // MEDIA_ERR_SRC_NOT_SUPPORTED
            errorDetail = '视频格式不支持（可能是编码格式问题，建议使用H.264编码的MP4）'
            break
          default:
            errorDetail = `错误代码: ${errorCode}`
        }
      }
      
      // 检查浏览器是否支持该文件类型
      const canPlay = video.canPlayType(file.type || 'video/mp4')
      console.log('浏览器支持检查:', {
        fileType: file.type,
        canPlay,
      })
      
      if (canPlay === '') {
        errorDetail += '（浏览器不支持该视频格式或编码）'
      }
      
      reject(new Error(`无法读取视频元数据: ${errorDetail || errorMessage}`))
    }

    // 监听更多事件以便调试
    video.addEventListener('loadstart', () => {
      console.log('视频开始加载')
    })
    
    video.addEventListener('progress', () => {
      console.log('视频加载进度:', video.buffered.length > 0 ? video.buffered.end(0) : 0)
    })
    
    video.addEventListener('loadeddata', () => {
      console.log('视频数据已加载')
    })

    video.preload = 'metadata'
    video.muted = true // 静音以避免自动播放策略问题
    video.playsInline = true // 支持内联播放
    video.crossOrigin = 'anonymous' // 尝试设置跨域属性
    
    video.onloadedmetadata = handleSuccess
    video.onerror = handleError

    // 设置超时（增加到60秒，因为50MB的文件可能需要更长时间）
    timeoutId = setTimeout(() => {
      if (!resolved) {
        resolved = true
        cleanup()
        console.error('视频元数据读取超时')
        reject(new Error('读取视频元数据超时（60秒），文件可能过大或格式不支持。请检查视频编码格式（建议使用H.264编码的MP4）'))
      }
    }, 60000) // 60秒超时

    // 开始加载
    video.src = url
    video.load() // 显式调用load()确保开始加载
    
    // 尝试播放一小段来触发元数据加载（某些视频的元数据在文件末尾）
    setTimeout(() => {
      if (!resolved && video.readyState >= 1) {
        // readyState >= 1 表示至少已加载元数据
        console.log('尝试通过播放触发元数据加载')
        video.play().catch((e) => {
          // 忽略播放错误，我们只需要元数据
          console.debug('播放失败（这是正常的，我们只需要元数据）:', e)
        })
      }
    }, 1000)
  })
}

/**
 * 从视频文件计算帧数
 * @param duration 视频时长（秒）
 * @param frameRate 帧率（fps）
 * @returns 帧数
 */
export function calculateFrameCount(duration: number, frameRate: number): number {
  return Math.round(duration * frameRate)
}

/**
 * 从文件扩展名获取视频格式
 * @param filename 文件名
 * @returns 视频格式（如 'mp4', 'ts'）
 */
export function getVideoFormat(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() || 'mp4'
  return ext
}

