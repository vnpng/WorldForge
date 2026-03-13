from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Any
import os
import json
import time
import re
import jwt 
import bcrypt 
import httpx # [NEW] 用于流式代理
from database import init_db, get_db_connection

def strip_html(text: str) -> str:
    if not text:
        return ""
    # 1. 提取 <summary> 标签内的文字，加换行保留标题
    text = re.sub(r'<summary>(.*?)</summary>', r'\n\1\n', text, flags=re.DOTALL)
    # 2. <br> 转换行
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    # 3. <p> 和 <div> 结尾标签转换行
    text = re.sub(r'</p>|</div>|</tr>', '\n', text, flags=re.IGNORECASE)
    # 4. 表格单元格 <td> <th> 之间加分隔符
    text = re.sub(r'<td[^>]*>|<th[^>]*>', ' | ', text, flags=re.IGNORECASE)
    # 5. 列表项 <li> 转换行加短横线
    text = re.sub(r'<li[^>]*>', '\n- ', text, flags=re.IGNORECASE)
    # 6. 删除所有剩余HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 7. 处理HTML转义字符
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&nbsp;', ' ').replace('&quot;', '"')
    # 8. 清理多余空行（超过2个连续换行压缩为2个）
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

class ChatRequest(BaseModel):
    session_id: str
    message: str
    mode: str  # 'rpg' 或 'chat'
    profile_id: str
    # RPG 专供字段
    world_id: Optional[str] = None
    char_id: Optional[str] = None
    engine_id: Optional[str] = None
    # 调优参数
    context_limit: int = 10
    temperature: float = 0.8

# 初始化数据库结构
init_db()

# --- 鉴权配置 ---
SECRET_KEY = "WORLD_FORGE_SECRET_RANDOM_KEY" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 

security = HTTPBearer()

app = FastAPI(title="WorldForge API Server", version="13.6.0")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- 数据模型定义 ---

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    invite_code: Optional[str] = None

class SessionSchema(BaseModel):
    id: str
    type: str
    title: Optional[str] = ""
    messages: List[Any] = []
    updatedAt: Optional[int] = int(time.time() * 1000)
    is_pinned: Optional[int] = 0 # [NEW] 置顶字段
    engine_id: Optional[str] = None
    world_id: Optional[str] = None
    char_id: Optional[str] = None

class SystemPromptSchema(BaseModel):
    id: str
    name: str
    intro: Optional[str] = "" # [NEW] 引擎简介
    content: str
    user_id: Optional[str] = None # [补全] 用于区分新建/编辑
    is_public: Optional[int] = 0
    sort_index: Optional[int] = 0 # [NEW] 排序字段

class ReorderPromptItem(BaseModel):
    id: str
    sort_index: int

class ProfileSchema(BaseModel):
    id: str
    name: str
    baseUrl: Optional[str] = ""
    apiKey: Optional[str] = ""
    model: Optional[str] = ""
    memoryLength: Optional[int] = 6
    stmLength: Optional[int] = 6
    tempRpg: Optional[float] = 1.0
    tempChat: Optional[float] = 0.6

class WorldSchema(BaseModel):
    id: str
    user_id: Optional[str] = None # [补全] 用于区分新建/编辑
    name: str
    intro: str
    desc: Optional[str] = ""
    conflict: Optional[str] = ""
    society: Optional[str] = ""
    history: Optional[str] = ""
    geography: Optional[str] = ""
    magic_system: Optional[str] = ""
    rules: Optional[str] = ""
    extra_rules: Optional[str] = ""
    sort_index: Optional[int] = 0

class CharacterSchema(BaseModel):
    id: str
    user_id: Optional[str] = None # [补全] 修复标题显示逻辑
    name: str
    gender: str
    age: str
    race: Optional[str] = ""
    identity: str
    appearance: Optional[str] = ""
    personality: Optional[str] = ""
    item: Optional[str] = ""
    style: Optional[str] = ""
    custom: Optional[str] = ""
    sort_index: Optional[int] = 0

class ReorderItem(BaseModel):
    id: str
    sort_index: int

# --- 鉴权辅助函数 ---

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hash_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = time.time() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(auth.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        conn = get_db_connection()
        user = conn.execute("SELECT id, username, role FROM Users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user is None:
            raise credentials_exception
        return dict(user)
    except jwt.PyJWTError:
        raise credentials_exception

# --- Auth 业务路由 ---

@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing_user = cursor.execute("SELECT id FROM Users WHERE username = ?", (user_data.username,)).fetchone()
    if existing_user:
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user_count = cursor.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
    is_first_user = user_count == 0
    if not is_first_user:
        if not user_data.invite_code:
            conn.close()
            raise HTTPException(status_code=400, detail="注册需要邀请码")
        invite = cursor.execute("SELECT code FROM InviteCodes WHERE code = ? AND is_used = 0", (user_data.invite_code,)).fetchone()
        if not invite:
            conn.close()
            raise HTTPException(status_code=400, detail="邀请码无效")
        cursor.execute("UPDATE InviteCodes SET is_used = 1 WHERE code = ?", (user_data.invite_code,))
    
    user_id = str(int(time.time() * 1000))
    role = "superadmin" if is_first_user else "user"
    password_hash = get_password_hash(user_data.password)
    cursor.execute('INSERT INTO Users (id, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?)', (user_id, user_data.username, password_hash, role, int(time.time())))
    if is_first_user:
        cursor.execute("UPDATE Sessions SET user_id = ? WHERE user_id = 'legacy'", (user_id,))
        cursor.execute("UPDATE Profiles SET user_id = ? WHERE user_id = 'legacy'", (user_id,))
        cursor.execute("UPDATE SystemPrompts SET user_id = ? WHERE user_id = 'legacy'", (user_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM Users WHERE username = ?", (user_data.username,)).fetchone()
    conn.close()
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {"id": user["id"], "username": user["username"], "role": user["role"]}
    }

@app.post("/api/auth/invite")
async def generate_invite(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="权限不足")
    conn = get_db_connection()
    import random, string
    new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    conn.execute('INSERT INTO InviteCodes (code, created_by, is_used, created_at) VALUES (?, ?, 0, ?)', (new_code, current_user["id"], int(time.time())))
    conn.commit()
    conn.close()
    return {"code": new_code}

# --- 业务 API 路由 ---

@app.get("/api/sessions", response_model=List[SessionSchema])
async def get_sessions(user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    # [适配] 修改查询逻辑，优先按 is_pinned 排序，再按 updatedAt 倒序
    cursor.execute("SELECT * FROM Sessions WHERE user_id = ? ORDER BY is_pinned DESC, updatedAt DESC", (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        item['messages'] = json.loads(item['messages']) if item['messages'] else []
        result.append(item)
    return result

@app.post("/api/sessions")
async def save_session(session: SessionSchema, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT user_id FROM Sessions WHERE id = ?", (session.id,)).fetchone()
    if existing and existing["user_id"] != user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="禁止覆盖他人数据")
    cursor.execute('''
    INSERT OR REPLACE INTO Sessions (id, type, title, messages, updatedAt, user_id, is_pinned, engine_id, world_id, char_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session.id, session.type, session.title, json.dumps(session.messages), session.updatedAt, user["id"], session.is_pinned, session.engine_id, session.world_id, session.char_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Sessions WHERE id = ? AND user_id = ?", (session_id, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/prompts", response_model=List[SystemPromptSchema])
async def get_prompts(user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    # [适配] 修改查询逻辑，增加 sort_index 排序
    cursor.execute("SELECT * FROM SystemPrompts WHERE user_id = ? OR is_public = 1 ORDER BY sort_index ASC", (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/prompts")
async def save_prompt(prompt: SystemPromptSchema, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT user_id FROM SystemPrompts WHERE id = ?", (prompt.id,)).fetchone()
    if existing:
        if existing["user_id"] != user["id"] and user["role"] != "superadmin":
            conn.close()
            raise HTTPException(status_code=403, detail="无权修改")
        target_user_id = existing["user_id"]
    else:
        target_user_id = user["id"]
    
    # [适配] 增加 intro 和 sort_index 写入
    cursor.execute('''
    INSERT OR REPLACE INTO SystemPrompts (id, name, intro, content, user_id, is_public, sort_index)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (prompt.id, prompt.name, prompt.intro, prompt.content, target_user_id, prompt.is_public, prompt.sort_index))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.put("/api/prompts/reorder")
async def reorder_prompts(items: List[ReorderPromptItem], user: dict = Depends(get_current_user)):
    """[NEW] 批量更新预设排序接口"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for item in items:
            # 物理所有权校验：只有记录属于当前用户，或者当前用户是超管且正在操作系统预设时才允许更新排序
            # 注意：普通用户无法更新系统预设的 sort_index，只能更新自己的
            existing = cursor.execute("SELECT user_id FROM SystemPrompts WHERE id = ?", (item.id,)).fetchone()
            if existing:
                is_owner = existing["user_id"] == user["id"]
                is_admin_system = (user["role"] == "superadmin" and existing["user_id"] == "system")
                
                if is_owner or is_admin_system:
                    cursor.execute("UPDATE SystemPrompts SET sort_index = ? WHERE id = ?", (item.sort_index, item.id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"status": "success"}

@app.delete("/api/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    protected_ids = ['sp_default_rpg', 'sp_chat', 'sp_novel', 'sp_official_4', 'sp_official_5']
    if prompt_id in protected_ids:
        conn.close()
        raise HTTPException(status_code=403, detail="禁止删除核心预设")
    existing = cursor.execute("SELECT user_id FROM SystemPrompts WHERE id = ?", (prompt_id,)).fetchone()
    if not existing or (existing["user_id"] != user["id"] and user["role"] != "superadmin"):
        conn.close()
        raise HTTPException(status_code=403, detail="无权删除")
    cursor.execute("DELETE FROM SystemPrompts WHERE id = ?", (prompt_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/profiles", response_model=List[ProfileSchema])
async def get_profiles(user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Profiles WHERE user_id = ?", (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/profiles")
async def save_profile(profile: ProfileSchema, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT user_id FROM Profiles WHERE id = ?", (profile.id,)).fetchone()
    if existing and existing["user_id"] != user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="ID 冲突")
    cursor.execute('''
    INSERT OR REPLACE INTO Profiles (id, name, baseUrl, apiKey, model, memoryLength, stmLength, tempRpg, tempChat, user_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (profile.id, profile.name, profile.baseUrl, profile.apiKey, profile.model, 
          profile.memoryLength, profile.stmLength, profile.tempRpg, profile.tempChat, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/profiles/{profile_id}")
async def delete_profile(profile_id: str, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Profiles WHERE id = ? AND user_id = ?", (profile_id, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success"}

# --- Worlds API ---
@app.get("/api/worlds", response_model=List[WorldSchema])
async def get_worlds(user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Worlds WHERE user_id = ? ORDER BY sort_index ASC", (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/worlds")
async def save_world(world: WorldSchema, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT user_id FROM Worlds WHERE id = ?", (world.id,)).fetchone()
    if existing and existing["user_id"] != user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="禁止覆盖他人数据")
    
    current_time = int(time.time())
    cursor.execute('''
    INSERT OR REPLACE INTO Worlds 
    (id, user_id, name, intro, desc, conflict, society, history, geography, magic_system, rules, extra_rules, sort_index, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM Worlds WHERE id = ?), ?))
    ''', (world.id, user["id"], world.name, world.intro, world.desc, world.conflict, world.society, world.history, world.geography, world.magic_system, world.rules, world.extra_rules, world.sort_index, world.id, current_time))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.put("/api/worlds/reorder")
async def reorder_worlds(items: List[ReorderItem], user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for item in items:
            cursor.execute("UPDATE Worlds SET sort_index = ? WHERE id = ? AND user_id = ?", (item.sort_index, item.id, user["id"]))
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"status": "success"}

@app.delete("/api/worlds/{world_id}")
async def delete_world(world_id: str, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Worlds WHERE id = ? AND user_id = ?", (world_id, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success"}

# --- Characters API ---
@app.get("/api/characters", response_model=List[CharacterSchema])
async def get_characters(user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Characters WHERE user_id = ? ORDER BY sort_index ASC", (user["id"],))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/api/characters")
async def save_character(char: CharacterSchema, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT user_id FROM Characters WHERE id = ?", (char.id,)).fetchone()
    if existing and existing["user_id"] != user["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="禁止覆盖他人数据")
    
    current_time = int(time.time())
    cursor.execute('''
    INSERT OR REPLACE INTO Characters 
    (id, user_id, name, gender, age, race, identity, appearance, personality, item, style, custom, sort_index, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM Characters WHERE id = ?), ?))
    ''', (char.id, user["id"], char.name, char.gender, char.age, char.race, char.identity, char.appearance, char.personality, char.item, char.style, char.custom, char.sort_index, char.id, current_time))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.put("/api/characters/reorder")
async def reorder_characters(items: List[ReorderItem], user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for item in items:
            cursor.execute("UPDATE Characters SET sort_index = ? WHERE id = ? AND user_id = ?", (item.sort_index, item.id, user["id"]))
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"status": "success"}

@app.delete("/api/characters/{char_id}")
async def delete_character(char_id: str, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Characters WHERE id = ? AND user_id = ?", (char_id, user["id"]))
    conn.commit()
    conn.close()
    return {"status": "success"}

# --- AI Proxy 核心引擎 ---
async def ai_stream_generator(client: httpx.AsyncClient, url: str, headers: dict, payload: dict):
    """通用 SSE 流式转发生成器"""
    try:
        async with client.stream("POST", f"{url}/chat/completions", json=payload, headers=headers, timeout=60.0) as response:
            if response.status_code != 200:
                error_detail = await response.aread()
                yield f"data: {json.dumps({'error': 'AI服务异常', 'detail': error_detail.decode()})}\n\n"
                return

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield line + "\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.post("/api/chat")
async def chat_proxy(req: ChatRequest, user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 获取选中的 API 节点配置
    profile = cursor.execute("SELECT * FROM Profiles WHERE id = ? AND user_id = ?", (req.profile_id, user["id"])).fetchone()
    if not profile:
        conn.close()
        raise HTTPException(status_code=404, detail="未找到选中的 API 配置")

    # 2. 拼装 System Prompt
    system_content = "你是 WorldForge 的 AI 助手，一个专注于文字冒险与创意写作的平台。你擅长帮助用户构建世界观、创作角色、设计剧情，也可以进行普通对话和创意写作辅助。请用自然、友好的语气与用户交流。"
    if req.mode == 'rpg':
        # 获取世界设定
        world = cursor.execute("SELECT * FROM Worlds WHERE id = ? AND user_id = ?", (req.world_id, user["id"])).fetchone() if req.world_id else None
        # 获取角色设定
        char = cursor.execute("SELECT * FROM Characters WHERE id = ? AND user_id = ?", (req.char_id, user["id"])).fetchone() if req.char_id else None
        # 获取引擎预设
        engine = cursor.execute("SELECT * FROM SystemPrompts WHERE id = ?", (req.engine_id,)).fetchone() if req.engine_id else None
        
        system_content = f"""
# [核心世界观设定]
{world['intro'] if world else '一个神秘的未知世界。'}
{world['desc'] if world and world['desc'] else ''}
核心冲突：{world['conflict'] if world else '未知'}

# [你扮演的角色信息]
姓名：{char['name'] if char else '探险者'}
身份：{char['identity'] if char else '平民'}
外貌与性格：{char['appearance'] if char else ''}，{char['personality'] if char else ''}

# [叙事风格指南]
{engine['content'] if engine else '请使用沉浸式的第一人称或第三人称进行文字冒险推演。'}

# [强制指令]
1. 必须使用 <cot> 标签进行剧情逻辑推演。
"""

    # 3. 准备历史消息 (Context)
    session = cursor.execute("SELECT messages FROM Sessions WHERE id = ? AND user_id = ?", (req.session_id, user["id"])).fetchone()
    history = json.loads(session['messages']) if session and session['messages'] else []
    
    # 截取历史记录
    context_msgs = history[-(req.context_limit):] if req.context_limit > 0 else []
    
    # 4. 构建发送给 AI 的完整 Payload
    messages = [{"role": "system", "content": system_content}]
    for m in context_msgs:
        role = "assistant" if m['role'] == 'ai' else "user"
        if role == "assistant":
            # AI消息保留原始内容，不清洗，防止AI"学坏"丢失格式
            messages.append({"role": role, "content": m['content']})
        else:
            # 用户消息清洗前端注入的HTML标签
            messages.append({"role": role, "content": strip_html(m['content'])})
    messages.append({"role": "user", "content": strip_html(req.message)})

    conn.close()

    # 5. 发起流式请求
    client = httpx.AsyncClient()
    headers = {"Authorization": f"Bearer {profile['apiKey']}"}
    payload = {
        "model": profile['model'],
        "messages": messages,
        "temperature": req.temperature,
        "stream": True,
        "stream_options": {"include_usage": True}
    }

    return StreamingResponse(
        ai_stream_generator(client, profile['baseUrl'], headers, payload),
        media_type="text/event-stream"
    )

@app.get("/")
async def read_index():
    return FileResponse(os.path.join("static", "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
