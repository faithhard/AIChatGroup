from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime
import os
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean

# 支持通过环境变量指定数据库目录（打包 exe 时写到 exe 同级目录）
_db_dir = os.environ.get("BOTGROUP_DB_DIR", ".")
_db_path = os.path.join(_db_dir, "chat.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_db_path}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    discussion_mode = Column(Boolean, default=False)  # 全员讨论开关
    is_default = Column(Boolean, default=False)       # 是否为默认群组（不可删除）
    bots = relationship("Bot", back_populates="group", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="group", cascade="all, delete-orphan")

class Bot(Base):
    __tablename__ = "bots"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    avatar = Column(String, default="🤖")
    model = Column(String)
    api_key = Column(String)
    base_url = Column(String)
    system_prompt = Column(Text, nullable=True)  # 每个bot独立系统提示词
    group_id = Column(Integer, ForeignKey("groups.id"))
    group = relationship("Group", back_populates="bots")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String)
    role = Column(String)
    content = Column(Text)
    file_path = Column(String, nullable=True) # 新增：存储上传的文件路径
    is_image = Column(Boolean, default=False)  # 新增：标识是否为图片
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    group_id = Column(Integer, ForeignKey("groups.id"))
    group = relationship("Group", back_populates="messages")

def init_db():
    Base.metadata.create_all(bind=engine)