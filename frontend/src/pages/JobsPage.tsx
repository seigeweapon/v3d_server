import { useState } from 'react'
import { Button, Card, Form, Input, Select, Table, Tag, message, Tooltip, Modal, Popconfirm, Switch, Space } from 'antd'
import { CopyOutlined, PlusOutlined, EditOutlined, SettingOutlined, StopOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchVideos, Video } from '../api/videos'
import { createJob, fetchJobs, deleteJob, updateJobNotes, Job, updateJobVisibility, JobVisibilityUpdate, terminateJob, syncJobStatus } from '../api/jobs'
import { getCurrentUser, fetchUsers, User } from '../api/users'

const JobsPage = () => {
  const { data: videos } = useQuery(['videos'], fetchVideos)
  const { data: jobs } = useQuery(['jobs'], fetchJobs)
  const { data: currentUser } = useQuery(['currentUser'], getCurrentUser, {
    staleTime: 5 * 60 * 1000,
    refetchOnMount: false,
  })

  const { data: allUsers } = useQuery<User[]>(['users'], fetchUsers, {
    enabled: !!currentUser?.is_superuser, // 只有管理员才需要获取用户列表
    staleTime: 5 * 60 * 1000,
    refetchOnMount: false,
  })
  const queryClient = useQueryClient()
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [editNotesModalVisible, setEditNotesModalVisible] = useState(false)
  const [visibilityModalVisible, setVisibilityModalVisible] = useState(false)
  const [editingJob, setEditingJob] = useState<Job | null>(null)
  const [editingVisibilityJob, setEditingVisibilityJob] = useState<Job | null>(null)
  const [jobForm] = Form.useForm()
  const [notesForm] = Form.useForm()
  const [visibilityForm] = Form.useForm()

  const mutation = useMutation((params: { video_id: number; parameters?: string; notes?: string }) => createJob(params.video_id, params.parameters, params.notes), {
    onSuccess: () => {
      message.success('任务已创建')
      queryClient.invalidateQueries(['jobs'])
      setCreateModalVisible(false)
      jobForm.resetFields()
    },
    onError: () => message.error('创建任务失败')
  })

  const deleteJobMutation = useMutation(
    async (jobId: number) => {
      await deleteJob(jobId)
    },
    {
      onSuccess: () => {
        message.success('删除成功')
        queryClient.invalidateQueries(['jobs'])
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.detail || error?.message || '删除失败'
        message.error(`删除失败: ${errorMessage}`)
        console.error('删除任务失败:', error)
      }
    }
  )

  const updateNotesMutation = useMutation(
    async (params: { id: number; notes: string }) => {
      await updateJobNotes(params.id, params.notes)
    },
    {
      onSuccess: () => {
        message.success('备注更新成功')
        queryClient.invalidateQueries(['jobs'])
        setEditNotesModalVisible(false)
        setEditingJob(null)
        notesForm.resetFields()
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.detail || error?.message || '更新失败'
        message.error(`更新失败: ${errorMessage}`)
        console.error('更新备注失败:', error)
      }
    }
  )

  const updateJobVisibilityMutation = useMutation(
    async (payload: { id: number; visibility: JobVisibilityUpdate }) => {
      await updateJobVisibility(payload.id, payload.visibility)
    },
    {
      onSuccess: () => {
        message.success('可见性设置更新成功')
        queryClient.invalidateQueries(['jobs'])
        setVisibilityModalVisible(false)
        setEditingVisibilityJob(null)
        visibilityForm.resetFields()
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.detail || error?.message || '更新失败'
        message.error(`更新失败: ${errorMessage}`)
        console.error('更新可见性失败:', error)
      }
    }
  )

  const terminateJobMutation = useMutation(
    async (jobId: number) => {
      await terminateJob(jobId)
    },
    {
      onSuccess: () => {
        message.success('已请求终止任务')
        queryClient.invalidateQueries(['jobs'])
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.detail || error?.message || '终止失败'
        message.error(`终止失败: ${errorMessage}`)
        console.error('终止任务失败:', error)
      }
    }
  )

  const syncJobStatusMutation = useMutation(
    async (jobId: number) => {
      await syncJobStatus(jobId)
    },
    {
      onSuccess: () => {
        message.success('状态已同步')
        queryClient.invalidateQueries(['jobs'])
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.detail || error?.message || '同步失败'
        message.error(`同步失败: ${errorMessage}`)
        console.error('同步任务状态失败:', error)
      }
    }
  )

  const getVideoInfo = (videoId: number): Video | undefined => {
    return videos?.find(v => v.id === videoId)
  }

  const formatVideoInfo = (videoId: number): string => {
    const video = getVideoInfo(videoId)
    if (!video) {
      return `${videoId}: -`
    }
    return `${videoId}: ${video.studio}/${video.producer}/${video.production}/${video.action}`
  }

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

  const handleTerminate = (job: Job) => {
    terminateJobMutation.mutate(job.id)
  }

  const handleSyncStatus = (job: Job) => {
    syncJobStatusMutation.mutate(job.id)
  }

  const handleDelete = (job: Job) => {
    deleteJobMutation.mutate(job.id)
  }

  const handleEditNotes = (job: Job) => {
    setEditingJob(job)
    notesForm.setFieldsValue({ notes: job.notes || '' })
    setEditNotesModalVisible(true)
  }

  const handleNotesModalOk = () => {
    if (!editingJob) return
    notesForm.validateFields().then((values) => {
      updateNotesMutation.mutate({ 
        id: editingJob.id, 
        notes: values.notes || '' 
      })
    }).catch(() => {
      // 验证失败，不执行任何操作
    })
  }

  const handleNotesModalCancel = () => {
    setEditNotesModalVisible(false)
    setEditingJob(null)
    notesForm.resetFields()
  }

  const handleEditVisibility = (job: Job) => {
    setEditingVisibilityJob(job)
    let visibleUserIds: number[] = []
    try {
      visibleUserIds = job.visible_to_user_ids ? JSON.parse(job.visible_to_user_ids) : []
    } catch (e) {
      console.error('解析 visible_to_user_ids 失败:', e, job.visible_to_user_ids)
    }
    visibilityForm.setFieldsValue({
      is_public: job.is_public,
      visible_to_user_ids: visibleUserIds,
    })
    setVisibilityModalVisible(true)
  }

  const handleVisibilityModalOk = async () => {
    if (!editingVisibilityJob) return
    try {
      const values = await visibilityForm.validateFields()
      const update: JobVisibilityUpdate = {}
      if (values.is_public !== editingVisibilityJob.is_public) {
        update.is_public = values.is_public
      }
      // 只有管理员可以修改 visible_to_user_ids
      if (currentUser?.is_superuser) {
        update.visible_to_user_ids = values.visible_to_user_ids || []
      }
      if (Object.keys(update).length > 0) {
        updateJobVisibilityMutation.mutate({ id: editingVisibilityJob.id, visibility: update })
      } else {
        setVisibilityModalVisible(false)
      }
    } catch (error) {
      console.error('表单验证失败:', error)
    }
  }

  const handleVisibilityModalCancel = () => {
    setVisibilityModalVisible(false)
    setEditingVisibilityJob(null)
    visibilityForm.resetFields()
  }

  const handleCopy = async (text: string) => {
    if (!text) return
    try {
      await navigator.clipboard.writeText(text)
      message.success('已复制到剪贴板')
    } catch (err) {
      // 降级方案：使用传统方法
      const textArea = document.createElement('textarea')
      textArea.value = text
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

  const columns = [
    { 
      title: 'ID', 
      dataIndex: 'id',
      width: 80
    },
    { 
      title: '创建人', 
      dataIndex: 'owner_full_name',
      width: 120,
      ellipsis: true,
      render: (text: string) => text || '-'
    },
    { 
      title: '视频信息', 
      key: 'video_info',
      render: (_: any, record: Job) => formatVideoInfo(record.video_id),
      ellipsis: true
    },
    { 
      title: '备注', 
      dataIndex: 'notes',
      ellipsis: true,
      render: (text: string, record: Job) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Tooltip title={text || '-'} placement="topLeft">
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {text || '-'}
            </span>
          </Tooltip>
          <Button
            type="text"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditNotes(record)}
            style={{ flexShrink: 0 }}
          />
        </div>
      )
    },
    {
      title: '可见性',
      key: 'visibility',
      width: 120,
      render: (_: any, record: Job) => {
        const isPublic = record.is_public ?? false
        let visibleUserIds: number[] = []
        try {
          visibleUserIds = record.visible_to_user_ids ? JSON.parse(record.visible_to_user_ids) : []
        } catch (e) {
          console.error('解析 visible_to_user_ids 失败:', e, record.visible_to_user_ids)
        }
        const hasCustomVisibility = visibleUserIds.length > 0
        
        if (isPublic) {
          return <Tag color="green">公开</Tag>
        } else if (hasCustomVisibility) {
          return <Tag color="orange">授权用户</Tag>
        } else {
          return <Tag color="default">私有</Tag>
        }
      },
    },
    { 
      title: '状态', 
      dataIndex: 'status', 
      width: 100,
      render: (status: string) => {
        const normalized = status?.toLowerCase?.() || ''
        const colorMap: Record<string, string> = {
          'completed': 'green',
          'pending': 'blue',
          'processing': 'orange',
          'running': 'orange',
          'submitted': 'blue',
          'terminated': 'gray',
          'failed': 'red'
        }
        return <Tag color={colorMap[normalized] || 'default'}>{status || '-'}</Tag>
      }
    },
    {
      title: 'Run ID',
      dataIndex: 'run_id',
      ellipsis: true,
      render: (text: string | null | undefined) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Tooltip title={text || '-'} placement="topLeft">
            {text ? (
              <a 
                href={`https://cloud.bytedance.net/mipp/execution_details?runId=${text}`} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#1890ff' }}
              >
                {text}
              </a>
            ) : (
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                -
              </span>
            )}
          </Tooltip>
          {text && (
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCopy(text)}
              style={{ flexShrink: 0 }}
            />
          )}
        </div>
      )
    },
    { 
      title: '参数', 
      dataIndex: 'parameters',
      ellipsis: true,
      render: (text: string) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Tooltip title={text || '-'} placement="topLeft">
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {text || '-'}
            </span>
          </Tooltip>
          {text && (
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCopy(text)}
              style={{ flexShrink: 0 }}
            />
          )}
        </div>
      )
    },
    { 
      title: 'TOS路径', 
      dataIndex: 'tos_path',
      ellipsis: true,
      render: (text: string) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Tooltip title={text || '-'} placement="topLeft">
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {text || '-'}
            </span>
          </Tooltip>
          {text && (
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleCopy(text)}
              style={{ flexShrink: 0 }}
            />
          )}
        </div>
      )
    },
    { 
      title: '创建时间', 
      dataIndex: 'created_at',
      width: 180,
      render: (text: string) => formatLocalDateTime(text)
    },
    { 
      title: '操作', 
      key: 'action',
      width: 280,
      fixed: 'right' as const,
      render: (_: any, record: Job) => (
        <Space>
          {(currentUser?.id === record.owner_id || currentUser?.is_superuser) && (
            <Button
              type="text"
              size="small"
              icon={<SettingOutlined />}
              onClick={() => handleEditVisibility(record)}
            >
              可见性
            </Button>
          )}
          <Button 
            type="text" 
            danger 
            size="small" 
            icon={<StopOutlined />}
            onClick={() => handleTerminate(record)}
            loading={terminateJobMutation.isLoading}
          >
            终止
          </Button>
          <Button
            type="text"
            size="small"
            icon={<ReloadOutlined />}
            onClick={() => handleSyncStatus(record)}
            loading={syncJobStatusMutation.isLoading}
          >
            同步
          </Button>
          {currentUser?.is_superuser && (
            <Popconfirm
              title="确定要删除这个任务吗？"
              description="删除后将同时删除TOS上的相关文件，此操作不可恢复。"
              onConfirm={() => handleDelete(record)}
              okText="确定"
              cancelText="取消"
              okButtonProps={{ danger: true }}
            >
              <Button 
                type="text" 
                danger 
                size="small" 
                icon={<DeleteOutlined />}
                loading={deleteJobMutation.isLoading}
              >
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ]

  const handleCreateJob = () => {
    setCreateModalVisible(true)
  }

  const handleModalOk = () => {
    jobForm.validateFields().then((values) => {
      mutation.mutate({ 
        video_id: values.video_id, 
        parameters: values.parameters,
        notes: values.notes
      })
    }).catch(() => {
      // 验证失败，不执行任何操作
    })
  }

  const handleModalCancel = () => {
    setCreateModalVisible(false)
    jobForm.resetFields()
  }

  return (
    <>
      <Card 
        title="任务中心"
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleCreateJob}
          >
            创建任务
          </Button>
        }
      >
        <Table 
          dataSource={jobs} 
          columns={columns} 
          rowKey="id" 
          scroll={{ x: 'max-content' }}
        />
      </Card>

      {/* 创建任务 Modal */}
      <Modal
        title="创建任务"
        open={createModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        okText="确定"
        cancelText="取消"
        confirmLoading={mutation.isLoading}
        width={600}
      >
        <Form form={jobForm} layout="vertical">
          <Form.Item 
            label="目标视频" 
            name="video_id" 
            rules={[{ required: true, message: '请选择视频' }]}
          >
            <Select
              placeholder="选择视频"
              options={videos?.map((video) => ({ 
                label: `ID: ${video.id} - ${video.studio}/${video.producer}/${video.production}/${video.action}`, 
                value: video.id 
              }))}
            />
          </Form.Item>
          <Form.Item 
            label="参数" 
            name="parameters"
          >
            <Input.TextArea 
              placeholder="自定义 JSON 或文本" 
              rows={4}
            />
          </Form.Item>
          <Form.Item 
            label="备注" 
            name="notes"
          >
            <Input.TextArea 
              placeholder="请输入备注信息" 
              rows={3}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑备注 Modal */}
      <Modal
        title="编辑备注"
        open={editNotesModalVisible}
        onOk={handleNotesModalOk}
        onCancel={handleNotesModalCancel}
        okText="确定"
        cancelText="取消"
        confirmLoading={updateNotesMutation.isLoading}
        width={500}
      >
        <Form form={notesForm} layout="vertical">
          <Form.Item 
            label="备注" 
            name="notes"
          >
            <Input.TextArea 
              placeholder="请输入备注信息" 
              rows={4}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 可见性管理 Modal */}
      <Modal
        title="管理可见性"
        open={visibilityModalVisible}
        onOk={handleVisibilityModalOk}
        onCancel={handleVisibilityModalCancel}
        okText="确定"
        cancelText="取消"
        confirmLoading={updateJobVisibilityMutation.isLoading}
        width={600}
      >
        <Form form={visibilityForm} layout="vertical">
          <Form.Item 
            label="公开" 
            name="is_public"
            tooltip="设置为公开后，所有用户都可以查看此任务"
          >
            <Switch checkedChildren="公开" unCheckedChildren="私有" />
          </Form.Item>
          {currentUser?.is_superuser && (
            <Form.Item 
              label="授权用户" 
              name="visible_to_user_ids"
              tooltip="管理员可以指定特定用户可见此任务（即使不是公开的）"
            >
              <Select
                mode="multiple"
                placeholder="选择可以查看此任务的用户"
                options={allUsers?.map(user => ({ 
                  label: `${user.full_name || user.email} (ID: ${user.id})`, 
                  value: user.id 
                }))}
                allowClear
              />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </>
  )
}

export default JobsPage
