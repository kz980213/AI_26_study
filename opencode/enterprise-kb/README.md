# Enterprise Knowledge Base Q&A System

基于 RAG 的企业知识库问答系统，支持答案引用追溯、召回效果评测和请求链路可观测。

## 技术栈

- **前端**: Vue 3 + TypeScript + Tailwind CSS
- **后端**: Python 3.11 + FastAPI
- **数据库**: PostgreSQL 16 + pgvector
- **LLM**: DeepSeek API（主）/ OpenAI 兼容接口（备）
- **Embedding**: text-embedding-3-small
- **评测**: Ragas
- **可观测**: Langfuse
- **部署**: Docker Compose

## 快速启动

```bash
# 1. 复制环境变量并填入实际值
cp backend/.env.example backend/.env

# 2. 启动所有服务
docker compose up --build -d

# 3. 访问
#   前端: http://localhost:5173
#   后端 API: http://localhost:8000/docs
#   Langfuse: http://localhost:3000
```

## API 文档

启动后访问 http://localhost:8000/docs 查看 Swagger 文档。

### 主要接口

| 接口 | 说明 |
|------|------|
| `POST /auth/register` | 注册用户 |
| `POST /auth/login` | 登录获取 JWT |
| `POST /ingest/upload` | 上传文档入库 |
| `GET /chat/stream?question=xxx&session_id=xxx` | SSE 流式问答 |
| `POST /eval/run` | 触发 Ragas 评测 |
