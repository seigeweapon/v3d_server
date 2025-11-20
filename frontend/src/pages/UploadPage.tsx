import { useState } from 'react'
import { Button, Card, Form, Input, Upload, message } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadVideo } from '../api/videos'

const UploadPage = () => {
  const [file, setFile] = useState<File | null>(null)
  const queryClient = useQueryClient()

  const mutation = useMutation(({ videoFile, description }: { videoFile: File; description?: string }) => uploadVideo(videoFile, description), {
    onSuccess: () => {
      message.success('上传成功')
      setFile(null)
      queryClient.invalidateQueries(['videos'])
    },
    onError: () => message.error('上传失败')
  })

  const handleSubmit = ({ description }: { description?: string }) => {
    if (!file) {
      message.warning('请先选择文件')
      return
    }
    mutation.mutate({ videoFile: file, description })
  }

  return (
    <Card title="上传视频" style={{ maxWidth: 600 }}>
      <Form layout="vertical" onFinish={handleSubmit}>
        <Form.Item label="视频文件" required>
          <Upload
            beforeUpload={(uploadFile) => {
              setFile(uploadFile)
              return false
            }}
            maxCount={1}
            fileList={file ? [{ uid: '1', name: file.name, status: 'done' }] : []}
            onRemove={() => setFile(null)}
          >
            <Button icon={<UploadOutlined />}>选择文件</Button>
          </Upload>
        </Form.Item>
        <Form.Item label="描述" name="description">
          <Input.TextArea rows={3} />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={mutation.isLoading}>
          上传
        </Button>
      </Form>
    </Card>
  )
}

export default UploadPage
