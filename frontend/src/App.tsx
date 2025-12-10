import { Layout } from 'antd'
import { Route, Routes, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import UploadPage from './pages/UploadPage'
import JobsPage from './pages/JobsPage'
import VideosPage from './pages/VideosPage'
import UserPage from './pages/UserPage'
import { useQuery } from '@tanstack/react-query'
import { getCurrentUser } from './api/users'

const { Header, Content } = Layout

const PrivateRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return children
}

const AppHeader = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated } = useAuth()
  const { data: user } = useQuery(
    ['currentUser'],
    getCurrentUser,
    {
      enabled: isAuthenticated,
      staleTime: 5 * 60 * 1000,
      refetchOnMount: false,
    }
  )

  const isActive = (path: string) => location.pathname === path

  return (
    <Header style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      color: '#fff', 
      fontWeight: 600 
    }}>
      <span
        onClick={() => navigate('/')}
        style={{
          cursor: 'pointer',
          userSelect: 'none',
          transition: 'opacity 0.3s',
          fontSize: '20px',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.opacity = '0.8'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.opacity = '1'
        }}
      >
        空间视频制作
      </span>
      {isAuthenticated && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 30, position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
          <span
            onClick={() => navigate('/videos')}
            style={{
              cursor: 'pointer',
              userSelect: 'none',
              transition: 'all 0.3s',
              fontSize: '18px',
              fontWeight: 500,
              color: isActive('/videos') ? '#ffd700' : '#fff',
              borderBottom: isActive('/videos') ? '2px solid #ffd700' : '2px solid transparent',
              paddingBottom: '2px',
            }}
            onMouseEnter={(e) => {
              if (!isActive('/videos')) {
                e.currentTarget.style.opacity = '0.8'
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = '1'
            }}
          >
            视频列表
          </span>
          <span
            onClick={() => navigate('/jobs')}
            style={{
              cursor: 'pointer',
              userSelect: 'none',
              transition: 'all 0.3s',
              fontSize: '18px',
              fontWeight: 500,
              color: isActive('/jobs') ? '#ffd700' : '#fff',
              borderBottom: isActive('/jobs') ? '2px solid #ffd700' : '2px solid transparent',
              paddingBottom: '2px',
            }}
            onMouseEnter={(e) => {
              if (!isActive('/jobs')) {
                e.currentTarget.style.opacity = '0.8'
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = '1'
            }}
          >
            任务列表
          </span>
        </div>
      )}
      {isAuthenticated && user && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: '14px', fontWeight: 400 }}>当前用户：</span>
          <span
            onClick={() => navigate('/user')}
            style={{
              cursor: 'pointer',
              userSelect: 'none',
              transition: 'opacity 0.3s',
              fontSize: '14px',
              fontWeight: 'normal',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = '0.8'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = '1'
            }}
          >
            {user.full_name || user.email}
          </span>
        </div>
      )}
    </Header>
  )
}

const AppLayout = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <AppHeader />
      <Content style={{ padding: 24 }}>
        <Routes>
          <Route
            path="/"
            element={
              <PrivateRoute>
                <DashboardPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/videos"
            element={
              <PrivateRoute>
                <VideosPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <PrivateRoute>
                <UploadPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/jobs"
            element={
              <PrivateRoute>
                <JobsPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/user"
            element={
              <PrivateRoute>
                <UserPage />
              </PrivateRoute>
            }
          />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </Content>
    </Layout>
  )
}

const App = () => (
  <AuthProvider>
    <AppLayout />
  </AuthProvider>
)

export default App
