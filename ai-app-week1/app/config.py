##这里是读取环境变量的，os可以和操作系统交互
import os 
##从 dataclasses 模块中导入 dataclass
##dataclass 是 Python 提供的一个装饰器，作用是：
##帮你快速创建“只用来存数据”的类
from dataclasses import dataclass

##@dataclass，装饰器语法，告诉 Python：下面这个类是一个数据类
##它会自动帮你生成一些常用能力，比如：__init__() 初始化方法，__repr__() 打印显示方法，__eq__() 比较方法
@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "ai_app")
    app_env: str = os.getenv("APP_ENV", "dev")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

def get_settings() -> Settings:
    return Settings()