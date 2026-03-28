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

第1周第1天最小工程化练习项目

目标：
- 创建 Python 虚拟环境
- 搭建项目结构
- 实现一个可运行 CLI
- 接入日志

## 安装依赖

```bash
python -m pip install -r requirements-dev.txt


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