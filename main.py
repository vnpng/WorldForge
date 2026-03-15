from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Any
import os
import json
import time
import jwt 
import bcrypt 
import httpx # [NEW] 用于流式代理
from database import init_db, get_db_connection

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

def require_role(allowed_roles: List[str]):
    """[RBAC] 核心权限守卫依赖"""
    async def role_checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="权限不足，仅限管理员操作")
        return user
    return role_checker

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
async def generate_invite(current_user: dict = Depends(require_role(["superadmin"]))):
    conn = get_db_connection()
    import random, string
    new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    conn.execute('INSERT INTO InviteCodes (code, created_by, is_used, created_at) VALUES (?, ?, 0, ?)', (new_code, current_user["id"], int(time.time())))
    conn.commit()
    conn.close()
    return {"code": new_code}

@app.get("/api/auth/invites")
async def list_invites(current_user: dict = Depends(require_role(["superadmin"]))):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT code, is_used, created_at FROM InviteCodes ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

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
    # 【安全加固】强制校验，非超管一律覆盖 is_public 为 0
    final_is_public = prompt.is_public if user["role"] == "superadmin" else 0
    
    cursor.execute('''
    INSERT OR REPLACE INTO SystemPrompts (id, name, intro, content, user_id, is_public, sort_index)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (prompt.id, prompt.name, prompt.intro, prompt.content, target_user_id, final_is_public, prompt.sort_index))
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
    existing = cursor.execute("SELECT user_id, is_public FROM SystemPrompts WHERE id = ?", (prompt_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="引擎不存在")
    if existing["is_public"] == 1:
        conn.close()
        raise HTTPException(status_code=403, detail="系统公开的引擎禁止删除，请先取消公开")
    if existing["user_id"] != user["id"] and user["role"] != "superadmin":
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
        
        def _f(val, fallback=''):
            return val if val else fallback

        world_name     = _f(world['name'] if world else '', '未命名世界')
        world_intro    = _f(world['intro'] if world else '')
        world_desc     = _f(world['desc'] if world else '')
        world_conflict = _f(world['conflict'] if world else '')
        world_society  = _f(world['society'] if world else '')
        world_history  = _f(world['history'] if world else '')
        world_geo      = _f(world['geography'] if world else '')
        world_magic    = _f(world['magic_system'] if world else '')
        world_rules    = _f(world['rules'] if world else '')
        world_extra    = _f(world['extra_rules'] if world else '')

        char_name        = _f(char['name'] if char else '', '探险者')
        char_gender      = _f(char['gender'] if char else '')
        char_age         = _f(char['age'] if char else '')
        char_race        = _f(char['race'] if char else '')
        char_identity    = _f(char['identity'] if char else '', '平民')
        char_appearance  = _f(char['appearance'] if char else '')
        char_personality = _f(char['personality'] if char else '')
        char_item        = _f(char['item'] if char else '')
        char_style       = _f(char['style'] if char else '')
        char_custom      = _f(char['custom'] if char else '')

        engine_content = _f(engine['content'] if engine else '', '请使用沉浸式叙事风格进行文字冒险推演。')

        system_content = f"""# [核心世界观设定]
世界名称：{world_name}
简介：{world_intro}
背景描述：{world_desc}
核心冲突：{world_conflict}
社会构成：{world_society}
历史大事记：{world_history}
地理环境：{world_geo}
力量/魔法/科技体系：{world_magic}
核心规则：{world_rules}
附加规则：{world_extra}

# [角色信息]
姓名：{char_name}
性别：{char_gender}
年龄：{char_age}
种族：{char_race}
身份/职业：{char_identity}
外貌：{char_appearance}
性格：{char_personality}
初始物品：{char_item}
说话风格：{char_style}
自定义补充：{char_custom}

# [引擎指令]
{engine_content}
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
        # 简单清理 content 中的 HTML
        messages.append({"role": role, "content": m['content']})
    messages.append({"role": "user", "content": req.message})

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
