## 常用命令
安装依赖：
`python -m pip install -r requirements-dev.txt`

运行项目：
`python -m app.main`

带参数运行：
`python -m app.main --name kk`

运行测试：
`python -m pytest -q`


# ai-app-week1

一个用于练习 Python 工程化最小集的示例项目。

## 项目目标
- 创建 Python 虚拟环境
- 建立项目结构
- 实现 CLI 程序
- 接入日志
- 编写测试

## 项目结构
```text
ai-app-week1/
├─ app/
│  ├─ __init__.py
│  ├─ __main__.py
│  ├─ main.py
│  ├─ cli.py
│  ├─ config.py
│  ├─ logger.py
│  ├─ exceptions.py
│  └─ services/
│     ├─ __init__.py
│     └─ greeting.py
├─ tests/
├─ logs/
├─ requirements.txt
├─ requirements-dev.txt
├─ .gitignore
└─ README.md

## 当前限制
- 目前是 CLI 项目，还没有 HTTP API
- 配置暂时通过环境变量读取，尚未引入更完整的配置方案
- 目前日志只做了基础输出，未做日志切分


## 下一步
第2周计划将当前 CLI 项目升级为 FastAPI 服务，补充：
- 路由
- 请求/响应模型
- 异常处理
- JWT 登录