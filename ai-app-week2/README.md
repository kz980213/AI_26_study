# day1
## Run
uvicorn app.main:app --reload

## Docs
http://127.0.0.1:8000/docs

## APIs
- GET /health
- POST /auth/register
- POST /auth/login
- GET /users/me
  
# day2
## 项目结构
- app/main.py：应用入口
- app/routers/：路由层
- app/auth.py：认证逻辑
- app/db.py：假数据存储
- app/exceptions.py：统一异常处理

# day3
## 新增接口
- PUT /users/me/password：修改当前用户密码

## 今日验证闭环
1. 注册
2. 登录
3. 获取当前用户
4. 修改密码
5. 用旧密码登录失败
6. 用新密码登录成功

## 测试
pytest -q

# day4
## 数据库
- 当前使用 SQLite
- 数据库文件：app.db

## 新增文件
- app/database.py：数据库连接与 Session
- app/models.py：ORM 模型

## 今日升级内容
- 用户数据从内存字典改为 SQLite 持久化存储
- register / login / users/me / users/me/password 全部改为走数据库

## 验证结果
- 服务重启后用户数据仍然存在
- 注册 / 登录 / 获取当前用户 / 修改密码闭环可用

# day5 day6
## 测试
pytest -q

## 请求日志
服务启动后会输出每次请求的日志，包含：
- method
- path
- status_code
- duration
- request_id

# day7

## 项目目标
一个可用于前后端联调的 FastAPI 用户鉴权服务

## 当前能力
- 用户注册
- 用户登录（JWT）
- 获取当前用户
- 修改当前用户密码
- SQLite 持久化
- 请求日志
- API 自动化测试

## 启动方式
uvicorn app.main:app --reload

## 测试方式
pytest -q

## Swagger
http://127.0.0.1:8000/docs

## 配置项
- SECRET_KEY
- ACCESS_TOKEN_EXPIRE_MINUTES
- DATABASE_URL
- CORS_ALLOW_ORIGINS
