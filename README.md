# AIChatGroup
# BotGroup — 多 AI 协作群聊平台

> 把 GPT、Gemini、DeepSeek、豆包等大模型拉进同一个聊天室，让它们围绕你的问题并发回答、互相引用、彼此反驳。

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi)
![Vue3](https://img.shields.io/badge/Vue-3-brightgreen?logo=vuedotjs)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 功能一览

| 功能 | 说明 |
|------|------|
| 多 AI 同框 | 每个群组可添加任意数量的 AI，所有 AI 并发回复 |
| 全员讨论模式 | 开启后 AI 可看到彼此上轮发言，互相引用和反驳 |
| 多模态支持 | 上传图片自动 Base64 编码发给支持视觉的模型 |
| 消息编辑重发 | 悬停消息点 ✏ 修改内容，确认后自动删除旧回复并重新生成 |
| 单条消息删除 | 悬停消息点 × 删除，AI 后续不会看到该条历史 |
| 群组管理 | 创建 / 重命名 / 删除群聊，默认群组仅可重命名不可删除 |
| Bot 独立配置 | 每个群组的 AI 成员独立，支持自定义模型、Key、提示词 |
| 连接重试 | 遭遇断连 / 超时自动重试 2 次，超时上限 180s |

---

## 界面预览

```
┌──────────────────────────────────────────────────────────┐
│  左侧：群聊列表       中间：聊天主窗         右侧：群组设置  │
│  ──────────────      ──────────────        ──────────── │
│  # 公共讨论区  ←当前  [群名 | 🗑清空记录]    全员讨论模式 ○ │
│  # 技术讨论组          消息气泡（悬停显示      群成员 (4)    │
│  # 产品头脑风暴         ✏编辑 / ×删除）       🤖 GPT-5.4  │
│                                              🤖 Gemini   │
│  ＋ 创建群聊           [📎] [输入框] [发送]   🤖 豆包      │
│                                              🤖 DeepSeek  │
└──────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 方式一：exe 一键运行（推荐普通用户）

无需安装 Python，下载即用。

**1. 下载**

从 [Releases](https://github.com/your-username/BotGroup/releases) 页面下载 `BotGroup.zip`，解压得到：

```
BotGroup/
├── BotGroup.exe    # 主程序
└── config.py       # 配置文件（必须和 exe 同目录）
```

**2. 配置 API Key**

用记事本打开 `config.py`，将 `sk-xxxxxxxxxxxxxxxxxxxxxxxx` 替换为你的真实 API Key：
并修改`model`、`base_url`为你的需求
```python
DEFAULT_BOTS = [
    {
        "name": "GPT-4o",                # <-- 改这里
        "model": "gpt-4o",               # <-- 改这里
        "api_key": "sk-你的密钥",         # <-- 改这里
        "base_url": "https://api.openai.com/v1", # <-- 改这里
        "system_prompt": "",           # <-- 这个可以在ui界面进行配置
    },
    # 可继续添加更多...
]
```

> 支持所有兼容 OpenAI Chat Completions 格式的接口（OpenAI、Azure、DeepSeek、豆包、Gemini 中转站等）。

**3. 双击运行**

双击 `BotGroup.exe`，控制台窗口显示启动信息后浏览器自动打开 `http://127.0.0.1:8000`。

```
BotGroup 启动中... 访问 http://127.0.0.1:8000
数据目录: D:\BotGroup
```

> - 聊天数据库 `chat.db` 和上传文件夹 `static/uploads/` 会自动创建在 exe 同目录
> - 关闭控制台窗口即停止服务

---

### 方式二：源码运行（推荐开发者）

**1. 克隆项目**

```bash
git clone https://github.com/faithhard/AIChatGroup.git
cd BotGroup
```

**2. 安装依赖**

```bash
pip install -r requirements.txt
```

**3. 配置 API Key**

编辑 `config.py`，填入你的 API Key 和模型信息（格式同上）。

**4. 启动服务**

```bash
python main.py
```

浏览器访问 `http://localhost:8000` 即可使用。

---

### 方式三：自行打包 exe

```bash
pip install -r requirements.txt
python build.py
```

打包完成后 exe 位于 `dist/BotGroup.exe`。将 `BotGroup.exe` 和 `config.py` 放到同一个文件夹即可分发。

---

## 项目结构

```
BotGroup/
├── main.py            # FastAPI 后端，所有 API 路由
├── ai_service.py      # AI 调用核心，处理多模态 & 重试逻辑
├── database.py        # SQLAlchemy 数据库模型（SQLite）
├── config.py          # 配置文件（API Key、模型、端口）
├── launcher.py        # exe 启动入口（自动开浏览器）
├── build.py           # PyInstaller 打包脚本
├── requirements.txt   # Python 依赖
├── templates/
│   └── index.html     # 前端（Vue 3 + TailwindCSS + DaisyUI）
├── static/
│   └── uploads/       # 用户上传文件目录（自动创建）
└── chat.db            # SQLite 数据库（首次启动自动创建）
```

---

## API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/groups` | 获取群组列表 |
| `POST` | `/api/groups` | 创建群组 |
| `GET` | `/api/groups/{id}` | 获取群组详情（含消息和 Bot） |
| `PUT` | `/api/groups/{id}/rename` | 重命名群组 |
| `DELETE` | `/api/groups/{id}` | 删除群组（默认群组不可删） |
| `POST` | `/api/groups/{id}/chat` | 发送消息并获取所有 AI 回复 |
| `DELETE` | `/api/groups/{id}/messages` | 清空群组全部消息 |
| `POST` | `/api/groups/{id}/toggle_discussion` | 切换全员讨论模式 |
| `POST` | `/api/groups/{id}/bots` | 添加 Bot |
| `PUT` | `/api/groups/{id}/bots/{bid}` | 更新 Bot 系统提示词 |
| `DELETE` | `/api/groups/{id}/bots/{bid}` | 移除 Bot |
| `DELETE` | `/api/messages/{id}` | 删除单条消息 |
| `POST` | `/api/messages/{id}/edit` | 编辑消息并重新发送 |
| `POST` | `/api/upload` | 上传文件（图片/文档） |

---

## 全员讨论模式说明

**关闭时（默认）**：每轮所有 AI 独立回答，互不可见。

**开启时**：
- 历史消息中 AI 的回复带 `[Bot名字]:` 前缀
- 系统提示词追加：*"请关注其他 AI 成员的发言，你可以引用或反驳他们的观点"*
- 效果：第 2 轮起 AI 之间能互相看到上轮所有人的发言并展开辩论

> 注意：同一轮内各 AI 并发调用，无法看到本轮其他 AI 的实时回复。跨轮讨论才会体现引用效果。

---

## 使用技巧

1. **快速切换话题** — 创建多个群组，每个群组维护独立的上下文历史
2. **角色扮演** — 为每个 Bot 设置不同的系统提示词（如"你是批判性思考者"、"你是支持者"）
3. **编辑重发** — 对已发出的问题不满意？悬停消息点 ✏ 修改后重发，AI 回复自动刷新
4. **精准删除** — 悬停消息点 × 删除，不影响其他消息，AI 后续也看不到

---

## 技术栈

**后端**
- [FastAPI](https://fastapi.tiangolo.com/) — 异步 Web 框架
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM，SQLite 存储
- [httpx](https://www.python-httpx.org/) — 异步 HTTP 客户端

**前端**（单文件，无需构建）
- [Vue 3](https://vuejs.org/) — 响应式 UI（CDN 引入）
- [TailwindCSS](https://tailwindcss.com/) + [DaisyUI](https://daisyui.com/) — 样式
- [markdown-it](https://github.com/markdown-it/markdown-it) + [highlight.js](https://highlightjs.org/) — Markdown 渲染与代码高亮

**打包**
- [PyInstaller](https://pyinstaller.org/) — 打包为 Windows 单文件 exe

---

## 数据库迁移说明

如果从旧版本升级，可能缺少 `is_default` 和 `system_prompt` 字段。

**方法一（推荐）**：删除 `chat.db`，重启后自动重建。

**方法二（保留数据）**：

```sql
ALTER TABLE groups ADD COLUMN is_default BOOLEAN DEFAULT 0;
ALTER TABLE bots   ADD COLUMN system_prompt TEXT;
UPDATE groups SET is_default = 1 WHERE id = (SELECT MIN(id) FROM groups);
```

---

## License

MIT
