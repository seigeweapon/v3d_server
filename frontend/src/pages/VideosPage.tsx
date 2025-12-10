import { Card, Table, Button, Modal, message, Tag, Popconfirm, Progress, Tooltip, Form, Input, Space, Descriptions, Checkbox } from 'antd'
import { PlusOutlined, CopyOutlined, DeleteOutlined, EditOutlined, CloseOutlined, EyeOutlined, DownloadOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { fetchVideos, Video, uploadVideo, deleteVideo, markVideoReady, markVideoFailed, updateVideo, extractVideoMetadata, downloadVideoZip } from '../api/videos'
import { useRef, useState, useEffect } from 'react'
import { getVideoMetadata, calculateFrameCount, getVideoFormat } from '../utils/videoMetadata'

// localStorage key for last upload values
const LAST_UPLOAD_VALUES_KEY = 'video_upload_last_values'

// 格式化时间为本地时间：YYYY-MM-DD hh:mm:ss
// 后端返回的时间是UTC时间但没有时区标识，需要明确按UTC解析后再转换为本地时间
const formatLocalDateTime = (dateString: string): string => {
  if (!dateString) return '-'
  
  // 如果字符串没有时区信息（没有Z或+/-时区），则添加Z表示UTC时间
  let utcString = dateString
  if (!dateString.includes('Z') && !dateString.match(/[+-]\d{2}:\d{2}$/)) {
    // 直接在末尾添加Z表示UTC时间（保留微秒部分）
    utcString = dateString + 'Z'
  }
  
  const date = new Date(utcString)
  // 检查日期是否有效
  if (isNaN(date.getTime())) return '-'
  // 使用本地时间方法获取各个时间组件（这些方法会自动处理时区转换）
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const VideosPage = () => {
  const videoTableRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState<{
    visible: boolean
    current: number
    total: number
    currentFile: string
  } | null>(null)
  const [videoUploadModalVisible, setVideoUploadModalVisible] = useState(false)
  const [videoEditModalVisible, setVideoEditModalVisible] = useState(false)
  const [videoDetailModalVisible, setVideoDetailModalVisible] = useState(false)
  const [editingVideo, setEditingVideo] = useState<Video | null>(null)
  const [detailVideo, setDetailVideo] = useState<Video | null>(null)
  const [videoForm] = Form.useForm()
  const [videoEditForm] = Form.useForm()
  const videoFileInputRef = useRef<HTMLInputElement>(null)
  const backgroundFileInputRef = useRef<HTMLInputElement>(null)
  const calibrationFileInputRef = useRef<HTMLInputElement>(null)
  const [selectedVideoFiles, setSelectedVideoFiles] = useState<File[]>([])
  const [selectedBackgroundFiles, setSelectedBackgroundFiles] = useState<File[]>([])
  const [selectedCalibrationFile, setSelectedCalibrationFile] = useState<File | null>(null)
  const [downloadModalVisible, setDownloadModalVisible] = useState(false)
  const [downloadingVideo, setDownloadingVideo] = useState<Video | null>(null)
  const [selectedFileTypes, setSelectedFileTypes] = useState<string[]>(['video', 'background', 'calibration'])
  const [downloading, setDownloading] = useState(false)

  const { data: videos, isLoading: videosLoading } = useQuery<Video[]>(['videos'], fetchVideos, {
    staleTime: 5 * 60 * 1000,
    refetchOnMount: false,
  })

  const deleteVideoMutation = useMutation(
    async (videoId: number) => {
      await deleteVideo(videoId)
    },
    {
      onSuccess: () => {
        message.success('删除成功')
        queryClient.invalidateQueries(['videos'])
        queryClient.refetchQueries(['videos'])
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.detail || error?.message || '删除失败'
        message.error(`删除失败: ${errorMessage}`)
        console.error('删除视频失败:', error)
      }
    }
  )

  const updateVideoMutation = useMutation(
    async (payload: { id: number; studio: string; producer: string; production: string; action: string }) => {
      await updateVideo(payload.id, {
        studio: payload.studio,
        producer: payload.producer,
        production: payload.production,
        action: payload.action,
      })
    },
    {
      onSuccess: () => {
        message.success('修改成功')
        queryClient.invalidateQueries(['videos'])
        queryClient.refetchQueries(['videos'])
        setVideoEditModalVisible(false)
        setEditingVideo(null)
        videoEditForm.resetFields()
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.detail || error?.message || '修改失败'
        message.error(`修改失败: ${errorMessage}`)
        console.error('修改视频失败:', error)
      }
    }
  )


  const uploadVideoMutation = useMutation(
    async (payload: { studio: string; producer: string; production: string; action: string; files: { videos: File[]; backgrounds: File[]; calibration: File } }) => {
      const { studio, producer, production, action, files } = payload

      // 读取第一个视频文件的元数据（用于设置视频参数）
      let videoMetadata: {
        frame_count: number
        frame_rate: number
        frame_width: number
        frame_height: number
        video_format: string
      } | null = null

      if (files.videos.length > 0) {
        try {
          setUploadProgress({
            visible: true,
            current: 0,
            total: 100,
            currentFile: '正在读取视频元数据...'
          })

          const firstVideo = files.videos[0]
          let metadata: { duration: number; videoWidth: number; videoHeight: number; frameRate?: number }
          
          // 先尝试前端读取（快速，支持常见格式）
          try {
            metadata = await getVideoMetadata(firstVideo)
            console.log('前端读取元数据成功')
          } catch (frontendError: any) {
            console.warn('前端读取失败，尝试后端读取:', frontendError)
            // 前端读取失败（可能是HEVC等格式），尝试后端读取
            setUploadProgress(prev => prev ? {
              ...prev,
              currentFile: '正在通过后端读取视频元数据（支持HEVC）...'
            } : null)
            
            const backendMetadata = await extractVideoMetadata(firstVideo)
            // 转换为前端格式
            metadata = {
              duration: backendMetadata.duration,
              videoWidth: backendMetadata.width,
              videoHeight: backendMetadata.height,
              frameRate: backendMetadata.frame_rate,
            }
            console.log('后端读取元数据成功:', backendMetadata)
          }
          
          // 计算帧数（如果无法获取帧率，使用默认值30fps）
          const frameRate = metadata.frameRate || 30.0
          const frameCount = calculateFrameCount(metadata.duration, frameRate)
          
          videoMetadata = {
            frame_count: frameCount,
            frame_rate: frameRate,
            frame_width: metadata.videoWidth,
            frame_height: metadata.videoHeight,
            video_format: getVideoFormat(firstVideo.name),
          }
        } catch (error: any) {
          console.error('读取视频元数据失败:', error)
          const errorMessage = error?.message || '未知错误'
          message.warning(`无法读取视频元数据: ${errorMessage}，将使用默认值`)
          // 使用默认值
          videoMetadata = {
            frame_count: 0,
            frame_rate: 30.0,
            frame_width: 1920,
            frame_height: 1080,
            video_format: getVideoFormat(files.videos[0].name),
          }
        }
      }

      // 对视频文件按文件名排序
      const sortedVideoFiles = [...files.videos].sort((a, b) => a.name.localeCompare(b.name))
      
      // 对背景文件按文件名排序
      const sortedBackgroundFiles = [...files.backgrounds].sort((a, b) => a.name.localeCompare(b.name))

      // 重命名视频文件：cam_1.mp4, cam_2.mp4, ... (保留原扩展名)
      const renamedVideoFiles = sortedVideoFiles.map((file, index) => {
        const ext = file.name.split('.').pop()?.toLowerCase() || 'mp4'
        const newName = `cam_${index + 1}.${ext}`
        return new File([file], newName, { type: file.type })
      })

      // 重命名背景文件：cam_1.png, cam_2.jpg, ... (保留原扩展名)
      const renamedBackgroundFiles = sortedBackgroundFiles.map((file, index) => {
        const ext = file.name.split('.').pop()?.toLowerCase() || 'png'
        const newName = `cam_${index + 1}.${ext}`
        return new File([file], newName, { type: file.type })
      })

      // 标定文件：calibration_ba.json
      const calibrationNewName = 'calibration_ba.json'
      const renamedCalibrationFile = new File([files.calibration], calibrationNewName, { type: files.calibration.type })

      // 提取文件信息（使用新文件名）
      const fileInfos = [
        ...renamedVideoFiles.map(file => ({ name: file.name, type: file.type || 'video/mp4' })),
        ...renamedBackgroundFiles.map(file => ({ name: file.name, type: file.type || 'image/png' })),
        { name: calibrationNewName, type: files.calibration.type || 'application/json' }
      ]

      // 第一步：在后端创建视频记录（生成 tos_path 和 PostObject 表单数据）
      let created: Video | null = null
      try {
        created = await uploadVideo({
          studio,
          producer,
          production,
          action,
          camera_count: files.videos.length,  // 相机数 = 视频文件数量
          prime_camera_number: 1,  // 主相机编号，默认为1
          frame_count: videoMetadata?.frame_count,
          frame_rate: videoMetadata?.frame_rate,
          frame_width: videoMetadata?.frame_width,
          frame_height: videoMetadata?.frame_height,
          video_format: videoMetadata?.video_format,
          file_infos: fileInfos
        })

        // 使用重命名后的文件（按顺序：所有视频文件，所有背景文件，标定文件）
        const fileList = [...renamedVideoFiles, ...renamedBackgroundFiles, renamedCalibrationFile]

        if (!created.post_form_data_list || created.post_form_data_list.length !== fileInfos.length) {
          throw new Error(`后端返回的表单数据数量不正确：期望 ${fileInfos.length} 个，实际 ${created.post_form_data_list?.length || 0} 个`)
        }

        // 第二步：使用 PostObject 表单上传所有文件到 TOS
        // 更新进度显示（从元数据读取切换到文件上传）
        setUploadProgress({
          visible: true,
          current: 0,
          total: fileList.length,
          currentFile: '准备上传文件...'
        })
        for (let i = 0; i < fileList.length; i++) {
          const file = fileList[i]
          const postFormData = created.post_form_data_list[i]
          const { action: uploadAction, fields } = postFormData

          setUploadProgress(prev => prev ? {
            ...prev,
            currentFile: file.name
          } : null)

          const formData = new FormData()
          Object.entries(fields).forEach(([key, value]) => {
            formData.append(key, value as string)
          })
          formData.append('file', file)

          let uploadSuccess = false
          try {
            const response = await fetch(uploadAction, {
              method: 'POST',
              body: formData,
            })

            if (response.status >= 200 && response.status < 300) {
              uploadSuccess = true
            } else {
              const errorText = await response.text().catch(() => '无法读取错误信息')
              console.warn(`文件 ${file.name} 上传响应状态码 ${response.status}:`, errorText)
              uploadSuccess = true // 假设上传成功
            }
          } catch (error: any) {
            console.warn(`文件 ${file.name} 上传请求异常:`, error)
            uploadSuccess = true // 假设上传成功
          }

          if (!uploadSuccess) {
            throw new Error(`文件 ${file.name} 上传到 TOS 失败`)
          }

          setUploadProgress(prev => prev ? {
            ...prev,
            current: prev.current + 1
          } : null)
        }

        // 第三步：通知后端上传已完成，将状态标记为 ready
        await markVideoReady(created.id)

        return created
      } catch (error: any) {
        // 如果已经创建了视频记录，标记为失败状态
        if (created && created.id) {
          try {
            await markVideoFailed(created.id)
          } catch (e) {
            console.error('标记视频失败状态时出错:', e)
          }
        }
        throw error
      }
    },
    {
      onSuccess: (_, variables) => {
        setUploadProgress(null)
        message.success('视频上传成功')
        
        // 保存本次上传的值到 localStorage，供下次使用
        try {
          const valuesToSave = {
            studio: variables.studio,
            producer: variables.producer,
            production: variables.production,
            action: variables.action,
          }
          localStorage.setItem(LAST_UPLOAD_VALUES_KEY, JSON.stringify(valuesToSave))
        } catch (error) {
          console.error('保存上次上传值失败:', error)
        }
        
        queryClient.invalidateQueries(['videos'])
        queryClient.refetchQueries(['videos'])
        setVideoUploadModalVisible(false)
        videoForm.resetFields()
        setSelectedVideoFiles([])
        setSelectedBackgroundFiles([])
        setSelectedCalibrationFile(null)
      },
      onError: (error: any) => {
        setUploadProgress(null)
        const errorMessage = error?.response?.data?.detail || error?.message || '上传失败'
        message.error(`上传失败: ${errorMessage}`)
        console.error('视频上传失败:', error)
        // 刷新列表以显示失败状态
        queryClient.invalidateQueries(['videos'])
        queryClient.refetchQueries(['videos'])
      }
    }
  )


  // 当模态框打开时，自动填充上次上传的值
  useEffect(() => {
    if (videoUploadModalVisible) {
      try {
        const lastValues = localStorage.getItem(LAST_UPLOAD_VALUES_KEY)
        if (lastValues) {
          const parsed = JSON.parse(lastValues)
          videoForm.setFieldsValue({
            studio: parsed.studio || '',
            producer: parsed.producer || '',
            production: parsed.production || '',
            action: parsed.action || '',
          })
        }
      } catch (error) {
        console.error('读取上次上传值失败:', error)
      }
    }
  }, [videoUploadModalVisible, videoForm])

  const handleAddVideo = () => {
    setVideoUploadModalVisible(true)
  }

  const handleVideoUploadModalOk = async () => {
    try {
      const values = await videoForm.validateFields()
      if (selectedVideoFiles.length === 0 || selectedBackgroundFiles.length === 0 || !selectedCalibrationFile) {
        message.warning('请选择所有必需的文件')
        return
      }
      uploadVideoMutation.mutate({
        studio: values.studio,
        producer: values.producer,
        production: values.production,
        action: values.action,
        files: {
          videos: selectedVideoFiles,
          backgrounds: selectedBackgroundFiles,
          calibration: selectedCalibrationFile
        }
      })
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  const handleVideoUploadModalCancel = () => {
    setVideoUploadModalVisible(false)
    videoForm.resetFields()
    setSelectedVideoFiles([])
    setSelectedBackgroundFiles([])
    setSelectedCalibrationFile(null)
    // 清空所有input的value
    if (videoFileInputRef.current) videoFileInputRef.current.value = ''
    if (backgroundFileInputRef.current) backgroundFileInputRef.current.value = ''
    if (calibrationFileInputRef.current) calibrationFileInputRef.current.value = ''
  }

  const handleEditVideo = (video: Video) => {
    setEditingVideo(video)
    videoEditForm.setFieldsValue({
      studio: video.studio,
      producer: video.producer,
      production: video.production,
      action: video.action,
    })
    setVideoEditModalVisible(true)
  }

  const handleVideoEditModalOk = async () => {
    try {
      const values = await videoEditForm.validateFields()
      if (!editingVideo) return
      updateVideoMutation.mutate({
        id: editingVideo.id,
        studio: values.studio,
        producer: values.producer,
        production: values.production,
        action: values.action,
      })
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  const handleVideoEditModalCancel = () => {
    setVideoEditModalVisible(false)
    setEditingVideo(null)
    videoEditForm.resetFields()
  }

  const handleViewDetail = (video: Video) => {
    setDetailVideo(video)
    setVideoDetailModalVisible(true)
  }

  const handleDetailModalCancel = () => {
    setVideoDetailModalVisible(false)
    setDetailVideo(null)
  }

  const handleDownload = (video: Video) => {
    setDownloadingVideo(video)
    setSelectedFileTypes(['video', 'background', 'calibration']) // 重置为默认全选
    setDownloadModalVisible(true)
  }

  const handleDownloadModalOk = async () => {
    if (!downloadingVideo || selectedFileTypes.length === 0) {
      message.warning('请至少选择一种文件类型')
      return
    }

    setDownloading(true)
    try {
      // 后端打包 ZIP，单链接下载
      const { blob, filename } = await downloadVideoZip(downloadingVideo.id, selectedFileTypes)

      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename || 'v3d_data.zip'
      link.style.display = 'none'
      document.body.appendChild(link)
      link.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(link)

      message.success('开始下载 ZIP，文件将保存到浏览器的默认下载目录')

      setDownloadModalVisible(false)
      setDownloadingVideo(null)
    } catch (error: any) {
      const errorMessage = error?.response?.data?.detail || error?.message || '获取下载链接失败'
      message.error(`下载失败: ${errorMessage}`)
      console.error('下载失败:', error)
    } finally {
      setDownloading(false)
    }
  }

  const handleDownloadModalCancel = () => {
    setDownloadModalVisible(false)
    setDownloadingVideo(null)
    setSelectedFileTypes(['video', 'background', 'calibration'])
  }

  const handleVideoFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = event.target.files
    if (!fileList || fileList.length === 0) {
      return
    }

    const files = Array.from(fileList)
    const invalidFiles = files.filter(file => {
      const ext = file.name.split('.').pop()?.toLowerCase()
      return ext !== 'mp4' && ext !== 'ts'
    })

    if (invalidFiles.length > 0) {
      message.error('视频文件必须是 mp4 或 ts 格式')
      event.target.value = ''
      return
    }

    setSelectedVideoFiles(files)
  }

  const handleBackgroundFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = event.target.files
    if (!fileList || fileList.length === 0) {
      return
    }

    const files = Array.from(fileList)
    const invalidFiles = files.filter(file => {
      const ext = file.name.split('.').pop()?.toLowerCase()
      return ext !== 'png' && ext !== 'jpeg' && ext !== 'jpg'
    })

    if (invalidFiles.length > 0) {
      message.error('背景文件必须是 png、jpeg 或 jpg 格式')
      event.target.value = ''
      return
    }

    setSelectedBackgroundFiles(files)
  }

  const handleCalibrationFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const ext = file.name.split('.').pop()?.toLowerCase()
      if (ext !== 'json' && ext !== 'txt') {
        message.error('标定文件必须是 json 或 txt 格式')
        event.target.value = ''
        return
      }
      setSelectedCalibrationFile(file)
    }
  }

  // 复制 TOS 路径到剪贴板
  const handleCopyTosPath = async (tosPath: string) => {
    try {
      await navigator.clipboard.writeText(tosPath)
      message.success('已复制到剪贴板')
    } catch (err) {
      // 降级方案：使用传统方法
      const textArea = document.createElement('textarea')
      textArea.value = tosPath
      textArea.style.position = 'fixed'
      textArea.style.opacity = '0'
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
        message.success('已复制到剪贴板')
      } catch (e) {
        message.error('复制失败')
      }
      document.body.removeChild(textArea)
    }
  }

  const videoColumns = [
    { title: 'ID', dataIndex: 'id', width: 80 },
    { title: '摄影棚', dataIndex: 'studio' },
    { title: '制片方', dataIndex: 'producer' },
    { title: '制作', dataIndex: 'production' },
    { title: '动作', dataIndex: 'action' },
    { title: '相机数', dataIndex: 'camera_count', width: 100 },
    { title: '帧数', dataIndex: 'frame_count', width: 100 },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status: string) => {
        const color = status === 'ready' ? 'green' : status === 'failed' ? 'red' : 'blue'
        const text = status === 'ready' ? '上传成功' : status === 'failed' ? '上传失败' : '上传中'
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: 'TOS路径',
      dataIndex: 'tos_path',
      ellipsis: true,
      render: (tosPath: string) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Tooltip title={tosPath || '-'} placement="topLeft">
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {tosPath || '-'}
            </span>
          </Tooltip>
          {tosPath && (
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCopyTosPath(tosPath)}
              style={{ flexShrink: 0 }}
            />
          )}
        </div>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (created_at: string) => formatLocalDateTime(created_at),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: Video) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            size="small"
            onClick={() => handleViewDetail(record)}
          >
            详细
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEditVideo(record)}
          >
            修改
          </Button>
          <Button
            type="text"
            icon={<DownloadOutlined />}
            size="small"
            onClick={() => handleDownload(record)}
          >
            下载
          </Button>
          <Popconfirm
            title="确定要删除这条视频数据吗？"
            description="删除后将同时删除 TOS 上的所有相关文件（包括视频、背景、标定文件），此操作不可恢复。"
            onConfirm={() => deleteVideoMutation.mutate(record.id)}
            okText="确定"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              size="small"
              loading={deleteVideoMutation.isLoading}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]


  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Card 
        title="视频列表" 
        ref={videoTableRef}
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAddVideo}
          >
            添加
          </Button>
        }
      >
        <Table
          loading={videosLoading}
          dataSource={videos}
          columns={videoColumns}
          rowKey="id"
          scroll={{ x: 1500 }}
        />
      </Card>

      {/* 上传进度 Modal */}
      <Modal
        title="上传文件"
        open={uploadProgress?.visible || false}
        closable={false}
        footer={null}
        maskClosable={false}
      >
        <div style={{ marginBottom: 16 }}>
          <Progress
            percent={uploadProgress ? Math.round((uploadProgress.current / uploadProgress.total) * 100) : 0}
            status="active"
            format={(percent) => `${percent}%`}
          />
        </div>
        <div style={{ marginTop: 16 }}>
          <p style={{ margin: 0, color: '#666' }}>
            {uploadProgress?.currentFile ? `正在上传: ${uploadProgress.currentFile}` : '准备上传...'}
          </p>
          <p style={{ margin: '8px 0 0 0', color: '#999', fontSize: '12px' }}>
            {uploadProgress ? `${uploadProgress.current} / ${uploadProgress.total} 个文件` : ''}
          </p>
        </div>
      </Modal>

      {/* 视频上传 Modal */}
      <Modal
        title="上传视频"
        open={videoUploadModalVisible}
        onOk={handleVideoUploadModalOk}
        onCancel={handleVideoUploadModalCancel}
        okText="确定"
        cancelText="取消"
        confirmLoading={uploadVideoMutation.isLoading}
        width={600}
      >
        <Form form={videoForm} layout="vertical">
          <Form.Item label="摄影棚" name="studio" rules={[{ required: true, message: '请输入摄影棚' }]}>
            <Input placeholder="请输入摄影棚" />
          </Form.Item>
          <Form.Item label="制片方" name="producer" rules={[{ required: true, message: '请输入制片方' }]}>
            <Input placeholder="请输入制片方" />
          </Form.Item>
          <Form.Item label="制作" name="production" rules={[{ required: true, message: '请输入制作' }]}>
            <Input placeholder="请输入制作" />
          </Form.Item>
          <Form.Item label="动作" name="action" rules={[{ required: true, message: '请输入动作' }]}>
            <Input placeholder="请输入动作" />
          </Form.Item>
          <Form.Item label="视频文件" required>
            <div>
              {selectedVideoFiles.length > 0 ? (
                <div 
                  style={{ 
                    marginBottom: 8,
                    maxHeight: '120px',
                    overflowY: 'auto',
                    padding: '8px',
                    border: '1px solid #d9d9d9',
                    borderRadius: '4px',
                    backgroundColor: '#fafafa'
                  }}
                >
                  <div style={{ marginBottom: 4, fontSize: '12px', color: '#666' }}>
                    已选择 {selectedVideoFiles.length} 个文件：
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {selectedVideoFiles.map((file, index) => (
                      <Tag 
                        key={index} 
                        closable
                        onClose={(e) => {
                          e.preventDefault()
                          const newFiles = selectedVideoFiles.filter((_, i) => i !== index)
                          setSelectedVideoFiles(newFiles)
                        }}
                        style={{ margin: 0 }}
                      >
                        {file.name}
                      </Tag>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ marginBottom: 8, color: '#999', fontSize: '12px' }}>
                  未选择文件
                </div>
              )}
              <Space>
                <Button onClick={() => {
                  if (videoFileInputRef.current) {
                    videoFileInputRef.current.value = ''
                    videoFileInputRef.current.click()
                  }
                }}>
                  选择文件（可多选）
                </Button>
                {selectedVideoFiles.length > 0 && (
                  <Button 
                    size="small" 
                    onClick={() => {
                      setSelectedVideoFiles([])
                      if (videoFileInputRef.current) {
                        videoFileInputRef.current.value = ''
                      }
                    }}
                  >
                    清除
                  </Button>
                )}
              </Space>
            </div>
            <input
              ref={videoFileInputRef}
              type="file"
              accept=".mp4,.ts"
              multiple
              style={{ display: 'none' }}
              onChange={handleVideoFileChange}
            />
          </Form.Item>
          <Form.Item label="背景文件" required>
            <div>
              {selectedBackgroundFiles.length > 0 ? (
                <div 
                  style={{ 
                    marginBottom: 8,
                    maxHeight: '120px',
                    overflowY: 'auto',
                    padding: '8px',
                    border: '1px solid #d9d9d9',
                    borderRadius: '4px',
                    backgroundColor: '#fafafa'
                  }}
                >
                  <div style={{ marginBottom: 4, fontSize: '12px', color: '#666' }}>
                    已选择 {selectedBackgroundFiles.length} 个文件：
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {selectedBackgroundFiles.map((file, index) => (
                      <Tag 
                        key={index} 
                        closable
                        onClose={(e) => {
                          e.preventDefault()
                          const newFiles = selectedBackgroundFiles.filter((_, i) => i !== index)
                          setSelectedBackgroundFiles(newFiles)
                        }}
                        style={{ margin: 0 }}
                      >
                        {file.name}
                      </Tag>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{ marginBottom: 8, color: '#999', fontSize: '12px' }}>
                  未选择文件
                </div>
              )}
              <Space>
                <Button onClick={() => {
                  if (backgroundFileInputRef.current) {
                    backgroundFileInputRef.current.value = ''
                    backgroundFileInputRef.current.click()
                  }
                }}>
                  选择文件（可多选）
                </Button>
                {selectedBackgroundFiles.length > 0 && (
                  <Button 
                    size="small" 
                    onClick={() => {
                      setSelectedBackgroundFiles([])
                      if (backgroundFileInputRef.current) {
                        backgroundFileInputRef.current.value = ''
                      }
                    }}
                  >
                    清除
                  </Button>
                )}
              </Space>
            </div>
            <input
              ref={backgroundFileInputRef}
              type="file"
              accept=".png,.jpeg,.jpg"
              multiple
              style={{ display: 'none' }}
              onChange={handleBackgroundFileChange}
            />
          </Form.Item>
          <Form.Item label="标定文件" required>
            <Input
              value={selectedCalibrationFile?.name || ''}
              placeholder="请选择标定文件（json、txt）"
              readOnly
              suffix={
                <Button onClick={() => {
                  if (calibrationFileInputRef.current) {
                    calibrationFileInputRef.current.value = ''
                    calibrationFileInputRef.current.click()
                  }
                }}>选择</Button>
              }
            />
            <input
              ref={calibrationFileInputRef}
              type="file"
              accept=".json,.txt"
              style={{ display: 'none' }}
              onChange={handleCalibrationFileChange}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 视频编辑 Modal */}
      <Modal
        title="修改视频信息"
        open={videoEditModalVisible}
        onOk={handleVideoEditModalOk}
        onCancel={handleVideoEditModalCancel}
        okText="确定"
        cancelText="取消"
        confirmLoading={updateVideoMutation.isLoading}
        width={600}
      >
        <Form form={videoEditForm} layout="vertical">
          <Form.Item label="摄影棚" name="studio" rules={[{ required: true, message: '请输入摄影棚' }]}>
            <Input placeholder="请输入摄影棚" />
          </Form.Item>
          <Form.Item label="制片方" name="producer" rules={[{ required: true, message: '请输入制片方' }]}>
            <Input placeholder="请输入制片方" />
          </Form.Item>
          <Form.Item label="制作" name="production" rules={[{ required: true, message: '请输入制作' }]}>
            <Input placeholder="请输入制作" />
          </Form.Item>
          <Form.Item label="动作" name="action" rules={[{ required: true, message: '请输入动作' }]}>
            <Input placeholder="请输入动作" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 视频详情 Modal */}
      <Modal
        title="视频详细信息"
        open={videoDetailModalVisible}
        onCancel={handleDetailModalCancel}
        footer={[
          <Button key="close" onClick={handleDetailModalCancel}>
            关闭
          </Button>
        ]}
        width={700}
      >
        {detailVideo && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="ID">{detailVideo.id}</Descriptions.Item>
            <Descriptions.Item label="摄影棚">{detailVideo.studio}</Descriptions.Item>
            <Descriptions.Item label="制片方">{detailVideo.producer}</Descriptions.Item>
            <Descriptions.Item label="制作">{detailVideo.production}</Descriptions.Item>
            <Descriptions.Item label="动作">{detailVideo.action}</Descriptions.Item>
            <Descriptions.Item label="相机数">{detailVideo.camera_count}</Descriptions.Item>
            <Descriptions.Item label="主相机编号">{detailVideo.prime_camera_number}</Descriptions.Item>
            <Descriptions.Item label="帧数">{detailVideo.frame_count}</Descriptions.Item>
            <Descriptions.Item label="帧率">{detailVideo.frame_rate} fps</Descriptions.Item>
            <Descriptions.Item label="分辨率">
              {detailVideo.frame_width} × {detailVideo.frame_height}
            </Descriptions.Item>
            <Descriptions.Item label="视频格式">{detailVideo.video_format}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={detailVideo.status === 'ready' ? 'green' : detailVideo.status === 'failed' ? 'red' : 'blue'}>
                {detailVideo.status === 'ready' ? '上传成功' : detailVideo.status === 'failed' ? '上传失败' : '上传中'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="TOS路径">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Tooltip title={detailVideo.tos_path || '-'} placement="topLeft">
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {detailVideo.tos_path || '-'}
                  </span>
                </Tooltip>
                {detailVideo.tos_path && (
                  <Button
                    type="text"
                    size="small"
                    icon={<CopyOutlined />}
                    onClick={() => handleCopyTosPath(detailVideo.tos_path)}
                    style={{ flexShrink: 0 }}
                  />
                )}
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {formatLocalDateTime(detailVideo.created_at)}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 下载文件类型选择对话框 */}
      <Modal
        title="选择要下载的文件类型"
        open={downloadModalVisible}
        onOk={handleDownloadModalOk}
        onCancel={handleDownloadModalCancel}
        confirmLoading={downloading}
        okText="确认下载"
        cancelText="取消"
      >
        <Checkbox.Group
          value={selectedFileTypes}
          onChange={(values) => setSelectedFileTypes(values as string[])}
          style={{ width: '100%' }}
        >
          <Space direction="vertical">
            <Checkbox value="video">视频文件 (video)</Checkbox>
            <Checkbox value="background">背景文件 (background)</Checkbox>
            <Checkbox value="calibration">标定文件 (calibration)</Checkbox>
          </Space>
        </Checkbox.Group>
        <div style={{ marginTop: 16, color: '#666', fontSize: 12, lineHeight: '1.8' }}>
          <div><strong>提示：</strong></div>
          <div>1. 确认后会将选中文件类型下的<strong>所有文件打包成一个 ZIP</strong> 并下载</div>
          <div>2. ZIP 内部目录：v3d_data_YYYYMMDD_hhmmss/&lt;类型&gt;/文件名</div>
          <div>3. 文件会保存到浏览器的<strong>默认下载目录</strong>（无法自定义路径，这是浏览器的安全限制）</div>
          <div>4. 如下载被拦截，请在浏览器提示中选择“允许下载”或检查下载设置</div>
        </div>
      </Modal>
    </div>
  )
}

export default VideosPage
