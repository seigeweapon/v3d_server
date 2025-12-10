import { useState } from 'react'
import { Button, Card, Form, Input, InputNumber, message } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createVideo } from '../api/videos'

const UploadPage = () => {
  const queryClient = useQueryClient()

  const mutation = useMutation(createVideo, {
    onSuccess: () => {
      message.success('视频创建成功')
      queryClient.invalidateQueries(['videos'])
    },
    onError: () => message.error('创建失败')
  })

  const handleSubmit = (values: any) => {
    mutation.mutate(values)
  }

  return (
    <Card title="创建视频" style={{ maxWidth: 800 }}>
      <Form layout="vertical" onFinish={handleSubmit}>
        <Form.Item label="摄影棚" name="studio" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="制片方" name="producer" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="制作" name="production" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="动作" name="action" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="相机数" name="camera_count" rules={[{ required: true }]}>
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item label="主相机编号" name="prime_camera_number" rules={[{ required: true }]}>
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item label="帧数" name="frame_count" rules={[{ required: true }]}>
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item label="帧率" name="frame_rate" rules={[{ required: true }]}>
          <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item label="宽度" name="frame_width" rules={[{ required: true }]}>
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item label="高度" name="frame_height" rules={[{ required: true }]}>
          <InputNumber min={1} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item label="视频格式" name="video_format" rules={[{ required: true }]}>
          <Input placeholder="例如: mp4, avi, mov" />
        </Form.Item>
        <Form.Item label="TOS路径" name="tos_path" rules={[{ required: true }]}>
          <Input placeholder="例如: tos://bucket/path/to/video" />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={mutation.isLoading}>
          创建视频
        </Button>
      </Form>
    </Card>
  )
}

export default UploadPage
