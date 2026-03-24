# ====================== main.py ======================
import os
import shutil
from fastapi import FastAPI, Depends, Request, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import asyncio

import database as db
from ai_service import fetch_ai_response
from config import DEFAULT_BOTS, HOST, PORT

app = FastAPI()

# --- 关键配置：创建上传目录并挂载静态服务 ---
UPLOAD_DIR = "static/uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
# ---------------------------------------

db.init_db()
templates = Jinja2Templates(directory="templates")

# ================= 模型配置从 config.py 读取 =================
# 如需修改默认 Bot，请编辑 config.py，无需改动此文件
# =============================================================

def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()


def add_default_bots_to_group(session: Session, group_id: int):
    for config in DEFAULT_BOTS:
        bot = db.Bot(
            name=config["name"],
            model=config["model"],
            api_key=config["api_key"],
            base_url=config["base_url"],
            system_prompt=config.get("system_prompt", ""),
            group_id=group_id
        )
        session.add(bot)
    session.commit()


# ====================== 修复后的上传接口（无需修改） ======================
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    is_image = file.content_type.startswith("image/")
    return {
        "file_path": f"/{file_path}".replace("\\", "/"),
        "is_image": is_image,
        "filename": file.filename
    }


@app.on_event("startup")
def startup_populate():
    session = db.SessionLocal()
    if not session.query(db.Group).first():
        default_group = db.Group(name="公共讨论区", is_default=True)
        session.add(default_group)
        session.commit()
        add_default_bots_to_group(session, default_group.id)
    session.close()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/groups")
def list_groups(session: Session = Depends(get_db)):
    groups = session.query(db.Group).all()
    return [{"id": g.id, "name": g.name, "is_default": g.is_default} for g in groups]


@app.post("/api/groups")
def create_group(name: str = Form(...), session: Session = Depends(get_db)):
    new_group = db.Group(name=name, is_default=False)
    session.add(new_group)
    session.commit()
    add_default_bots_to_group(session, new_group.id)
    return {"status": "success", "id": new_group.id}


@app.put("/api/groups/{group_id}/rename")
def rename_group(group_id: int, name: str = Form(...), session: Session = Depends(get_db)):
    group = session.query(db.Group).filter(db.Group.id == group_id).first()
    if not group:
        raise HTTPException(404, "群组不存在")
    group.name = name.strip()
    session.commit()
    return {"status": "success"}


@app.delete("/api/groups/{group_id}")
def delete_group(group_id: int, session: Session = Depends(get_db)):
    group = session.query(db.Group).filter(db.Group.id == group_id).first()
    if not group:
        raise HTTPException(404, "群组不存在")
    if group.is_default:
        raise HTTPException(403, "默认群组不可删除")
    session.delete(group)
    session.commit()
    return {"status": "success"}


@app.get("/api/groups/{group_id}")
def get_group_details(group_id: int, session: Session = Depends(get_db)):
    group = session.query(db.Group).filter(db.Group.id == group_id).first()
    if not group: raise HTTPException(404)
    return {
        "id": group.id,
        "name": group.name,
        "discussion_mode": group.discussion_mode,
        "is_default": group.is_default,
        "bots": [{"id": b.id, "name": b.name, "model": b.model, "avatar": b.avatar, "system_prompt": b.system_prompt or ""} for b in group.bots],
        "messages": [{"id": m.id, "sender": m.sender, "content": m.content, "role": m.role, "file_path": m.file_path, "is_image": m.is_image} for m in group.messages]
    }


@app.post("/api/groups/{group_id}/bots")
def add_custom_bot(group_id: int, name: str = Form(...), model: str = Form(...),
                   api_key: str = Form(...), base_url: str = Form(...),
                   system_prompt: str = Form(""), session: Session = Depends(get_db)):
    bot = db.Bot(name=name, model=model, api_key=api_key, base_url=base_url,
                 system_prompt=system_prompt, group_id=group_id)
    session.add(bot)
    session.commit()
    return {"status": "success"}


@app.delete("/api/groups/{group_id}/bots/{bot_id}")
def delete_bot(group_id: int, bot_id: int, session: Session = Depends(get_db)):
    bot = session.query(db.Bot).filter(db.Bot.id == bot_id, db.Bot.group_id == group_id).first()
    if not bot:
        raise HTTPException(404, "Bot 不存在")
    session.delete(bot)
    session.commit()
    return {"status": "success"}


@app.delete("/api/messages/{message_id}")
def delete_message(message_id: int, session: Session = Depends(get_db)):
    msg = session.query(db.Message).filter(db.Message.id == message_id).first()
    if not msg:
        raise HTTPException(404, "消息不存在")
    session.delete(msg)
    session.commit()
    return {"status": "success"}


@app.post("/api/messages/{message_id}/edit")
async def edit_and_resend(
        message_id: int,
        content: str = Form(""),
        file_path: str = Form(None),
        is_image: bool = Form(False),
        session: Session = Depends(get_db)
):
    """编辑某条用户消息并重新发送：
    1. 删除该消息及其后面所有消息（包括 AI 回复）
    2. 以新内容重新写入用户消息并调用 AI
    """
    msg = session.query(db.Message).filter(db.Message.id == message_id).first()
    if not msg:
        raise HTTPException(404, "消息不存在")
    if msg.role != "user":
        raise HTTPException(400, "只能编辑用户消息")

    group_id = msg.group_id
    group = session.query(db.Group).filter(db.Group.id == group_id).first()

    # 删除该消息及之后的所有消息
    session.query(db.Message).filter(
        db.Message.group_id == group_id,
        db.Message.id >= message_id
    ).delete(synchronize_session=False)
    session.commit()
    session.expire_all()  # 清除 identity map，避免 SAWarning

    # 写入编辑后的用户消息
    new_msg = db.Message(
        sender="User",
        role="user",
        content=content,
        file_path=file_path,
        is_image=is_image,
        group_id=group_id
    )
    session.add(new_msg)
    session.commit()

    # 取最近历史
    msgs = session.query(db.Message).filter(db.Message.group_id == group_id)\
        .order_by(db.Message.id.desc()).limit(12).all()
    msgs.reverse()
    history = [{"role": m.role, "content": m.content, "sender": m.sender,
                "file_path": m.file_path, "is_image": m.is_image} for m in msgs]

    # 并发调用 AI
    tasks = [fetch_ai_response(b.name, b.model, b.api_key, b.base_url,
                               history, group.discussion_mode, b.system_prompt or "")
             for b in group.bots]
    results = await asyncio.gather(*tasks)

    # 保存 AI 回复
    bot_msgs = []
    for i, res_content in enumerate(results):
        bot_msg = db.Message(sender=group.bots[i].name, role="assistant",
                             content=res_content, group_id=group_id)
        session.add(bot_msg)
        bot_msgs.append((i, bot_msg))
    session.commit()

    bot_responses = [
        {"id": bm.id, "sender": group.bots[i].name, "content": bm.content, "role": "assistant"}
        for i, bm in bot_msgs
    ]
    return {
        "user_msg_id": new_msg.id,
        "responses": bot_responses
    }


@app.delete("/api/groups/{group_id}/messages")
def clear_messages(group_id: int, session: Session = Depends(get_db)):
    session.query(db.Message).filter(db.Message.group_id == group_id).delete()
    session.commit()
    return {"status": "success"}


@app.put("/api/groups/{group_id}/bots/{bot_id}")
def update_bot(group_id: int, bot_id: int, system_prompt: str = Form(""),
               session: Session = Depends(get_db)):
    bot = session.query(db.Bot).filter(db.Bot.id == bot_id, db.Bot.group_id == group_id).first()
    if not bot: raise HTTPException(404)
    bot.system_prompt = system_prompt
    session.commit()
    return {"status": "success"}


@app.post("/api/groups/{group_id}/toggle_discussion")
def toggle_discussion(group_id: int, enabled: bool = Form(...), session: Session = Depends(get_db)):
    group = session.query(db.Group).filter(db.Group.id == group_id).first()
    group.discussion_mode = enabled
    session.commit()
    return {"status": "success"}


# ====================== 【核心修正】只保留这一个 chat 接口 ======================
# 删除了上方那个旧的 chat 函数（它不传递 file_path，导致你看到的 is_image=None、file_path=None）
@app.post("/api/groups/{group_id}/chat")
async def chat(
        group_id: int,
        content: str = Form(""),
        file_path: str = Form(None),
        is_image: bool = Form(False),
        session: Session = Depends(get_db)
):
    group = session.query(db.Group).filter(db.Group.id == group_id).first()

    # ==================== 新增调试：确认前端传来的图片路径真的被接收 ====================
    print(f"DEBUG: 【Chat Endpoint】收到请求 | content='{content}' | file_path={file_path} | is_image={is_image}")

    # 1. 保存用户消息（含图片路径）
    user_msg = db.Message(
        sender="User",
        role="user",
        content=content,
        file_path=file_path,
        is_image=is_image,
        group_id=group_id
    )
    session.add(user_msg)
    session.commit()

    print(f"DEBUG: 【Chat Endpoint】用户消息已保存到 DB | file_path={file_path}")

    # 2. 获取最近历史（现在会包含 file_path 和 is_image）
    msgs = session.query(db.Message).filter(db.Message.group_id == group_id)\
        .order_by(db.Message.id.desc()).limit(12).all()
    msgs.reverse()

    history = []
    for m in msgs:
        history.append({
            "role": m.role,
            "content": m.content,
            "sender": m.sender,
            "file_path": m.file_path,
            "is_image": m.is_image
        })

    print(f"DEBUG: 【Chat Endpoint】构建 history 完成，共 {len(history)} 条，最后一条 file_path={history[-1].get('file_path') if history else None}")

    # 3. 并发调用 AI（传入正确的 history + discussion_mode + system_prompt）
    tasks = [fetch_ai_response(b.name, b.model, b.api_key, b.base_url, history, group.discussion_mode, b.system_prompt or "")
             for b in group.bots]
    results = await asyncio.gather(*tasks)

    # 4. 保存 AI 回复
    bot_msgs = []
    for i, res_content in enumerate(results):
        bot_msg = db.Message(sender=group.bots[i].name, role="assistant", content=res_content, group_id=group_id)
        session.add(bot_msg)
        bot_msgs.append((i, bot_msg))

    session.commit()

    bot_responses = [
        {"id": bm.id, "sender": group.bots[i].name, "content": bm.content, "role": "assistant"}
        for i, bm in bot_msgs
    ]
    return {"user_msg_id": user_msg.id, "responses": bot_responses}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)