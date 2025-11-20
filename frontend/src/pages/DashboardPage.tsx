import { Card, Col, Row, Statistic } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { fetchVideos } from '../api/videos'
import { fetchJobs } from '../api/jobs'

const DashboardPage = () => {
  const { data: videos } = useQuery(['videos'], fetchVideos)
  const { data: jobs } = useQuery(['jobs'], fetchJobs)

  return (
    <Row gutter={16}>
      <Col span={8}>
        <Card>
          <Statistic title="视频数量" value={videos?.length ?? 0} />
        </Card>
      </Col>
      <Col span={8}>
        <Card>
          <Statistic title="任务数量" value={jobs?.length ?? 0} />
        </Card>
      </Col>
      <Col span={8}>
        <Card>
          <Statistic title="已完成任务" value={jobs?.filter((job) => job.status === 'completed').length ?? 0} />
        </Card>
      </Col>
    </Row>
  )
}

export default DashboardPage
