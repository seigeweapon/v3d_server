import { Card, Typography, Form, Input, Button, message } from 'antd'
import { login } from '../api/auth'
import { useAuth } from '../hooks/useAuth'

const LoginPage = () => {
  const { login: setToken } = useAuth()

  const onFinish = async (values: { email: string; password: string }) => {
    try {
      const data = await login(values.email, values.password)
      setToken(data.access_token)
    } catch (error) {
      message.error('登录失败，请检查账号或密码')
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 120 }}>
      <Card title="登录" style={{ width: 360 }}>
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item label="邮箱" name="email" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item label="密码" name="password" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              登录
            </Button>
          </Form.Item>
        </Form>
        <Typography.Paragraph type="secondary">注册功能请使用后端接口</Typography.Paragraph>
      </Card>
    </div>
  )
}

export default LoginPage
