import sqlite3
import json
import os
import time

# 数据库存储路径，位于项目根目录的 data 文件夹中
DB_PATH = os.path.join("data", "worldforge.db")

def get_db_connection():
    """获取数据库连接，并设置 row_factory 以支持字典格式返回"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def upgrade_tables(cursor):
    """
    表结构自动升级逻辑：检测字段是否存在，若不存在则使用 ALTER TABLE 追加。
    这种方式可以确保从旧版本平滑升级，且存量数据无损。
    """
    # 1. 升级 Sessions 表：增加 user_id
    cursor.execute("PRAGMA table_info(Sessions)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'user_id' not in columns:
        print("正在为 Sessions 表追加 user_id 字段...")
        cursor.execute("ALTER TABLE Sessions ADD COLUMN user_id TEXT")

    # 2. 升级 SystemPrompts 表
    cursor.execute("PRAGMA table_info(SystemPrompts)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'user_id' not in columns:
        print("正在为 SystemPrompts 表追加 user_id 字段...")
        cursor.execute("ALTER TABLE SystemPrompts ADD COLUMN user_id TEXT")
    if 'is_public' not in columns:
        print("正在为 SystemPrompts 表追加 is_public 字段...")
        cursor.execute("ALTER TABLE SystemPrompts ADD COLUMN is_public INTEGER DEFAULT 0")
    
    # [V13.6.0+ 排序升级] 增加 sort_index 字段
    if 'sort_index' not in columns:
        print("正在为 SystemPrompts 表追加 sort_index 字段...")
        cursor.execute("ALTER TABLE SystemPrompts ADD COLUMN sort_index INTEGER DEFAULT 0")

    # 3. 升级 Profiles 表：增加 user_id
    cursor.execute("PRAGMA table_info(Profiles)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'user_id' not in columns:
        print("正在为 Profiles 表追加 user_id 字段...")
        cursor.execute("ALTER TABLE Profiles ADD COLUMN user_id TEXT")

def init_legacy_data(cursor):
    """
    存量数据继承初始化逻辑：
    1. 将内置的核心预设标记为 'system' 且设为公开。
    2. 将未归属的数据标记为 'legacy'。
    """
    core_prompt_ids = ['sp_default_rpg', 'sp_chat', 'sp_novel', 'sp_official_4', 'sp_official_5']
    
    for pid in core_prompt_ids:
        cursor.execute('''
            UPDATE SystemPrompts 
            SET user_id = 'system', is_public = 1 
            WHERE id = ?
        ''', (pid,))
    
    cursor.execute("UPDATE Sessions SET user_id = 'legacy' WHERE user_id IS NULL")
    cursor.execute("UPDATE Profiles SET user_id = ? WHERE user_id IS NULL", ('legacy',))
    cursor.execute("UPDATE SystemPrompts SET user_id = 'legacy' WHERE user_id IS NULL AND user_id != 'system'")

def init_db():
    """
    初始化数据库表结构：创建新表、升级旧表、初始化版本元数据。
    """
    if not os.path.exists("data"):
        os.makedirs("data")
        
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user', 
        created_at INTEGER
    )
    ''')

    # 2. InviteCodes 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS InviteCodes (
        code TEXT PRIMARY KEY,
        created_by TEXT,
        is_used INTEGER DEFAULT 0,
        created_at INTEGER
    )
    ''')

    # 3. Sessions 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sessions (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        title TEXT,
        messages TEXT,
        updatedAt INTEGER
    )
    ''')

    # 4. SystemPrompts 表 (含 sort_index)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SystemPrompts (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        content TEXT,
        sort_index INTEGER DEFAULT 0
    )
    ''')

    # 5. Profiles 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Profiles (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        baseUrl TEXT,
        apiKey TEXT,
        model TEXT,
        memoryLength INTEGER DEFAULT 6,
        stmLength INTEGER DEFAULT 6,
        tempRpg REAL DEFAULT 1.0,
        tempChat REAL DEFAULT 0.6
    )
    ''')

    # 6. SystemConfig 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS SystemConfig (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    # 执行升级与迁移
    upgrade_tables(cursor)
    init_legacy_data(cursor)
    
    # 更新系统版本标识
    cursor.execute("INSERT OR REPLACE INTO SystemConfig (key, value) VALUES ('db_version', '13.6.0')")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("V13.6.0 数据库架构升级(排序字段)完成。")
