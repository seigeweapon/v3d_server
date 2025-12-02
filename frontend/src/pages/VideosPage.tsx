import { Card, Table, Row, Col } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { fetchVideos, Video } from '../api/videos'
import { fetchBackgrounds, Background } from '../api/backgrounds'
import { fetchCalibrations, Calibration } from '../api/calibrations'
import { useRef, useEffect, useState } from 'react'

const VideosPage = () => {
  const videoTableRef = useRef<HTMLDivElement>(null)
  const [tableHeight, setTableHeight] = useState<number>(400)

  const { data: videos, isLoading: videosLoading } = useQuery<Video[]>(['videos'], fetchVideos, {
    staleTime: 5 * 60 * 1000,
    refetchOnMount: false,
  })

  const { data: backgrounds, isLoading: backgroundsLoading } = useQuery<Background[]>(
    ['backgrounds'],
    fetchBackgrounds,
    {
      staleTime: 5 * 60 * 1000,
      refetchOnMount: false,
    }
  )

  const { data: calibrations, isLoading: calibrationsLoading } = useQuery<Calibration[]>(
    ['calibrations'],
    fetchCalibrations,
    {
      staleTime: 5 * 60 * 1000,
      refetchOnMount: false,
    }
  )

  useEffect(() => {
    const updateTableHeight = () => {
      if (videoTableRef.current) {
        // 获取视频表格的实际高度（包括表头）
        const videoTableElement = videoTableRef.current.querySelector('.ant-table-body')
        if (videoTableElement) {
          const videoTableHeight = videoTableElement.clientHeight || videoTableRef.current.offsetHeight
          setTableHeight(Math.floor(videoTableHeight * 0.75))
        } else {
          // 如果表格还没渲染，使用容器的默认高度
          const defaultHeight = videoTableRef.current.offsetHeight || 400
          setTableHeight(Math.floor(defaultHeight * 0.75))
        }
      }
    }

    // 延迟执行以确保表格已渲染
    const timer = setTimeout(updateTableHeight, 100)
    window.addEventListener('resize', updateTableHeight)
    return () => {
      clearTimeout(timer)
      window.removeEventListener('resize', updateTableHeight)
    }
  }, [videos, videosLoading])

  const videoColumns = [
    { title: 'ID', dataIndex: 'id', width: 80 },
    { title: '工作室', dataIndex: 'studio' },
    { title: '制片人', dataIndex: 'producer' },
    { title: '制作', dataIndex: 'production' },
    { title: '动作', dataIndex: 'action' },
    { title: '相机数', dataIndex: 'camera_count', width: 100 },
    { title: '主相机编号', dataIndex: 'prime_camera_number', width: 120 },
    { title: '背景ID', dataIndex: 'background_id', width: 100 },
    { title: '标定ID', dataIndex: 'calibration_id', width: 100 },
    { title: '帧数', dataIndex: 'frame_count', width: 100 },
    { title: '帧率', dataIndex: 'frame_rate', width: 100 },
    { title: '宽度', dataIndex: 'frame_width', width: 100 },
    { title: '高度', dataIndex: 'frame_height', width: 100 },
    { title: '视频格式', dataIndex: 'video_format', width: 120 },
    { title: 'TOS路径', dataIndex: 'tos_path', ellipsis: true },
    { title: '创建时间', dataIndex: 'created_at', width: 180 },
  ]

  const backgroundColumns = [
    { title: 'ID', dataIndex: 'id', width: 80 },
    { title: '相机数', dataIndex: 'camera_count', width: 100 },
    { title: 'TOS路径', dataIndex: 'tos_path', ellipsis: true },
    { title: '备注', dataIndex: 'notes', ellipsis: true },
    { title: '创建时间', dataIndex: 'created_at', width: 180 },
  ]

  const calibrationColumns = [
    { title: 'ID', dataIndex: 'id', width: 80 },
    { title: '相机数', dataIndex: 'camera_count', width: 100 },
    { title: 'TOS路径', dataIndex: 'tos_path', ellipsis: true },
    { title: '备注', dataIndex: 'notes', ellipsis: true },
    { title: '创建时间', dataIndex: 'created_at', width: 180 },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Card title="视频列表" ref={videoTableRef}>
        <Table
          loading={videosLoading}
          dataSource={videos}
          columns={videoColumns}
          rowKey="id"
          scroll={{ x: 1500 }}
        />
      </Card>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="背景列表">
            <Table
              loading={backgroundsLoading}
              dataSource={backgrounds}
              columns={backgroundColumns}
              rowKey="id"
              scroll={{ y: tableHeight, x: 600 }}
              pagination={false}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="标定列表">
            <Table
              loading={calibrationsLoading}
              dataSource={calibrations}
              columns={calibrationColumns}
              rowKey="id"
              scroll={{ y: tableHeight, x: 600 }}
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default VideosPage
