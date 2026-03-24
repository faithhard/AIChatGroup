# ================================================================
# BotGroup 配置文件
# 修改此文件来配置默认 AI 成员，无需改动 main.py
# ================================================================

# 服务器配置
HOST = "0.0.0.0"
PORT = 8000

# 默认 AI 成员列表
# 每次创建新群组时会自动添加以下 Bot
# 字段说明：
#   name        - 显示名称（群组内唯一）
#   model       - 模型 ID，需与 API 提供商一致
#   api_key     - API 密钥
#   base_url    - API 地址（兼容 OpenAI 格式的接口均可）
#   system_prompt - 系统提示词，留空则使用默认提示词
DEFAULT_BOTS = [
    {
        "name": "gpt-5.4",
        "model": "gpt-5.4-2026-03-05",
        "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxx",
        "base_url": "https://api.openai.com/v1",
        "system_prompt": "",
    },
    {
        "name": "gemini",
        "model": "gemini-2.0-flash",
        "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxx",
        "base_url": "https://api.openai.com/v1",
        "system_prompt": "",
    },
    {
        "name": "doubao",
        "model": "doubao-seed-2-0-pro-260215",
        "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxx",
        "base_url": "https://api.openai.com/v1",
        "system_prompt": "",
    },
    {
        "name": "deepseek",
        "model": "deepseek-v3",
        "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxx",
        "base_url": "https://api.openai.com/v1",
        "system_prompt": "",
    },
]
