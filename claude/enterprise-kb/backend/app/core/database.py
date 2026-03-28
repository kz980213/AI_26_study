"""
数据库引擎与异步 session 管理
使用 async SQLAlchemy 支持高并发场景
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


# 创建异步数据库引擎
engine = create_async_engine(
    settings.database_url,
    echo=False,          # 生产环境关闭 SQL 日志
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 超出 pool_size 时允许的额外连接数
    pool_pre_ping=True,  # 使用前检查连接是否存活
)

# 异步 session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不自动过期对象，避免额外查询
)


class Base(DeclarativeBase):
    """ORM 基类，所有模型继承此类"""
    pass


async def get_db() -> AsyncSession:
    """
    FastAPI 依赖注入：获取数据库 session
    使用 async with 确保 session 在请求结束后自动关闭
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库表结构（开发环境使用，生产环境推荐 Alembic）"""
    from app.models.db import User, Document, Chunk, Session, Message  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
