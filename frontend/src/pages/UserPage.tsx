import { Card, Descriptions, Tag, Space } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { getCurrentUser, User } from '../api/users'

// 格式化时间为本地时间：YYYY-MM-DD hh:mm:ss
const formatLocalDateTime = (dateString: string): string => {
  if (!dateString) return '-'
  
  // 如果字符串没有时区信息（没有Z或+/-时区），则添加Z表示UTC时间
  let utcString = dateString
  if (!dateString.includes('Z') && !dateString.match(/[+-]\d{2}:\d{2}$/)) {
    utcString = dateString + 'Z'
  }
  
  const date = new Date(utcString)
  if (isNaN(date.getTime())) return '-'
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const UserPage = () => {
  const { data: user, isLoading } = useQuery<User>(['currentUser'], getCurrentUser, {
    staleTime: 5 * 60 * 1000,
    refetchOnMount: false,
  })

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <Card
        title="用户信息"
        loading={isLoading}
      >
        {user && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="用户ID">
              {user.id}
            </Descriptions.Item>
            <Descriptions.Item label="邮箱">
              {user.email}
            </Descriptions.Item>
            <Descriptions.Item label="全名">
              {user.full_name || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={user.is_active ? 'green' : 'red'}>
                {user.is_active ? '活跃' : '已禁用'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="权限等级">
              <Space>
                <Tag color={user.is_superuser ? 'purple' : 'blue'}>
                  {user.is_superuser ? '超级管理员' : '普通用户'}
                </Tag>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {formatLocalDateTime(user.created_at)}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Card>
    </div>
  )
}

export default UserPage

