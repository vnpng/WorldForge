from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Any
import os
import json
import time
import jwt 
import bcrypt 
from database import init_db, get_db_connection

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

class SystemPromptSchema(BaseModel):
    id: str
    name: str
    content: str
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
    cursor.execute("SELECT * FROM Sessions WHERE user_id = ? ORDER BY updatedAt DESC", (user["id"],))
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
    INSERT OR REPLACE INTO Sessions (id, type, title, messages, updatedAt, user_id)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (session.id, session.type, session.title, json.dumps(session.messages), session.updatedAt, user["id"]))
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
    
    # [适配] 增加 sort_index 写入
    cursor.execute('''
    INSERT OR REPLACE INTO SystemPrompts (id, name, content, user_id, is_public, sort_index)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (prompt.id, prompt.name, prompt.content, target_user_id, prompt.is_public, prompt.sort_index))
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

@app.get("/")
async def read_index():
    return FileResponse(os.path.join("static", "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
