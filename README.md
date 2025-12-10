# 空间视频制作平台

该项目提供一个完整的前后端平台，用于管理空间视频的采集数据和训练任务。

## 目录结构

- `backend/`: FastAPI 服务，提供用户/视频/任务接口
- `frontend/`: React + Vite 前端，提供上传、任务面板
- `storage/`: 本地文件存储目录（开发环境）

## 快速开始

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

### 前端

需要 Node.js 18+。

```bash
cd frontend
npm install
npm run dev
```

开发环境下，前端通过 Vite 代理到 `http://localhost:8000` 的后端。

## 下一步集成

1. **替换 task 占位服务**：在 `backend/app/services/tasks.py` 接入现有处理系统
2. **完善鉴权**：引入刷新 token、密码修改、第三方登录
3. **对象存储**：将 `save_file` 替换为 MinIO/S3 上传策略
4. **状态推送**：在 Job 路由中对接真实进度、WebSocket 推送
