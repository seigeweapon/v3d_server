import { Layout } from 'antd'
import { Route, Routes, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import UploadPage from './pages/UploadPage'
import JobsPage from './pages/JobsPage'

const { Header, Content } = Layout

const PrivateRoute = ({ children }: { children: JSX.Element }) => {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  return children
}

const AppLayout = () => (
  <Layout style={{ minHeight: '100vh' }}>
    <Header style={{ color: '#fff', fontWeight: 600 }}>Video Processing Portal</Header>
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

const App = () => (
  <AuthProvider>
    <AppLayout />
  </AuthProvider>
)

export default App
