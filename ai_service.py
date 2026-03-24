import httpx
import asyncio
import base64
import os
import mimetypes


def encode_image_to_base64(file_path):
    """
    将图片（支持本地路径 或 URL）转换为 Base64
    """
    if not file_path:
        print("DEBUG: file_path 为空，跳过")
        return None, None

    # ==================== 优先处理 URL（Web 上传最常见） ====================
    if file_path.startswith(('http://', 'https://')):
        try:
            print(f"DEBUG: 检测到图片 URL，正在异步下载 -> {file_path}")
            # 使用同步 httpx（图片小，阻塞可忽略；如需严格异步可后续优化）
            response = httpx.get(file_path, timeout=15.0, follow_redirects=True)
            if response.status_code != 200:
                print(f"DEBUG: 下载失败 HTTP {response.status_code}")
                return None, None

            image_bytes = response.content
            mime_type = response.headers.get("Content-Type", "").lower()
            if not mime_type.startswith("image/"):
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type:
                    mime_type = "image/png"

            encoded = base64.b64encode(image_bytes).decode("utf-8")
            print(f"DEBUG: URL图片下载成功！MIME: {mime_type} | Base64长度: {len(encoded)}")
            return encoded, mime_type

        except Exception as e:
            print(f"DEBUG: URL下载异常 -> {str(e)}")
            return None, None

    # ==================== 本地路径处理（兼容 /static/uploads/...） ====================
    path = file_path.lstrip('/')
    possible_paths = [path]

    # 自动补全常见路径（防止前端只传文件名或相对路径）
    if not path.startswith("static/"):
        possible_paths.append(os.path.join("static", "uploads", path))
    possible_paths.append(os.path.join(os.getcwd(), path))

    final_path = None
    for p in possible_paths:
        if os.path.exists(p):
            final_path = p
            break

    if not final_path:
        print(f"DEBUG: 本地图片未找到（已尝试所有路径）-> 原路径: {file_path}")
        return None, None

    mime_type, _ = mimetypes.guess_type(final_path)
    if not mime_type:
        mime_type = "image/png"

    with open(final_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    print(f"DEBUG: 本地图片编码成功！路径: {final_path} | MIME: {mime_type} | Base64长度: {len(encoded)}")
    return encoded, mime_type


async def fetch_ai_response(bot_name, model, api_key, base_url, prompt_history, is_discussion=False, system_prompt=""):
    """
    发送多模态请求给大模型
    """
    if not api_key or api_key == "sk-xxx":
        return f"【未配置】我是 {bot_name}，请在右侧面板配置 API Key 后测试图片识别。"

    # ==================== 新增：完整 DEBUG 输出（关键！用来排查为什么之前没打印） ====================
    print("=== DEBUG: fetch_ai_response 被调用 ===")
    print(f"DEBUG: prompt_history 共有 {len(prompt_history)} 条消息")
    for idx, msg in enumerate(prompt_history):
        print(f"DEBUG: msg[{idx}] | role={msg.get('role')} | "
              f"content_len={len(str(msg.get('content', '')))} | "
              f"is_image={msg.get('is_image')} | "
              f"file_path={msg.get('file_path')}")

    formatted_messages = []

    # 1. 系统提示词：优先使用 bot 自定义的，否则用默认
    if system_prompt and system_prompt.strip():
        sys_prompt = system_prompt.strip()
    else:
        sys_prompt = f"你的名字是 {bot_name}。你正在一个多AI协作群聊中。"
    if is_discussion:
        sys_prompt += "请关注其他AI成员的发言，你可以引用或反驳他们的观点。"

    formatted_messages.append({"role": "system", "content": sys_prompt})

    # 2. 处理历史消息（核心修改点在这里）
    for msg in prompt_history:
        role = msg.get("role", "user")
        text = msg.get("content", "")

        if is_discussion and role == "assistant":
            text = f"[{msg.get('sender', 'AI')}]: {text}"

        # ==================== 关键修复：只要有 file_path 就当作图片消息 ====================
        # 之前只判断 msg.get("is_image")，导致前端没传这个字段时完全跳过 → 无任何 DEBUG
        if msg.get("file_path"):
            print(f"DEBUG: 检测到图片消息！正在编码 -> file_path={msg.get('file_path')}")
            b64_data, mime = encode_image_to_base64(msg["file_path"])
            if b64_data:
                content_payload = [
                    {"type": "text", "text": text if text else "请分析这张图片的内容。"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64_data}"
                        }
                    }
                ]
                formatted_messages.append({"role": role, "content": content_payload})
                continue

        # 普通文本消息
        formatted_messages.append({
            "role": role,
            "content": [{"type": "text", "text": text}]
        })

    # 3. 构造请求（兼容 base_url 末尾带不带 /v1）
    _base = base_url.rstrip('/')
    if _base.endswith('/v1'):
        url = f"{_base}/chat/completions"
    else:
        url = f"{_base}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": formatted_messages,
        "temperature": 0.7
    }

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code != 200:
                    error_msg = response.text
                    print(f"DEBUG: API 错误详情 -> {error_msg}")
                    return f"接口报错({response.status_code}): 请检查 Key 或模型是否支持 Vision。"

                result = response.json()
                if "choices" in result:
                    return result['choices'][0]['message']['content']
                return f"响应异常格式: {str(result)[:100]}"

        except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            if attempt < max_retries:
                print(f"DEBUG: [{bot_name}] 连接异常，第{attempt+1}次重试 -> {str(e)}")
                await asyncio.sleep(2 * (attempt + 1))
                continue
            return f"请求失败（已重试{max_retries}次）: {str(e)}"
        except Exception as e:
            return f"请求异常: {str(e)}"