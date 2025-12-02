import { Layout } from 'antd'
import { Route, Routes, Navigate, useNavigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import UploadPage from './pages/UploadPage'
import JobsPage from './pages/JobsPage'
import VideosPage from './pages/VideosPage'

const { Header, Content } = Layout

const PrivateRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return children
}

const AppLayout = () => {
  const navigate = useNavigate()
  
  return (
  <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ color: '#fff', fontWeight: 600 }}>
        <span
          onClick={() => navigate('/')}
          style={{
            cursor: 'pointer',
            userSelect: 'none',
            transition: 'opacity 0.3s',
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
      </Header>
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
