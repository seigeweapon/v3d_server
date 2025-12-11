import { useState, useEffect } from 'react'
import { Card, Table, Button, Modal, message, Tag, Popconfirm, Form, Input, Space, Checkbox, Tooltip } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchUsers, User, createUser, updateUser, deleteUser, UserCreate, UserUpdate, getCurrentUser } from '../api/users'

// 格式化时间为本地时间：YYYY-MM-DD hh:mm:ss
const formatLocalDateTime = (dateString: string): string => {
  if (!dateString) return '-'
  
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

const UsersManagementPage = () => {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [userForm] = Form.useForm()
  const [editForm] = Form.useForm()

  const { data: currentUser } = useQuery(['currentUser'], getCurrentUser, {
    staleTime: 5 * 60 * 1000,
    refetchOnMount: false,
  })

  // 如果不是管理员，重定向到首页
  useEffect(() => {
    if (currentUser && !currentUser.is_superuser) {
      message.error('您没有权限访问此页面')
      navigate('/')
    }
  }, [currentUser, navigate])

  const { data: users, isLoading: usersLoading } = useQuery<User[]>(['users'], fetchUsers, {
    enabled: !!currentUser?.is_superuser, // 只有管理员才能查询
    staleTime: 5 * 60 * 1000,
    refetchOnMount: false,
  })

  const createUserMutation = useMutation(
    async (userData: UserCreate) => {
      return await createUser(userData)
    },
    {
      onSuccess: () => {
        message.success('用户创建成功')
        queryClient.invalidateQueries(['users'])
        setCreateModalVisible(false)
        userForm.resetFields()
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.detail || error?.message || '创建用户失败'
        message.error(`创建用户失败: ${errorMessage}`)
        console.error('创建用户失败:', error)
      }
    }
  )

  const updateUserMutation = useMutation(
    async (payload: { id: number; data: UserUpdate }) => {
      return await updateUser(payload.id, payload.data)
    },
    {
      onSuccess: () => {
        message.success('用户更新成功')
        queryClient.invalidateQueries(['users'])
        setEditModalVisible(false)
        setEditingUser(null)
        editForm.resetFields()
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.detail || error?.message || '更新用户失败'
        message.error(`更新用户失败: ${errorMessage}`)
        console.error('更新用户失败:', error)
      }
    }
  )

  const deleteUserMutation = useMutation(
    async (userId: number) => {
      await deleteUser(userId)
    },
    {
      onSuccess: () => {
        message.success('用户删除成功')
        queryClient.invalidateQueries(['users'])
      },
      onError: (error: any) => {
        const errorMessage = error?.response?.data?.detail || error?.message || '删除用户失败'
        message.error(`删除用户失败: ${errorMessage}`)
        console.error('删除用户失败:', error)
      }
    }
  )

  const handleCreate = () => {
    setCreateModalVisible(true)
  }

  const handleCreateModalOk = () => {
    userForm.validateFields().then((values) => {
      createUserMutation.mutate({
        email: values.email,
        full_name: values.full_name,
        password: values.password,
        is_superuser: values.is_superuser || false,
      })
    }).catch(() => {})
  }

  const handleCreateModalCancel = () => {
    setCreateModalVisible(false)
    userForm.resetFields()
  }

  const handleEdit = (user: User) => {
    setEditingUser(user)
    setEditModalVisible(true)
    editForm.setFieldsValue({
      full_name: user.full_name,
      old_password: '', // 旧密码留空
      password: '', // 新密码留空，只有填写了才会更新
      is_superuser: user.is_superuser,
    })
  }

  const handleEditModalOk = () => {
    editForm.validateFields().then((values) => {
      if (editingUser) {
        const updateData: UserUpdate = {}
        if (values.full_name !== editingUser.full_name) {
          updateData.full_name = values.full_name
        }
        if (values.password && values.password.trim()) {
          if (!values.old_password || !values.old_password.trim()) {
            message.error('修改密码需要提供当前登录用户密码')
            return
          }
          updateData.old_password = values.old_password
          updateData.password = values.password
        }
        if (values.is_superuser !== editingUser.is_superuser) {
          updateData.is_superuser = values.is_superuser
        }
        updateUserMutation.mutate({ id: editingUser.id, data: updateData })
      }
    }).catch(() => {})
  }

  const handleEditModalCancel = () => {
    setEditModalVisible(false)
    setEditingUser(null)
    editForm.resetFields()
  }

  const handleDelete = (user: User) => {
    deleteUserMutation.mutate(user.id)
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      width: 200,
      ellipsis: true,
    },
    {
      title: '全名',
      dataIndex: 'full_name',
      width: 150,
      ellipsis: true,
      render: (text: string) => text || '-',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '活跃' : '已禁用'}
        </Tag>
      ),
    },
    {
      title: '权限',
      dataIndex: 'is_superuser',
      width: 100,
      render: (isSuperuser: boolean) => (
        <Tag color={isSuperuser ? 'purple' : 'blue'}>
          {isSuperuser ? '管理员' : '普通用户'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      render: (text: string) => formatLocalDateTime(text),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: User) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          {currentUser && record.id !== currentUser.id ? (
            <Popconfirm
              title="确定要删除这个用户吗？"
              description="删除后该用户将无法登录系统，此操作不可恢复。"
              onConfirm={() => handleDelete(record)}
              okText="确定"
              cancelText="取消"
              okButtonProps={{ danger: true }}
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                size="small"
                loading={deleteUserMutation.isLoading}
              >
                删除
              </Button>
            </Popconfirm>
          ) : (
            <Tooltip title="不能删除当前登录账户">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                size="small"
                disabled
              >
                删除
              </Button>
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <>
      <Card
        title="用户管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            创建用户
          </Button>
        }
      >
        <Table
          loading={usersLoading}
          dataSource={users}
          columns={columns}
          rowKey="id"
        />
      </Card>

      {/* 创建用户 Modal */}
      <Modal
        title="创建用户"
        open={createModalVisible}
        onOk={handleCreateModalOk}
        onCancel={handleCreateModalCancel}
        okText="确定"
        cancelText="取消"
        confirmLoading={createUserMutation.isLoading}
        width={500}
      >
        <Form form={userForm} layout="vertical">
          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' },
            ]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item
            label="全名"
            name="full_name"
          >
            <Input placeholder="请输入全名（可选）" />
          </Form.Item>
          <Form.Item
            label="密码"
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码长度至少6位' },
            ]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          <Form.Item
            name="is_superuser"
            valuePropName="checked"
            initialValue={false}
          >
            <Checkbox>创建为管理员用户</Checkbox>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑用户 Modal */}
      <Modal
        title="编辑用户"
        open={editModalVisible}
        onOk={handleEditModalOk}
        onCancel={handleEditModalCancel}
        okText="确定"
        cancelText="取消"
        confirmLoading={updateUserMutation.isLoading}
        width={500}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item label="邮箱">
            <Input value={editingUser?.email} disabled />
          </Form.Item>
          <Form.Item
            label="全名"
            name="full_name"
          >
            <Input placeholder="请输入全名" />
          </Form.Item>
          <Form.Item
            label="当前登录用户密码"
            name="old_password"
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  const newPassword = getFieldValue('password')
                  if (newPassword && newPassword.trim() && !value) {
                    return Promise.reject(new Error('修改密码需要提供当前登录用户密码'))
                  }
                  return Promise.resolve()
                },
              }),
            ]}
          >
            <Input.Password placeholder="留空则不修改密码" />
          </Form.Item>
          <Form.Item
            label="新密码"
            name="password"
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  const oldPassword = getFieldValue('old_password')
                  if (value && value.trim() && !oldPassword) {
                    return Promise.reject(new Error('修改密码需要提供当前登录用户密码'))
                  }
                  return Promise.resolve()
                },
              }),
            ]}
          >
            <Input.Password placeholder="留空则不修改密码" />
          </Form.Item>
          <Form.Item
            name="is_superuser"
            valuePropName="checked"
          >
            <Checkbox>管理员用户</Checkbox>
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}

export default UsersManagementPage

