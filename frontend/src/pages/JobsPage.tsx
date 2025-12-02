import { useState } from 'react'
import { Button, Card, Form, Input, Select, Table, Tag, message } from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchVideos } from '../api/videos'
import { createJob, fetchJobs } from '../api/jobs'

const JobsPage = () => {
  const { data: videos } = useQuery(['videos'], fetchVideos)
  const { data: jobs } = useQuery(['jobs'], fetchJobs)
  const queryClient = useQueryClient()
  const [selectedVideo, setSelectedVideo] = useState<number | null>(null)

  const mutation = useMutation((params: { video_id: number; parameters?: string }) => createJob(params.video_id, params.parameters), {
    onSuccess: () => {
      message.success('任务已创建')
      queryClient.invalidateQueries(['jobs'])
    },
    onError: () => message.error('创建任务失败')
  })

  const columns = [
    { title: 'ID', dataIndex: 'id' },
    { title: '视频', dataIndex: 'video_id' },
    { title: '状态', dataIndex: 'status', render: (status: string) => <Tag color={status === 'completed' ? 'green' : 'blue'}>{status}</Tag> },
    { title: '参数', dataIndex: 'parameters' }
  ]

  const handleSubmit = ({ parameters }: { parameters?: string }) => {
    if (!selectedVideo) {
      message.warning('请选择视频')
      return
    }
    mutation.mutate({ video_id: selectedVideo, parameters })
  }

  return (
    <Card title="任务中心">
      <Form layout="inline" onFinish={handleSubmit} style={{ marginBottom: 24 }}>
        <Form.Item label="目标视频" required>
          <Select
            style={{ width: 240 }}
            placeholder="选择视频"
            options={videos?.map((video) => ({ 
              label: `ID: ${video.id} - ${video.studio}/${video.action}`, 
              value: video.id 
            }))}
            onChange={setSelectedVideo}
          />
        </Form.Item>
        <Form.Item label="参数" name="parameters">
          <Input placeholder="自定义 JSON 或文本" style={{ width: 240 }} />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={mutation.isLoading}>
          创建任务
        </Button>
      </Form>
      <Table dataSource={jobs} columns={columns} rowKey="id" />
    </Card>
  )
}

export default JobsPage
