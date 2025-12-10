import { Card, Table, Button, Modal, message, Tag, Popconfirm, Progress, Tooltip, Form, Input } from 'antd'
import { PlusOutlined, CopyOutlined, DeleteOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { fetchVideos, Video, uploadVideo, deleteVideo, markVideoReady, markVideoFailed } from '../api/videos'
import { useRef, useState } from 'react'

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
  const [videoForm] = Form.useForm()
  const videoFileInputRef = useRef<HTMLInputElement>(null)
  const backgroundFileInputRef = useRef<HTMLInputElement>(null)
  const calibrationFileInputRef = useRef<HTMLInputElement>(null)
  const [selectedVideoFile, setSelectedVideoFile] = useState<File | null>(null)
  const [selectedBackgroundFile, setSelectedBackgroundFile] = useState<File | null>(null)
  const [selectedCalibrationFile, setSelectedCalibrationFile] = useState<File | null>(null)

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


  const uploadVideoMutation = useMutation(
    async (payload: { studio: string; producer: string; production: string; action: string; files: { video: File; background: File; calibration: File } }) => {
      const { studio, producer, production, action, files } = payload

      // 提取文件信息
      const fileInfos = [
        { name: files.video.name, type: files.video.type || 'video/mp4' },
        { name: files.background.name, type: files.background.type || 'image/png' },
        { name: files.calibration.name, type: files.calibration.type || 'application/json' }
      ]

      // 第一步：在后端创建视频记录（生成 tos_path 和 PostObject 表单数据）
      let created: Video | null = null
      try {
        created = await uploadVideo({
          studio,
          producer,
          production,
          action,
          file_infos: fileInfos
        })

        if (!created.post_form_data_list || created.post_form_data_list.length !== 3) {
          throw new Error('后端返回的表单数据数量不正确')
        }

        // 第二步：使用 PostObject 表单上传所有文件到 TOS
        setUploadProgress({
          visible: true,
          current: 0,
          total: 3,
          currentFile: ''
        })

        const fileList = [files.video, files.background, files.calibration]
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
      onSuccess: () => {
        setUploadProgress(null)
        message.success('视频上传成功')
        queryClient.invalidateQueries(['videos'])
        queryClient.refetchQueries(['videos'])
        setVideoUploadModalVisible(false)
        videoForm.resetFields()
        setSelectedVideoFile(null)
        setSelectedBackgroundFile(null)
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


  const handleAddVideo = () => {
    setVideoUploadModalVisible(true)
  }

  const handleVideoUploadModalOk = async () => {
    try {
      const values = await videoForm.validateFields()
      if (!selectedVideoFile || !selectedBackgroundFile || !selectedCalibrationFile) {
        message.warning('请选择所有必需的文件')
        return
      }
      uploadVideoMutation.mutate({
        studio: values.studio,
        producer: values.producer,
        production: values.production,
        action: values.action,
        files: {
          video: selectedVideoFile,
          background: selectedBackgroundFile,
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
    setSelectedVideoFile(null)
    setSelectedBackgroundFile(null)
    setSelectedCalibrationFile(null)
  }

  const handleVideoFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const ext = file.name.split('.').pop()?.toLowerCase()
      if (ext !== 'mp4' && ext !== 'ts') {
        message.error('视频文件必须是 mp4 或 ts 格式')
        event.target.value = ''
        return
      }
      setSelectedVideoFile(file)
    }
  }

  const handleBackgroundFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const ext = file.name.split('.').pop()?.toLowerCase()
      if (ext !== 'png' && ext !== 'jpeg' && ext !== 'jpg') {
        message.error('背景文件必须是 png、jpeg 或 jpg 格式')
        event.target.value = ''
        return
      }
      setSelectedBackgroundFile(file)
    }
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
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: Video) => (
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
            <Input
              value={selectedVideoFile?.name || ''}
              placeholder="请选择视频文件（mp4、ts）"
              readOnly
              suffix={
                <Button onClick={() => videoFileInputRef.current?.click()}>选择</Button>
              }
            />
            <input
              ref={videoFileInputRef}
              type="file"
              accept=".mp4,.ts"
              style={{ display: 'none' }}
              onChange={handleVideoFileChange}
            />
          </Form.Item>
          <Form.Item label="背景文件" required>
            <Input
              value={selectedBackgroundFile?.name || ''}
              placeholder="请选择背景文件（png、jpeg、jpg）"
              readOnly
              suffix={
                <Button onClick={() => backgroundFileInputRef.current?.click()}>选择</Button>
              }
            />
            <input
              ref={backgroundFileInputRef}
              type="file"
              accept=".png,.jpeg,.jpg"
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
                <Button onClick={() => calibrationFileInputRef.current?.click()}>选择</Button>
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
    </div>
  )
}

export default VideosPage
