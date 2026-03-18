<template>
<div id="app">

  <!-- LOGIN -->
  <div class="login-page" v-if="!loggedIn">
    <div class="login-card">
      <div class="login-logo"><i class="fas fa-dice-d20"></i></div>
      <div class="login-title">World<span>Forge</span></div>
      <div class="login-sub">{{ isLoginMode ? 'AI 驱动的文字冒险引擎' : '开启创世之旅' }}</div>
      
      <div class="login-field">
        <div class="login-label">用户名</div>
        <input class="login-input" v-model="loginUser" placeholder="输入用户名" @keydown.enter="isLoginMode ? doLogin() : doRegister()"/>
      </div>
      <div class="login-field">
        <div class="login-label">密码</div>
        <div style="position: relative; width: 100%;">
          <input class="login-input" :type="showPass ? 'text' : 'password'" v-model="loginPass" placeholder="输入密码" @keydown.enter="isLoginMode ? doLogin() : doRegister()" style="width: 100%; padding-right: 40px;"/>
          <div class="pass-toggle" @click="showPass = !showPass" style="position: absolute; right: 12px; top: 50%; transform: translateY(-50%); cursor: pointer; color: var(--grey); opacity: 0.7; z-index: 10;">
            <i class="fas" :class="showPass ? 'fa-eye-slash' : 'fa-eye'"></i>
          </div>
        </div>
      </div>
      <div class="login-field" v-if="!isLoginMode">
        <div class="login-label">确认密码</div>
        <div style="position: relative; width: 100%;">
          <input class="login-input" :type="showPassConfirm ? 'text' : 'password'" v-model="loginPassConfirm" placeholder="请再次输入密码" @keydown.enter="doRegister" style="width: 100%; padding-right: 40px;"/>
          <div class="pass-toggle" @click="showPassConfirm = !showPassConfirm" style="position: absolute; right: 12px; top: 50%; transform: translateY(-50%); cursor: pointer; color: var(--grey); opacity: 0.7; z-index: 10;">
            <i class="fas" :class="showPassConfirm ? 'fa-eye-slash' : 'fa-eye'"></i>
          </div>
        </div>
      </div>
      <div class="login-field" v-if="!isLoginMode">
        <div class="login-label">邀请码</div>
        <input class="login-input" v-model="inviteCode" placeholder="输入邀请码" @keydown.enter="doRegister"/>
      </div>
      
      <button class="login-btn" @click="isLoginMode ? doLogin() : doRegister()">
        <i class="fas" :class="isLoginMode ? 'fa-sign-in-alt' : 'fa-user-plus'"></i>
        {{ isLoginMode ? '进入世界' : '确认注册' }}
      </button>

      <div style="text-align: center; margin-top: 16px; font-size: var(--text-sm);">
        <a href="#" @click.prevent="isLoginMode = !isLoginMode" style="color: var(--white-soft); text-decoration: underline; text-underline-offset: 4px; transition: color 0.2s;">
          {{ isLoginMode ? '还没有账号？前往注册' : '已有账号？返回登录' }}
        </a>
      </div>

      <div class="login-footer">测试版本</div>
    </div>
  </div>

  <!-- APP -->
  <div id="app-layout" v-if="loggedIn" :class="{'hide-cot':!showCoT,'hide-debug':!showDebug}" @click="closeAllDropdowns(); showToolsMenu=false; showProfileMenu=false; showCharDrawer=false; showActionList=false">
    
    <!-- SIDEBAR -->
    <div class="sidebar" :class="{collapsed:sidebarCollapsed}">
      <div class="sb-topbar">
        <div class="sb-toggle" @click.stop="sidebarCollapsed=!sidebarCollapsed"><i class="fas fa-bars"></i></div>
        <div class="sb-brand">World<span>Forge</span></div>
      </div>
      
      <div class="sb-divider"></div>

      <!-- Global Navigation -->
      <div class="sb-nav" style="padding: 0;">
        <div class="session-item" :class="{active: currentView === 'chat' && currentSessionId === null}" @click="newChatSession()">
          <div class="session-dot" style="background: transparent; display: flex; align-items: center; justify-content: center;">
            <i class="fas fa-plus" style="font-size: var(--text-sm);"></i>
          </div>
          <div class="session-name"><strong>发起聊天对话</strong></div>
        </div>
        <div class="session-item" :class="{active: currentView === 'rpg-start'}" @click="currentView='rpg-start'; currentSessionId = null">
          <div class="session-dot" style="background: transparent; display: flex; align-items: center; justify-content: center;">
            <i class="fas fa-dice-d20" style="font-size: var(--text-sm);"></i>
          </div>
          <div class="session-name"><strong>发起 RPG 冒险</strong></div>
        </div>
        <div class="sb-divider"></div>
        <div class="session-item" :class="{active: currentView === 'discover' || currentView === 'card-detail'}" @click="currentView = 'discover'; currentSessionId = null">
          <div class="session-dot" style="background: transparent; display: flex; align-items: center; justify-content: center;">
            <i class="fas fa-compass" style="font-size: var(--text-sm);"></i>
          </div>
          <div class="session-name">发现</div>
        </div>
        <div class="session-item" :class="{active: currentView === 'creators'}" @click="currentView = 'creators'; currentSessionId = null">
          <div class="session-dot" style="background: transparent; display: flex; align-items: center; justify-content: center;">
            <i class="fas fa-paint-brush" style="font-size: var(--text-sm);"></i>
          </div>
          <div class="session-name">创作者</div>
        </div>
        <div class="sb-divider"></div>
        <div class="session-item" :class="{active: currentView === 'engine-mgr'}" @click="currentView = 'engine-mgr'; currentSessionId = null">
          <div class="session-dot"><i class="fas fa-layer-group" style="font-size: var(--text-sm);"></i></div>
          <div class="session-name">引擎管理</div>
        </div>
        <div class="session-item" :class="{active: currentView === 'world-mgr'}" @click="currentView = 'world-mgr'; editingWorld = null; currentSessionId = null">
          <div class="session-dot"><i class="fas fa-globe" style="font-size: var(--text-sm);"></i></div>
          <div class="session-name">世界管理</div>
        </div>
        <div class="session-item" :class="{active: currentView === 'char-mgr'}" @click="currentView = 'char-mgr'; editingChar = null; currentSessionId = null">
          <div class="session-dot"><i class="fas fa-user-ninja" style="font-size: var(--text-sm);"></i></div>
          <div class="session-name">角色管理</div>
        </div>
      </div>

      <div class="sb-divider"></div>

      <div class="sb-body">
        <!-- Sessions -->
        <div class="sessions-wrap">
          <div class="sb-session-header" @click="sessionsOpen=!sessionsOpen">
            <div class="sb-section-label"><div class="session-dot"><i class="fas fa-clock"></i></div> 最近会话</div>
            <i class="fas fa-angle-down sb-chevron" :class="{open:sessionsOpen}"></i>
          </div>
          <div v-show="sessionsOpen">
            <div
              v-for="s in sessions" :key="s.id"
              class="session-item"
              :class="[s.mode, {active:currentSessionId===s.id}]"
              @click="selectSession(s.id)"
              style="position:relative"
            >
              <div class="session-dot"><div class="dot-inner" :style="s.mode==='rpg'?'background:var(--purple)':'background:var(--green)'"></div></div>
              <div style="flex: 1; overflow: hidden; display: flex; flex-direction: column; justify-content: center; gap: 1px;">
                <div class="session-name" style="font-size: var(--text-md) !important; flex: none !important; width: 100%;">
                  <i v-if="s.is_pinned" class="fas fa-thumbtack" style="font-size:var(--text-xs); color:var(--purple-lt); margin-right:4px;"></i>
                  {{s.name}}
                </div>
                <div style="font-size: var(--text-xs); color: var(--grey); opacity: 0.8; line-height: 1;">
                  {{ formatDate(s.updatedAt) }}
                </div>
              </div>
              <div class="session-menu-btn" @click.stop="toggleDropdown(s.id)">
                <i class="fas fa-ellipsis-v"></i>
              </div>
              <transition name="menu-pop">
                <div class="dropdown" v-if="openDropdown===s.id" @click.stop>
                  <div class="dropdown-item" @click="togglePin(s.id)">
                    <i class="fas fa-thumbtack" style="font-size:var(--text-sm);color:var(--grey)"></i> 
                    {{ s.is_pinned ? '取消置顶' : '置顶会话' }}
                  </div>
                  <div class="dropdown-item" @click="renameSession(s.id)"><i class="fas fa-pen" style="font-size:var(--text-sm);color:var(--grey)"></i> 重命名</div>
                  <div class="dropdown-item" @click="exportSession(s.id)"><i class="fas fa-file-export" style="font-size:var(--text-sm);color:var(--grey)"></i> 导出对话 (JSON)</div>
                  <div class="dropdown-item danger" @click="deleteSession(s.id)"><i class="fas fa-trash" style="font-size:var(--text-sm)"></i> 删除</div>
                </div>
              </transition>
            </div>
            <div v-if="sessions.length===0" style="font-size:var(--text-xs);color:var(--grey);padding:8px 4px;text-align:center">
              暂无会话
            </div>
          </div>
        </div>
      </div>

      <div class="sb-divider"></div>

      <div class="sb-footer">
        <div class="sb-footer-inner" @click="currentView='profile'; currentSessionId=null" title="个人中心">
          <div class="user-card-sb">
            <div class="user-avatar-sb">
              <img :src="'https://api.dicebear.com/7.x/avataaars/svg?seed=' + currentUser.name" alt="avatar">
            </div>
            <div class="user-name-sb">{{ currentUser.name }}</div>
          </div>
          <div class="settings-btn"><i class="fas fa-cog"></i></div>
        </div>
      </div>    </div>

    <!-- MAIN STAGE -->
    <div class="main-stage">
      <!-- Status bar -->
      <div class="status-bar">
        <template v-if="currentView==='discover'">
          <div class="top-title"><i class="fas fa-compass" style="color:var(--grey)"></i> 发现探索</div>
        </template>
        <template v-else-if="currentView==='creators'">
          <div class="top-title"><i class="fas fa-paint-brush" style="color:var(--grey)"></i> 创作者中心</div>
        </template>
        <template v-else-if="currentView==='engine-mgr'">
          <div class="top-title"><i class="fas fa-layer-group" style="color:var(--grey)"></i> 引擎管理</div>
        </template>
        <template v-else-if="currentView==='world-mgr'">
          <div class="top-title"><i class="fas fa-globe" style="color:var(--grey)"></i> 世界管理</div>
        </template>
        <template v-else-if="currentView==='char-mgr'">
          <div class="top-title"><i class="fas fa-user-ninja" style="color:var(--grey)"></i> 角色管理</div>
        </template>
        <template v-else-if="currentView==='profile'">
          <div class="top-title"><i class="fas fa-user" style="color:var(--grey)"></i> 个人中心</div>
        </template>
        <template v-else-if="currentView==='card-detail'">
          <div class="back-btn-top" @click="currentView='discover'"><i class="fas fa-arrow-left"></i> 返回发现</div>
        </template>
        <template v-else-if="currentView==='rpg-start'">
          <div class="top-title"><i class="fas fa-dice-d20" style="color:var(--grey)"></i> 新建开局</div>
        </template>
        <template v-else-if="currentView==='chat'">
          <template v-if="isWelcome">
            <div class="top-title" style="color:var(--grey); font-weight: normal;"><i class="fas fa-sparkles"></i> 新建会话</div>
          </template>
          <template v-else>
            <div class="mode-tag" :class="currentMode">
              <i :class="currentMode==='rpg'?'fas fa-dice-d20':'fas fa-comment-alt'" style="font-size:var(--text-xs)"></i>
              {{currentMode==='rpg'?'RPG':'Chat'}}
            </div>
            <div class="status-sep">·</div>
            <div class="status-session">{{activeSession?.name || '未命名'}}</div>
            <div class="status-sep">·</div>
            <div class="status-api">{{activeProfile.name}}</div>
            <div class="status-right">
            </div>
          </template>
        </template>
      </div>

      <!-- DISCOVER VIEW -->
      <div class="view-container" v-if="currentView==='discover'">
        <div class="view-inner">
          <div class="discover-header">
            <div class="discover-title">欢迎，冒险者！</div>
            <div class="discover-sub">探索社区创造的奇妙世界与角色。</div>
          </div>

          <!-- 发现页快速入口占位区 -->
          <div class="discover-quick-start" style="margin-bottom: 32px;">
            <div class="select-panel">
              <div class="panel-header" style="opacity: 0.5;">
                <span><i class="fas fa-bolt"></i> 快速开始</span>
              </div>
              <div style="height: 100px; display: flex; align-items: center; justify-content: center; color: var(--grey); border: 1px dashed rgba(255,255,255,0.1); border-radius: var(--r-sm); margin-top: 12px; font-size: var(--text-sm);">
                功能基座已就绪，等待您的设计指令...
              </div>
            </div>
          </div>
          
          <div v-for="(sec, sIdx) in discoverSections" :key="sec.title" class="discover-section">
            <div class="section-divider"></div>
            <div class="section-title">{{sec.title}}</div>
            <div class="scroll-wrapper">
              <button class="nav-arrow left" @click="scrollRow(sIdx, -800)" v-if="sec.items.length > 0"><i class="fas fa-chevron-left"></i></button>
              <div class="card-row" :ref="el => { if (el) rowRefs[sIdx] = el }" @mousedown="startDrag($event, sIdx)" @mouseleave="stopDrag" @mouseup="stopDrag" @mousemove="onDrag($event, sIdx)">
                <template v-for="w in sec.items" :key="w.id">
                  
                  <div v-if="w.type === 'npc'" class="npc-card" style="cursor: not-allowed; opacity: 0.6;">
                    <div class="npc-image"><i :class="w.icon"></i></div>
                    <div class="npc-body">
                      <div class="npc-title">{{w.name}}</div>
                      <div class="npc-desc">{{w.desc}}</div>
                      <div class="npc-footer">
                        <div class="npc-author"><i class="fas fa-user-circle"></i> @{{w.author}}</div>
                        <div style="font-size:var(--text-xs);color:var(--grey)"><i class="fas fa-eye" style="font-size:var(--text-xs)"></i> {{w.plays}}</div>
                      </div>
                    </div>
                  </div>

                  <div v-else class="world-card" @click="w.isDead ? null : openDetail(w)" :style="w.isDead ? 'cursor: not-allowed; opacity: 0.6;' : 'cursor: pointer;'">
                    <div class="wc-image"><i :class="w.icon"></i><div class="wc-tag">{{w.tag}}</div></div>
                    <div class="wc-body">
                      <div class="wc-title" style="font-size:var(--text-lg)">{{w.name}}</div>
                      <div class="wc-desc" style="-webkit-line-clamp:2">{{w.desc}}</div>
                      <div class="wc-footer">
                        <div class="wc-author">@{{w.author}}</div>
                        <div style="font-size:var(--text-xs);color:var(--grey)"><i class="fas fa-play" style="font-size:var(--text-xs)"></i> {{w.plays}}</div>
                      </div>
                    </div>
                  </div>

                </template>
              </div>
              <button class="nav-arrow right" @click="scrollRow(sIdx, 800)" v-if="sec.items.length > 0"><i class="fas fa-chevron-right"></i></button>
            </div>
          </div>
        </div>
      </div>

      <div class="view-container" v-if="currentView==='creators'">
        <div class="view-inner" style="height:100%; display:flex; align-items:center; justify-content:center;">
          <div style="color:var(--grey);font-size:var(--text-lg);text-align:center;">
            <i class="fas fa-paint-brush" style="font-size:48px;opacity:0.2;margin-bottom:12px"></i>
            <div>开发中，敬请期待。</div>
          </div>
        </div>
      </div>

      <div class="view-container" v-if="currentView==='engine-mgr'">
        <div class="view-inner">
          <template v-if="!editingEngine">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 32px;">
              <div>
                <div class="discover-title">引擎管理</div>
                <div class="discover-sub" style="margin-top:4px;"><strong style="color: #ffffff;">· 官方引擎库 · 为不同世界观量身定制的叙事核心 ·</strong></div>
                <div class="discover-sub" style="margin-top:4px;">“ 引擎 决定了AI以何种方式演绎你的世界——剧情推演、叙事风格、战斗规则、事件逻辑，都由它掌控。”</div>
              </div>
              <button class="btn btn-primary btn-md" @click="addNewEngine()"><i class="fas fa-plus"></i> 新建预设</button>
            </div>
            <div ref="engineListRef" class="wf-admin-list">
              <div v-for="p in systemPrompts" :key="p.id" class="preset-card" :class="{active:p.active}">
                <div class="drag-handle"><i class="fas fa-grip-vertical"></i></div>
                <div class="preset-card-content">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">
                    <div class="preset-name">{{p.name}}</div>
                    <span class="tag tag-rpg" v-if="p.type==='rpg'" style="font-size:var(--text-xs);padding:1px 7px">RPG</span>
                    <span class="tag tag-chat" v-else style="font-size:var(--text-xs);padding:1px 7px">Chat</span>
                    <span class="tag" v-if="p.isPublic" style="background:rgba(255,255,255,0.1);color:var(--white-soft);font-size:var(--text-xs);padding:1px 6px;">公开</span>
                  </div>
                  <div class="preset-desc">{{p.intro || '暂无简介'}}</div>
                </div>
                <div class="preset-card-actions">
                  <label class="toggle" style="transform:scale(.9)" v-if="hasRole(['superadmin'])">
                    <input type="checkbox" :checked="p.isPublic" @change="toggleEnginePublic(p)"/>
                    <div class="toggle-track"></div><div class="toggle-thumb"></div>
                  </label>
                  <div
                    class="icon-btn icon-btn-sm"
                    :style="(p.isPublic && !hasRole(['superadmin'])) ? 'opacity:0.3;cursor:not-allowed;' : ''"
                    @click="(p.isPublic && !hasRole(['superadmin'])) ? null : editEngine(p)"
                    :title="(p.isPublic && !hasRole(['superadmin'])) ? '公开引擎仅超管可修改' : '编辑'"
                  ><i class="fas fa-pen"></i></div>
                  <div
                    class="icon-btn icon-btn-sm"
                    :style="p.isPublic ? 'opacity:0.3;cursor:not-allowed;' : ''"
                    @click="!p.isPublic && confirmDelete(p, 'engine')"
                    :title="p.isPublic ? '请先取消系统公开后再删除' : '删除'"
                  ><i class="fas fa-trash"></i></div>
                </div>
              </div>
            </div>
          </template>
          <template v-else>
            <div style="display:flex; align-items:center; gap: 16px; margin-bottom: 32px;">
              <div class="icon-btn" @click="exitEdit('engine')" style="background:var(--ink-muted)"><i class="fas fa-arrow-left"></i></div>
              <div>
                <div class="discover-title">{{ editingEngine.user_id !== undefined ? '编辑引擎' : '新建引擎' }}</div>
                <div class="discover-sub" style="margin-top:4px;">修改预设的系统级 Prompt。</div>
              </div>
            </div>
            <div class="config-section" style="margin-bottom:0">
              <div class="form-grid">
                <div class="form-field full">
                  <div class="form-label">
                    <div class="form-label-left">引擎名称</div>
                    <span v-if="!editingEngine.name" style="color:var(--danger);font-size:var(--text-xs);">* 必填</span>
                  </div>
                  <input class="form-input" v-model="editingEngine.name" placeholder="输入引擎预设名称..."/>
                </div>
                <div class="form-field full">
                  <div class="form-label">
                    <div class="form-label-left">引擎简介</div>
                  </div>
                  <input class="form-input" v-model="editingEngine.intro" placeholder="一句话描述这个引擎的作用..."/>
                </div>
                <div class="form-field full">
                  <div class="form-label"><div class="form-label-left"><i class="fas fa-terminal" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 引擎内容 (System Prompt)</div></div>
                  <textarea class="form-textarea" v-model="editingEngine.desc" placeholder="输入详细的系统级提示词约束..." style="height: 600px;"></textarea>
                </div>
              </div>
              <div style="display:flex; justify-content:space-between; align-items:center; margin-top:24px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.06);">
                <div>
                  <div v-if="hasRole(['superadmin'])" style="display:flex; align-items:center; gap:10px;">
                    <label class="toggle" style="transform:scale(.9)">
                      <input type="checkbox" v-model="editingEngine.isPublic"/>
                      <div class="toggle-track"></div><div class="toggle-thumb"></div>
                    </label>
                    <span style="font-size:var(--text-sm); color:var(--white-soft);">设为系统公开</span>
                  </div>
                </div>
                <div style="display:flex; gap:12px;">
                  <button class="btn btn-ghost btn-md" @click="exitEdit('engine')">退出编辑</button>
                  <button class="btn btn-primary btn-md" @click="saveEdit('engine')" :disabled="!editingEngine.name" :style="(!editingEngine.name) ? 'opacity:0.3;cursor:not-allowed;' : ''"><i class="fas fa-save"></i> 保存更改</button>
                  <button class="btn btn-primary btn-md" @click="saveEdit('engine', true)" :disabled="!editingEngine.name" :style="(!editingEngine.name) ? 'opacity:0.3;cursor:not-allowed;' : ''"><i class="fas fa-check-circle"></i> 保存并返回</button>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="view-container" v-if="currentView==='world-mgr'">
        <div class="view-inner">
          <template v-if="!editingWorld">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 32px;">
              <div>
                <div class="discover-title">世界管理</div>
                <div class="discover-sub" style="margin-top:4px;">定义故事世界的背景框架，AI 将在此框架内推演叙事。</div>
              </div>
              <button class="btn btn-primary btn-md" @click="addNewWorld()"><i class="fas fa-plus"></i> 新建世界</button>
            </div>
            <div v-if="worlds.length===0" class="empty-state">暂无世界设定</div>
            <div ref="worldListRef" class="wf-admin-list">
              <div v-for="w in worlds" :key="w.id" class="preset-card">
                <div class="drag-handle"><i class="fas fa-grip-vertical"></i></div>
                <div class="preset-card-content">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">
                    <div class="preset-name">{{w.name}}</div>
                  </div>
                  <div class="preset-desc">{{w.intro || '暂无简介'}}</div>
                </div>
                <div class="preset-card-actions">
                  <div class="icon-btn icon-btn-sm" @click="editWorld(w)" title="编辑"><i class="fas fa-pen"></i></div>
                  <div class="icon-btn icon-btn-sm" @click="confirmDelete(w, 'world')" title="删除"><i class="fas fa-trash"></i></div>
                </div>
              </div>
            </div>
          </template>
          <template v-else>
            <div style="display:flex; align-items:center; gap: 16px; margin-bottom: 32px;">
              <div class="icon-btn" @click="exitEdit('world')" style="background:var(--ink-muted)"><i class="fas fa-arrow-left"></i></div>
              <div>
                <div class="discover-title">{{ editingWorld.user_id ? '编辑世界' : '新建世界' }}</div>
                <div class="discover-sub" style="margin-top:4px;">修改世界观的详细设定。</div>
              </div>
            </div>
            <div class="config-section" style="margin-bottom:0">
              <div class="form-grid">
                <div class="form-field full">
                  <div class="form-label">
                    <div class="form-label-left">世界名称</div>
                    <span v-if="!editingWorld.name" style="color:var(--danger);font-size:var(--text-xs);">* 此项必填</span>
                  </div>
                  <input class="form-input" v-model="editingWorld.name" placeholder="输入世界名称..."/>
                </div>
                <div class="form-field full">
                  <div class="form-label">
                    <div class="form-label-left">世界简介</div>
                    <span v-if="!editingWorld.intro" style="color:var(--danger);font-size:var(--text-xs);">* 此项必填</span>
                  </div>
                  <textarea class="form-textarea" v-model="editingWorld.intro" placeholder="一句话概括这个世界..."></textarea>
                </div>
                <div class="form-field full">
                  <div class="form-label"><div class="form-label-left"><i class="fas fa-globe" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 世界背景描述</div></div>
                  <textarea class="form-textarea" v-model="editingWorld.desc" placeholder="详细的背景故事、世界起源等..."></textarea>
                </div>
                <div class="form-field full">
                  <div class="form-label"><div class="form-label-left"><i class="fas fa-bolt" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 核心冲突</div></div>
                  <textarea class="form-textarea" v-model="editingWorld.conflict" placeholder="当前世界面临的最大危机或矛盾核心..."></textarea>
                </div>

                <details class="form-field full" style="background: rgba(255,255,255,0.02); border: 1px dashed rgba(255,255,255,0.15); border-radius: 8px; padding: 16px;" :open="!!(editingWorld.society || editingWorld.history || editingWorld.geography || editingWorld.magic_system || editingWorld.rules || editingWorld.extra_rules)">
                  <summary style="cursor: pointer; font-size: var(--text-sm); font-weight: 700; color: var(--purple-lt); outline: none; list-style: none; display: flex; align-items: center; gap: 8px; user-select: none;">
                    <i class="fas fa-sliders-h" style="font-size: var(--text-xs);"></i> 展开更多详细设定
                  </summary>
                  <div class="form-grid" style="margin-top: 16px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 16px;">
                    <div class="form-field full">
                      <div class="form-label"><div class="form-label-left"><i class="fas fa-users" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 社会构成</div></div>
                      <textarea class="form-textarea" v-model="editingWorld.society" placeholder="政治体制、阶级、主要阵营..."></textarea>
                    </div>
                    <div class="form-field full">
                      <div class="form-label"><div class="form-label-left"><i class="fas fa-book" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 大事记 / 历史</div></div>
                      <textarea class="form-textarea" v-model="editingWorld.history" placeholder="改变世界走向的重大历史事件..."></textarea>
                    </div>
                    <div class="form-field full">
                      <div class="form-label"><div class="form-label-left"><i class="fas fa-mountain" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 地理环境</div></div>
                      <textarea class="form-textarea" v-model="editingWorld.geography" placeholder="大陆分布、气候、特殊地貌..."></textarea>
                    </div>
                    <div class="form-field full">
                      <div class="form-label"><div class="form-label-left"><i class="fas fa-magic" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 力量 / 魔法 / 科技体系</div></div>
                      <textarea class="form-textarea" v-model="editingWorld.magic_system" placeholder="超自然力量的来源与运转机制，或科技发展水平..."></textarea>
                    </div>
                    <div class="form-field full">
                      <div class="form-label"><div class="form-label-left"><i class="fas fa-gavel" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 核心规则</div></div>
                      <textarea class="form-textarea" v-model="editingWorld.rules" placeholder="跑团中的死亡机制、核心约束等..."></textarea>
                    </div>
                    <div class="form-field full">
                      <div class="form-label"><div class="form-label-left"><i class="fas fa-plus-circle" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 附加规则 / 特殊设定</div></div>
                      <textarea class="form-textarea" v-model="editingWorld.extra_rules" placeholder="其他的特殊设定、补充规则..."></textarea>
                    </div>
                  </div>
                </details>

              </div>
              <div style="display:flex; justify-content:flex-end; gap:12px; margin-top:24px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.06);">
                <button class="btn btn-ghost btn-md" @click="exitEdit('world')">退出编辑</button>
                <button class="btn btn-primary btn-md" @click="saveEdit('world')" :disabled="!editingWorld.name || !editingWorld.intro" :style="(!editingWorld.name || !editingWorld.intro) ? 'opacity:0.3;cursor:not-allowed;' : ''"><i class="fas fa-save"></i> 保存更改</button>
                <button class="btn btn-primary btn-md" @click="saveEdit('world', true)" :disabled="!editingWorld.name || !editingWorld.intro" :style="(!editingWorld.name || !editingWorld.intro) ? 'opacity:0.3;cursor:not-allowed;' : ''"><i class="fas fa-check-circle"></i> 保存并返回</button>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="view-container" v-if="currentView==='char-mgr'">
        <div class="view-inner">
          <template v-if="!editingChar">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 32px;">
              <div>
                <div class="discover-title">角色管理</div>
                <div class="discover-sub" style="margin-top:4px;">设定你扮演的角色信息。</div>
              </div>
              <button class="btn btn-primary btn-md" @click="addNewChar()"><i class="fas fa-plus"></i> 新建角色</button>
            </div>
            <div v-if="characters.length===0" class="empty-state">暂无角色设定</div>
            <div ref="charListRef" class="wf-admin-list">
              <div v-for="c in characters" :key="c.id" class="preset-card">
                <div class="drag-handle"><i class="fas fa-grip-vertical"></i></div>
                <div class="preset-card-content">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">
                    <div class="preset-name">{{c.name}}</div>
                  </div>
                  <div class="preset-desc">{{c.identity || '暂无身份'}}</div>
                </div>
                <div class="preset-card-actions">
                  <div class="icon-btn icon-btn-sm" @click="editChar(c)" title="编辑"><i class="fas fa-pen"></i></div>
                  <div class="icon-btn icon-btn-sm" @click="confirmDelete(c, 'char')" title="删除"><i class="fas fa-trash"></i></div>
                </div>
              </div>
            </div>
          </template>
          <template v-else>
            <div style="display:flex; align-items:center; gap: 16px; margin-bottom: 32px;">
              <div class="icon-btn" @click="exitEdit('char')" style="background:var(--ink-muted)"><i class="fas fa-arrow-left"></i></div>
              <div>
                <div class="discover-title">{{ editingChar.user_id ? '编辑角色' : '新建角色' }}</div>
                <div class="discover-sub" style="margin-top:4px;">修改角色的详细设定。</div>
              </div>
            </div>
            <div class="config-section" style="margin-bottom:0">
              <div style="display: flex; flex-direction: column; gap: 14px;">
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">
                  <div class="form-field">
                    <div class="form-label">
                      <div class="form-label-left">姓名</div>
                      <span v-if="!editingChar.name" style="color:var(--danger);font-size:var(--text-xs);">* 必填</span>
                    </div>
                    <input class="form-input" v-model="editingChar.name" placeholder="如：银翼·克劳德"/>
                  </div>
                  <div class="form-field">
                    <div class="form-label">
                      <div class="form-label-left">性别</div>
                      <span v-if="!editingChar.gender" style="color:var(--danger);font-size:var(--text-xs);">* 必填</span>
                    </div>
                    <input class="form-input" v-model="editingChar.gender" placeholder="男 / 女 / 其他"/>
                  </div>
                  <div class="form-field">
                    <div class="form-label">
                      <div class="form-label-left">年龄</div>
                      <span v-if="!editingChar.age" style="color:var(--danger);font-size:var(--text-xs);">* 必填</span>
                    </div>
                    <input class="form-input" v-model="editingChar.age" placeholder="如：28"/>
                  </div>
                </div>

                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px;">
                  <div class="form-field">
                    <div class="form-label"><div class="form-label-left">种族</div></div>
                    <input class="form-input" v-model="editingChar.race" placeholder="如：人类、精灵..."/>
                  </div>
                  <div class="form-field">
                    <div class="form-label">
                      <div class="form-label-left"><i class="fas fa-user-ninja" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 身份/职业</div>
                      <span v-if="!editingChar.identity" style="color:var(--danger);font-size:var(--text-xs);">* 必填</span>
                    </div>
                    <input class="form-input" v-model="editingChar.identity" placeholder="如：流亡骑士"/>
                  </div>
                </div>

                <div class="form-field full">
                  <div class="form-label"><div class="form-label-left"><i class="fas fa-eye" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 外貌描述</div></div>
                  <textarea class="form-textarea" v-model="editingChar.appearance" placeholder="发色、瞳色、穿着打扮、显著特征..."></textarea>
                </div>
                <div class="form-field full">
                  <div class="form-label"><div class="form-label-left"><i class="fas fa-heart" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 性格特点</div></div>
                  <textarea class="form-textarea" v-model="editingChar.personality" placeholder="外冷内热、狡猾爱财、或是极具正义感..."></textarea>
                </div>
                <div class="form-field full">
                  <div class="form-label"><div class="form-label-left"><i class="fas fa-shopping-bag" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 初始携带物品</div></div>
                  <textarea class="form-textarea" v-model="editingChar.item" placeholder="断剑、等离子手枪、或是神秘的卷轴..."></textarea>
                </div>
                <div class="form-field full">
                  <div class="form-label"><div class="form-label-left"><i class="fas fa-comment-dots" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 叙事/说话风格</div></div>
                  <textarea class="form-textarea" v-model="editingChar.style" placeholder="沉默寡言，字字珠玑；或语速极快，喜欢用比喻..."></textarea>
                </div>
                <div class="form-field full">
                  <div class="form-label"><div class="form-label-left"><i class="fas fa-plus-circle" style="color:var(--purple-lt);font-size:var(--text-xs)"></i> 自定义补充</div></div>
                  <textarea class="form-textarea" v-model="editingChar.custom" placeholder="其他特殊的设定、身世秘密或隐藏能力..."></textarea>
                </div>

              </div>
              <div style="display:flex; justify-content:flex-end; gap:12px; margin-top:24px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.06);">
                <button class="btn btn-ghost btn-md" @click="exitEdit('char')">退出编辑</button>
                <button class="btn btn-primary btn-md" @click="saveEdit('char')" :disabled="!editingChar.name || !editingChar.gender || !editingChar.age || !editingChar.identity" :style="(!editingChar.name || !editingChar.gender || !editingChar.age || !editingChar.identity) ? 'opacity:0.3;cursor:not-allowed;' : ''"><i class="fas fa-save"></i> 保存更改</button>
                <button class="btn btn-primary btn-md" @click="saveEdit('char', true)" :disabled="!editingChar.name || !editingChar.gender || !editingChar.age || !editingChar.identity" :style="(!editingChar.name || !editingChar.gender || !editingChar.age || !editingChar.identity) ? 'opacity:0.3;cursor:not-allowed;' : ''"><i class="fas fa-check-circle"></i> 保存并返回</button>
              </div>
            </div>
          </template>
        </div>
      </div>

      <div class="view-container" v-if="currentView==='card-detail'">
        <div class="view-inner">
          <div class="detail-view">
            <div class="detail-header">
              <div class="detail-cover"><i :class="selectedCard?.icon || 'fas fa-globe'"></i></div>
              <div class="detail-info">
                <div class="detail-title">{{selectedCard?.name}}</div>
                <div class="detail-author"><i class="fas fa-user-circle"></i> @{{selectedCard?.author}}</div>
                <div class="detail-desc">{{selectedCard?.desc}}</div>
              </div>
            </div>
            <div class="config-section">
              <div class="config-title"><i class="fas fa-user-ninja"></i> 选择你的角色</div>
              <select class="form-select" v-model="quickSetup.characterId">
                <option :value="null">请选择角色...</option>
                <option v-for="c in characters" :key="c.id" :value="c.id">{{c.name}}</option>
              </select>
            </div>
            <div class="config-section">
              <div class="config-title"><i class="fas fa-server"></i> 选择底层引擎</div>
              <select class="form-select" v-model="quickSetup.engineId">
                <option v-for="e in engines" :key="e.id" :value="e.id">{{e.name}}</option>
              </select>
            </div>
            <div class="detail-actions">
              <button class="btn btn-ghost btn-md"><i class="fas fa-bookmark"></i> 加入库中</button>
              <button class="btn btn-primary btn-md" @click="startAdventureFromDetail()"><i class="fas fa-play"></i> 开启冒险</button>
            </div>
          </div>
        </div>
      </div>

      <div class="view-container" v-if="currentView==='rpg-start'">
        <div class="view-inner">
          <div class="start-view">
            <div>
              <div class="discover-title">新建开局</div>
              <div class="discover-sub">组合世界、角色与引擎，开启新的篇章。</div>
            </div>
            
            <div class="panel-grid">
              <div class="select-panel">
                <div class="panel-header"><span><i class="fas fa-server" style="color:var(--purple-lt)"></i> 选择引擎</span></div>
                <div class="panel-list">
                  <div v-for="e in rpgEngines" :key="e.id" class="list-item" :class="{selected: setupForm.engineId===e.id}" @click="setupForm.engineId=e.id">
                    <div class="item-name">{{e.name}}</div><div class="item-desc">{{e.intro || '暂无简介'}}</div>
                  </div>
                </div>
              </div>
              <div class="select-panel">
                <div class="panel-header"><span><i class="fas fa-globe" style="color:var(--purple-lt)"></i> 选择世界</span></div>
                <div class="panel-list">
                  <div v-if="worlds.length===0" class="empty-state">暂无世界设定</div>
                  <div v-for="w in worlds" :key="w.id" class="list-item" :class="{selected: setupForm.worldId===w.id}" @click="setupForm.worldId=w.id">
                    <div class="item-name">{{w.name}}</div><div class="item-desc">{{w.desc}}</div>
                  </div>
                </div>
              </div>
              <div class="select-panel">
                <div class="panel-header"><span><i class="fas fa-user-ninja" style="color:var(--green)"></i> 选择角色</span></div>
                <div class="panel-list">
                  <div v-if="characters.length===0" class="empty-state">暂无角色设定</div>
                  <div v-for="c in characters" :key="c.id" class="list-item" :class="{selected: setupForm.characterId===c.id}" @click="setupForm.characterId=c.id">
                    <div class="item-name">{{c.name}}</div><div class="item-desc">{{c.identity}}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="start-actions">
              <button class="btn btn-primary btn-md" :disabled="!canStartRPG" @click="startRPG()"><i class="fas fa-dice-d20"></i> 生成序章并开始冒险</button>
            </div>
          </div>
        </div>
      </div>

      <div class="view-container" v-if="currentView==='profile'">
        <div class="view-inner" style="height: 100%; display: flex; flex-direction: column;">
          <div class="discover-header" style="margin-bottom: 24px; flex-shrink: 0;">
            <div class="discover-title">个人中心</div>
            <div class="discover-sub">管理你的资产、配置与应用偏好。</div>
          </div>
          <div style="flex: 1; display: flex; overflow: hidden; background: var(--ink-soft); border: 1px solid rgba(255,255,255,.08); border-radius: var(--r-lg);">
            <div class="settings-nav">
              <div v-for="item in settingsNav" :key="item.key"
                class="settings-nav-item" :class="{active:settingsTab===item.key}"
                @click="settingsTab=item.key">
                <i :class="item.icon"></i>
                <div><div class="nav-label">{{item.label}}</div><div class="nav-desc">{{item.desc}}</div></div>
              </div>
            </div>

            <div class="settings-content">
              <template v-if="settingsTab==='basic'">
                <div class="s-title">基础设置</div>
                <div class="s-sub">配置应用名称和界面行为。</div>
                <div class="form-grid" style="margin-bottom:16px">
                  <div class="form-field">
                    <div class="form-label"><div class="form-label-left">用户 ID</div></div>
                    <input class="form-input" :value="currentUser.id" readonly style="opacity: 0.7; cursor: not-allowed;"/>
                  </div>
                  <div class="form-field">
                    <div class="form-label">
                      <div class="form-label-left">用户名</div>
                      <span v-if="hasRole(['superadmin'])" style="color:var(--purple-lt);font-size:var(--text-xs);"><i class="fas fa-crown"></i> 超管</span>
                    </div>
                    <input class="form-input" :value="currentUser.name" readonly style="opacity: 0.7; cursor: not-allowed;"/>
                  </div>
                </div>
                
                <div class="divider"></div>
                
                <div style="display:flex; justify-content:center; padding-top:8px;">
                  <button class="btn btn-danger btn-md" @click="doLogout">
                    <i class="fas fa-sign-out-alt"></i> 退出登录
                  </button>
                </div>
              </template>

              <template v-if="settingsTab==='api'">
                <div style="display:flex; flex-direction:column; min-height:100%;">

                  <!-- 标题栏 -->
                  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:16px;">
                    <div class="s-title" style="margin-bottom:0">API 节点管理</div>
                    <button class="btn btn-primary btn-md" @click="showNewProfileModal=true">
                      <i class="fas fa-plus"></i> 新建节点
                    </button>
                  </div>

                  <!-- 节点列表 -->
                  <div class="wf-admin-list" style="margin-bottom:20px;">
                    <div v-if="profiles.length === 0" style="color:var(--grey); font-size:var(--text-sm); padding:12px 0;">
                      暂无节点，点击"新建节点"添加
                    </div>
                    <div
                      v-for="p in profiles" :key="p.id"
                      class="preset-card"
                      :style="{
                        background: activeProfileId === p.id ? 'rgba(125, 57, 235, 0.12)' : 'var(--ink-muted)',
                        border: activeProfileId === p.id ? '1.5px solid var(--purple-lt)' : '1.5px solid transparent',
                        boxShadow: activeProfileId === p.id ? '0 0 15px rgba(125, 57, 235, 0.15)' : 'none'
                      }"
                      @click="activeProfileId = p.id"
                    >
                      <div class="preset-card-content" style="display:flex; align-items:center; gap:12px;">
                        <!-- 激活指示器 -->
                        <div :style="{
                          width: '10px', height: '10px', borderRadius: '50%',
                          background: activeProfileId === p.id ? 'var(--purple-lt)' : 'transparent',
                          border: activeProfileId === p.id ? 'none' : '2px solid var(--grey)',
                          boxShadow: activeProfileId === p.id ? '0 0 8px var(--purple-lt)' : 'none',
                          flex: 'none'
                        }"></div>
                        <div>
                          <div style="font-size:var(--text-sm); font-weight:700;" :style="{ color: activeProfileId === p.id ? 'var(--white)' : 'var(--white-soft)' }">{{ p.name }}</div>
                          <div style="font-size:var(--text-xs);" :style="{ color: activeProfileId === p.id ? 'var(--purple-lt)' : 'var(--grey)' }">{{ p.model }}</div>
                        </div>
                      </div>
                      <div class="preset-card-actions">
                        <div class="icon-btn icon-btn-sm" @click.stop="startEditing(p)" title="编辑"><i class="fas fa-pen"></i></div>
                        <div class="icon-btn icon-btn-sm" @click.stop="deleteProfile(p.id)" title="删除"><i class="fas fa-trash"></i></div>
                      </div>
                    </div>
                  </div>

                  <!-- 底部导出/导入 -->
                  <div style="display:flex; gap:10px; margin-top:auto; padding-top:24px;">
                    <button class="btn btn-ghost btn-md" style="flex:1; justify-content:center;" @click="exportApiData">
                      <i class="fas fa-file-export"></i> 导出
                    </button>
                    <button class="btn btn-ghost btn-md" style="flex:1; justify-content:center;" @click="triggerImport">
                      <i class="fas fa-file-import"></i> 导入
                    </button>
                    <input type="file" ref="importInput" style="display:none" accept=".json" @change="importApiData">
                  </div>

                </div>
              </template>

              <template v-if="settingsTab==='data'">
                <div class="s-title">数据管理</div>
                <div class="s-sub">导出备份或导入恢复你的核心数据。</div>
                <div style="display:flex;flex-direction:column;gap:10px">
                  <!-- Sessions -->
                  <div class="api-config-card" style="flex-direction:row;align-items:center;justify-content:space-between">
                    <div><div style="font-size:var(--text-sm);font-weight:700">导出所有对话/存档数据</div><div style="font-size:var(--text-xs);color:var(--grey);margin-top:2px">将所有会话记录导出为 JSON 文件</div></div>
                    <button class="btn btn-ghost btn-md" @click="exportSessions"><i class="fas fa-file-export"></i> 导出</button>
                  </div>
                  <div class="api-config-card" style="flex-direction:row;align-items:center;justify-content:space-between">
                    <div><div style="font-size:var(--text-sm);font-weight:700">导入对话/存档数据</div><div style="font-size:var(--text-xs);color:var(--grey);margin-top:2px">从 JSON 文件恢复会话记录，每条作为新存档导入</div></div>
                    <button class="btn btn-ghost btn-md" @click="$refs.importSessionsInput.click()"><i class="fas fa-file-import"></i> 导入</button>
                    <input type="file" ref="importSessionsInput" style="display:none" accept=".json" @change="importSessions">
                  </div>

                  <!-- Worlds -->
                  <div class="api-config-card" style="flex-direction:row;align-items:center;justify-content:space-between">
                    <div><div style="font-size:var(--text-sm);font-weight:700">导出所有世界数据</div><div style="font-size:var(--text-xs);color:var(--grey);margin-top:2px">将所有世界设定导出为 JSON 文件</div></div>
                    <button class="btn btn-ghost btn-md" @click="exportWorlds"><i class="fas fa-file-export"></i> 导出</button>
                  </div>
                  <div class="api-config-card" style="flex-direction:row;align-items:center;justify-content:space-between">
                    <div><div style="font-size:var(--text-sm);font-weight:700">导入单个/多个世界数据</div><div style="font-size:var(--text-xs);color:var(--grey);margin-top:2px">从 JSON 文件导入世界设定，每条作为新记录导入</div></div>
                    <button class="btn btn-ghost btn-md" @click="$refs.importWorldsInput.click()"><i class="fas fa-file-import"></i> 导入</button>
                    <input type="file" ref="importWorldsInput" style="display:none" accept=".json" @change="importWorlds">
                  </div>

                  <!-- Characters -->
                  <div class="api-config-card" style="flex-direction:row;align-items:center;justify-content:space-between">
                    <div><div style="font-size:var(--text-sm);font-weight:700">导出所有角色数据</div><div style="font-size:var(--text-xs);color:var(--grey);margin-top:2px">将所有角色设定导出为 JSON 文件</div></div>
                    <button class="btn btn-ghost btn-md" @click="exportChars"><i class="fas fa-file-export"></i> 导出</button>
                  </div>
                  <div class="api-config-card" style="flex-direction:row;align-items:center;justify-content:space-between">
                    <div><div style="font-size:var(--text-sm);font-weight:700">导入单个/多个角色数据</div><div style="font-size:var(--text-xs);color:var(--grey);margin-top:2px">从 JSON 文件导入角色设定，每条作为新记录导入</div></div>
                    <button class="btn btn-ghost btn-md" @click="$refs.importCharsInput.click()"><i class="fas fa-file-import"></i> 导入</button>
                    <input type="file" ref="importCharsInput" style="display:none" accept=".json" @change="importChars">
                  </div>

                </div>
              </template>

              <template v-if="settingsTab==='admin'">
                <div class="s-title">超管面板</div>
                <div class="s-sub">邀请码管理，仅超级管理员可见。</div>

                <div style="display:flex; align-items:center; gap:12px; margin-bottom:20px;">
                  <button class="btn btn-primary btn-md" @click="generateInvite">
                    <i class="fas fa-plus"></i> 生成新邀请码
                  </button>
                  <div v-if="lastGeneratedCode" style="display:flex; align-items:center; gap:8px; background:rgba(125,57,235,0.12); border:1.5px solid var(--purple-lt); border-radius:8px; padding:6px 14px;">
                    <span style="font-size:var(--text-sm); font-weight:700; letter-spacing:2px; color:var(--purple-lt);">{{ lastGeneratedCode }}</span>
                    <div class="icon-btn" style="width:24px;height:24px;font-size:var(--text-xs);" @click="copyInviteCode(lastGeneratedCode)" title="复制">
                      <i :class="copiedInviteCode === lastGeneratedCode ? 'fas fa-check' : 'fas fa-copy'" :style="copiedInviteCode === lastGeneratedCode ? 'color:var(--green)' : ''"></i>
                    </div>
                  </div>
                </div>

                <div style="display:flex; flex-direction:column; gap:6px;">
                  <div v-if="inviteList.length === 0" style="color:var(--grey); font-size:var(--text-sm); padding:12px 0;">
                    暂无邀请码记录
                  </div>
                  <div
                    v-for="item in inviteList" :key="item.code"
                    style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border-radius:8px; background:var(--ink-muted);"
                    :style="{ opacity: item.is_used ? 0.45 : 1 }"
                  >
                    <div style="display:flex; align-items:center; gap:12px;">
                      <span style="font-size:var(--text-sm); font-weight:700; letter-spacing:2px; color:var(--white-soft);">{{ item.code }}</span>
                      <span v-if="item.is_used" style="font-size:var(--text-xs); color:var(--grey); background:rgba(255,255,255,0.06); padding:2px 8px; border-radius:4px;">已使用</span>
                      <span v-else style="font-size:var(--text-xs); color:var(--green); background:rgba(191,247,41,0.08); padding:2px 8px; border-radius:4px;">未使用</span>
                    </div>
                    <div v-if="!item.is_used" class="icon-btn" style="width:24px;height:24px;font-size:var(--text-xs);" @click="copyInviteCode(item.code)" title="复制">
                      <i :class="copiedInviteCode === item.code ? 'fas fa-check' : 'fas fa-copy'" :style="copiedInviteCode === item.code ? 'color:var(--green)' : ''"></i>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- CHAT STATE -->
      <template v-if="currentView==='chat'">
        <div class="welcome-view" v-if="isWelcome">
          <div class="welcome-greeting">
            <h1>请坐 我的朋友 😃</h1>
            <h2>有什么我能帮上忙的？👇</h2>
          </div>
          
          <div class="input-inner">
            <textarea class="main-input" placeholder="想聊点什么？  Enter 发送消息，Shift + Enter 换行" v-model="inputText" @keydown.enter.exact.prevent="sendFromWelcome" @input="autoResize($event)" rows="1"></textarea>
            <div class="input-tools">
              <div class="tools-left">
              </div>
              <div class="tools-right" style="position: relative;">
                <div class="tool-btn-text" @click.stop="showProfileMenu=!showProfileMenu; showToolsMenu=false; showCharDrawer=false; showEngineParams=false">
                  {{ activeProfile?.name || 'API' }} <i class="fas fa-chevron-down" style="font-size:var(--text-xs)"></i>
                </div>

                <transition name="menu-pop">
                  <div class="tools-menu profile-menu" v-if="showProfileMenu" @click.stop style="bottom: 100%; right: 0; margin-bottom: 8px;">
                    <div 
                      v-for="p in profiles" :key="p.id" 
                      class="menu-item" 
                      :class="{active: activeProfileId === p.id}"
                      @click="activeProfileId = p.id; showProfileMenu = false"
                    >
                      <div class="menu-item-label" style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
                        <span>{{ p.name }}</span>
                        <i v-if="activeProfileId === p.id" class="fas fa-check" style="font-size: var(--text-xs); color: var(--purple-lt);"></i>
                      </div>
                    </div>
                    <div v-if="profiles.length === 0" class="menu-item" style="opacity: 0.5;">
                      <div class="menu-item-label">暂无可用节点</div>
                    </div>
                  </div>
                </transition>

                <div class="tool-btn"><i class="fas fa-microphone"></i></div>
                <button class="send-btn-gemini" @click="isStreaming ? stopStreaming() : sendFromWelcome()" :disabled="!inputText.trim() && !isStreaming" :style="isStreaming ? 'background:var(--danger)' : ''">
                  <i :class="isStreaming ? 'fas fa-stop' : 'fas fa-arrow-up'"></i>
                </button>
              </div>
            </div>
          </div>

          <div class="welcome-suggestions">
            <div class="suggest-pill" @click="inputText='开启新的冒险'; sendFromWelcome()"><i class="fas fa-dice-d20" style="color:var(--purple-lt)"></i> 开启新的冒险</div>
            <div class="suggest-pill" @click="inputText='继续上次剧情'; sendFromWelcome()"><i class="fas fa-history" style="color:var(--green)"></i> 继续上次剧情</div>
            <div class="suggest-pill" @click="inputText='探索热门世界'; sendFromWelcome()">探索热门世界</div>
            <div class="suggest-pill" @click="inputText='创建我的角色'; sendFromWelcome()">创建我的角色</div>
            <div class="suggest-pill" @click="inputText='构思跑团剧本'; sendFromWelcome()">构思跑团剧本</div>
            <div class="suggest-pill" @click="inputText='设定魔法体系'; sendFromWelcome()">设定魔法体系</div>
          </div>
        </div>

        <div class="chat-area" :class="currentMode" ref="chatAreaEl" @scroll="onChatScroll" v-else>
          <div class="chat-inner">
            <div
              v-for="msg in currentMessages" :key="msg.id"
              class="msg-group" :class="msg.role"
              v-show="!msg.hidden"
            >
              <!-- Bubble -->
              <div class="bubble" :class="msg.role">
                <template v-if="msg.role==='ai' && currentMode==='rpg'">
                  <details class="debug-box" v-if="msg.role === 'ai'">
                    <summary><i class="fas fa-bug" style="font-size:var(--text-xs)"></i> 调试 Prompt</summary>
                    <div class="debug-content">
                      <div v-if="msg.usage" class="inner-stats" style="padding-bottom: 8px; margin-bottom: 8px; border-bottom: 1px solid rgba(255,165,0,0.15); display: flex; flex-wrap: wrap; gap: 10px; font-size: var(--text-xs);">
                        <span><i class="fas fa-arrow-up"></i> 你的字数: {{msg.usage.user_words}}</span>
                        <span><i class="fas fa-database"></i> 上下文消耗: {{msg.usage.prompt_tokens}}</span>
                        <span><i class="fas fa-arrow-down"></i> 回复字数: {{msg.usage.ai_words}}</span>
                        <span><i class="fas fa-coins"></i> 回复消耗: {{msg.usage.completion_tokens}}</span>
                      </div>
                      <div v-if="msg.debug">{{msg.debug}}</div>
                    </div>
                  </details>
                  <details class="cot-box" v-if="msg.cot">
                    <summary><i class="fas fa-brain" style="font-size:var(--text-xs)"></i> 推理过程</summary>
                    <div class="cot-content">{{msg.cot}}</div>
                  </details>
                </template>
                <div v-html="msg.content"></div>
              </div>

              <!-- Action buttons -->
              <div class="msg-actions">
                <template v-if="msg.role==='user'">
                  <div class="action-btn" @click="editUserMsg(msg)"><i class="fas fa-pen" style="font-size:var(--text-xs)"></i> 编辑</div>
                                    <div class="action-btn" @click="copyMsg(msg)" style="min-width:52px;justify-content:center">
                    <template v-if="copiedMsgId === msg.id">
                      <i class="fas fa-check" style="font-size:var(--text-xs);color:var(--green)"></i> 已复制
                    </template>
                    <template v-else>
                      <i class="fas fa-copy" style="font-size:var(--text-xs)"></i> 复制
                    </template>
                  </div>
                  <div class="action-btn danger" @click="deleteMsg(msg)"><i class="fas fa-trash" style="font-size:var(--text-xs)"></i> 删除</div>
                </template>
                <template v-else>
                  <div class="action-btn regen" @click="regenMsg(msg)"><i class="fas fa-sync-alt" style="font-size:var(--text-xs)"></i> 重新生成</div>
                                    <div class="action-btn" @click="copyMsg(msg)" style="min-width:52px;justify-content:center">
                    <template v-if="copiedMsgId === msg.id">
                      <i class="fas fa-check" style="font-size:var(--text-xs);color:var(--green)"></i> 已复制
                    </template>
                    <template v-else>
                      <i class="fas fa-copy" style="font-size:var(--text-xs)"></i> 复制
                    </template>
                  </div>
                  <div class="action-btn danger" @click="deleteMsg(msg)"><i class="fas fa-trash" style="font-size:var(--text-xs)"></i> 删除</div>
                </template>
              </div>
            </div>
          </div>
        </div>

        <div class="input-bar" v-if="!isWelcome">
          <div class="input-inner">
            <div class="drawer-overlay" v-if="showCharDrawer" @click="showCharDrawer=false"></div>
            
            <transition name="drawer">
              <div class="char-drawer" v-if="showCharDrawer" @click.stop>
                <div class="drawer-grid">
                  <div class="drawer-stats">
                    <div class="drawer-inv-header">状态面板</div>
                    <div class="char-header-sb" style="background:transparent; border:none; padding:0; margin-bottom:12px;">
                      <div class="char-avatar-sb"><i class="fas fa-user-ninja"></i></div>
                      <div>
                        <div class="char-name-sb">银翼·克劳德</div>
                        <div class="char-role-sb">流亡骑士 · Lv.12</div>
                      </div>
                    </div>
                    <div v-for="s in charStats" :key="s.name" class="stat-row">
                      <div class="stat-label">{{s.name}}</div>
                      <div class="stat-bar"><div class="stat-bar-fill" :style="{width:s.val+'%',background:s.color}"></div></div>
                      <div class="stat-val">{{s.val}}</div>
                    </div>
                  </div>
                  <div class="drawer-inventory">
                    <div class="drawer-inv-header">随身背包</div>
                    <div class="drawer-inv-grid">
                      <div v-for="item in inventory" :key="item.id" class="inv-item" :class="{'has-item':item.emoji}" :title="item.name" style="height:54px;">
                        <span>{{item.emoji}}</span>
                        <div class="inv-count" v-if="item.count">{{item.count}}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </transition>
            <div class="action-list-container" v-if="currentMode==='rpg' && actionChips.length > 0">
              <transition name="menu-pop">
                <div class="action-vertical-list" v-if="showActionList">
                  <div 
                    v-for="(chip, index) in actionChips" 
                    :key="chip" 
                    class="action-vertical-item"
                    @click="inputText=chip; sendMessage(); showActionList=false"
                  >
                    {{ index + 1 }}. {{ chip }}
                  </div>
                </div>
              </transition>
              
              <div class="action-list-btn" @click.stop="showActionList=!showActionList; showToolsMenu=false; showCharDrawer=false">
                <i class="fas fa-lightbulb"></i> 推荐行动
              </div>
            </div>

            <button class="send-btn-gemini" v-show="showScrollBottom && !isWelcome" @click="scrollToBottom(true)" style="position: absolute; top: -48px; left: 50%; transform: translateX(-50%); background: rgba(255, 255, 255, 0.3) !important; box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); z-index: 10;">
              <i class="fas fa-arrow-down"></i>
            </button>

            <textarea class="main-input" :placeholder="currentMode==='rpg'?'描述你的行动...  Enter 发送 ,  Shift + Enter 换行':'输入内容...  Enter 发送 ,  Shift + Enter 换行'" v-model="inputText" ref="mainInputEl" @keydown.enter.exact.prevent="sendMessage" @input="autoResize($event)" rows="1"></textarea>
            <div class="input-tools">
              <div class="tools-left" style="position: relative;">
                <div class="tool-btn-text" @click.stop="showToolsMenu=!showToolsMenu; showProfileMenu=false; showCharDrawer=false; showActionList=false; showEngineParams=false" :style="{color: showToolsMenu ? 'var(--purple-lt)' : ''}">
                  <i class="fas fa-bars"></i> 功能
                </div>

                <transition name="menu-pop">
                  <div class="tools-menu" v-if="showToolsMenu" @click.stop>
                    <div class="menu-item" v-if="hasRole(['superadmin', 'admin'])">
                      <div class="menu-item-label">开发者调试</div>
                      <label class="toggle" style="transform: scale(0.8);">
                        <input type="checkbox" v-model="showDebug"/>
                        <div class="toggle-track"></div><div class="toggle-thumb"></div>
                      </label>
                    </div>
                    <div class="menu-item">
                      <div class="menu-item-label">流式输出</div>
                      <label class="toggle" style="transform: scale(0.8);">
                        <input type="checkbox" v-model="streamingEnabled"/>
                        <div class="toggle-track"></div><div class="toggle-thumb"></div>
                      </label>
                    </div>
                    <div class="menu-item">
                      <div class="menu-item-label">CoT (思维链)</div>
                      <label class="toggle" style="transform: scale(0.8);">
                        <input type="checkbox" v-model="showCoT"/>
                        <div class="toggle-track"></div><div class="toggle-thumb"></div>
                      </label>
                    </div>
                  </div>
                </transition>

                <div class="tool-btn-text" @click.stop="showEngineParams=true; showToolsMenu=false; showProfileMenu=false; showCharDrawer=false; showActionList=false">
                  <i class="fas fa-sliders-h"></i> 调节
                </div>

                <div class="tool-btn-text" v-if="currentMode==='rpg'" @click.stop="showCharDrawer=!showCharDrawer; showToolsMenu=false; showActionList=false; showEngineParams=false; showProfileMenu=false" :style="{color: showCharDrawer ? 'var(--purple-lt)' : ''}">
                  <i class="fas fa-user-shield"></i> 角色与背包
                </div>

                <div class="modal-overlay" v-if="showEngineParams" @click.stop="showEngineParams=false" style="z-index: 300;">
                  <div class="modal-box large" @click.stop>
                    <div class="modal-header">
                      <div class="modal-title"><i class="fas fa-dice-d20" style="color:var(--purple-lt)"></i> 引擎高级参数</div>
                      <div class="icon-btn" @click="showEngineParams=false"><i class="fas fa-times"></i></div>
                    </div>
                    
                    <div class="modal-body" style="padding: 12px 24px;">

                      <!-- Context Limit -->
                      <div class="param-card">
                        <div class="param-header">
                          <div class="param-info"><i class="fas fa-history" style="color:var(--purple-lt)"></i> 携带历史记忆长度 (Context Limit)</div>
                        </div>
                        <div class="param-control-wrap">
                          <div class="param-floating-value" :style="{ left: ((advParams.contextLimit - 1) / (50 - 1) * 100) + '%' }">
                            {{advParams.contextLimit}}
                          </div>
                          <input type="range" class="custom-slider" v-model="advParams.contextLimit" min="1" max="50">
                        </div>
                        <div class="param-desc-box">
                          <div class="p-text"><strong>作用:</strong> 严格限制每次 API 请求时，发送给大模型的对话条数（你发1句+AI回1句=2条）。</div>
                          <div class="p-text"><strong>原理:</strong> 得益于本程序的“前端状态面板”架构，即便只传最近 2-6 条对话，AI 依然能通过读取面板来保持世界观和人设不崩塌。</div>
                          <div class="p-text"><strong>建议:</strong> 日常跑团推荐设为 <strong>4 ~ 6</strong>。设置过高会导致 Token 消耗成倍暴涨。</div>
                        </div>
                      </div>

                      <!-- STM Threshold -->
                      <div class="param-card">
                        <div class="param-header">
                          <div class="param-info"><i class="fas fa-brain" style="color:var(--danger)"></i> 短期记忆 (STM) 归纳阈值</div>
                        </div>
                        <div class="param-control-wrap">
                          <div class="param-floating-value" :style="{ left: ((advParams.stmThreshold - 1) / (20 - 1) * 100) + '%' }">
                            {{advParams.stmThreshold}}
                          </div>
                          <input type="range" class="custom-slider" v-model="advParams.stmThreshold" min="1" max="20">
                        </div>
                        <div class="param-desc-box">
                          <div class="p-text"><strong>作用:</strong> 决定 AI 面板中“短期记忆”最多能容纳几条。超过此数值时，AI 会强制触发记忆压缩，将老旧的 STM 概括并移入 LTM 表中！</div>
                          <div class="p-text"><strong>建议:</strong> 默认推荐 <strong>6</strong>。太低会导致 AI 频繁压缩记忆浪费算力，太高会导致短期记忆面板过长引起遗忘。</div>
                        </div>
                      </div>

                      <!-- RPG Temp -->
                      <div class="param-card">
                        <div class="param-header">
                          <div class="param-info"><i class="fas fa-fire" style="color:var(--warn)"></i> RPG 创造力 (Temperature)</div>
                        </div>
                        <div class="param-control-wrap">
                          <div class="param-floating-value" :style="{ left: (advParams.rpgTemp / 2 * 100) + '%' }">
                            {{advParams.rpgTemp}}
                          </div>
                          <input type="range" class="custom-slider" v-model="advParams.rpgTemp" min="0" max="2" step="0.1">
                        </div>
                        <div class="param-desc-box">
                          <div class="p-text"><strong>作用:</strong> 决定大模型在“RPG跑团模式”下生成文本的随机性、发散程度与词汇华丽度。</div>
                          <div class="p-text"><strong>建议:</strong> 对于小说/跑团推演，推荐设为 <strong>0.8 ~ 1.0</strong> 之间。过高(>1.2)易发散幻觉，过低(<0.5)回复如机械般死板。</div>
                        </div>
                      </div>

                      <!-- Chat Temp -->
                      <div class="param-card">
                        <div class="param-header">
                          <div class="param-info"><i class="fas fa-comment-dots" style="color:var(--green)"></i> 日常聊天严谨度 (Temperature)</div>
                        </div>
                        <div class="param-control-wrap">
                          <div class="param-floating-value" :style="{ left: (advParams.chatTemp / 1 * 100) + '%' }">
                            {{advParams.chatTemp}}
                          </div>
                          <input type="range" class="custom-slider" v-model="advParams.chatTemp" min="0" max="1" step="0.1">
                        </div>
                        <div class="param-desc-box">
                          <div class="p-text"><strong>作用:</strong> 决定左侧蓝色“普通对话模式”下的随机性。</div>
                          <div class="p-text"><strong>建议:</strong> 日常问答、写代码或查资料，需要逻辑严密，推荐设为 <strong>0.5 ~ 0.6</strong>。</div>
                        </div>
                      </div>

                    </div>


                    <div class="modal-footer" style="gap: 12px;">
                      <button class="btn btn-ghost btn-md" style="flex: 1; justify-content: center;" @click="resetAdvParams">恢复默认</button>
                      <button class="btn btn-primary btn-md" style="flex: 2; justify-content: center; border-radius: 99px;" @click="showEngineParams=false">完成设定</button>
                    </div>
                  </div>
                </div>
              </div>
              <div class="tools-right" style="position: relative;">
                <div class="tool-btn-text" @click.stop="showProfileMenu=!showProfileMenu; showToolsMenu=false; showCharDrawer=false; showEngineParams=false">
                  {{ activeProfile?.name || 'API' }} <i class="fas fa-chevron-down" style="font-size:var(--text-xs)"></i>
                </div>

                <transition name="menu-pop">
                  <div class="tools-menu profile-menu" v-if="showProfileMenu" @click.stop style="bottom: 100%; right: 0; margin-bottom: 8px;">
                    <div 
                      v-for="p in profiles" :key="p.id" 
                      class="menu-item" 
                      :class="{active: activeProfileId === p.id}"
                      @click="activeProfileId = p.id; showProfileMenu = false"
                    >
                      <div class="menu-item-label" style="display: flex; align-items: center; justify-content: space-between; width: 100%;">
                        <span>{{ p.name }}</span>
                        <i v-if="activeProfileId === p.id" class="fas fa-check" style="font-size: var(--text-xs); color: var(--purple-lt);"></i>
                      </div>
                    </div>
                    <div v-if="profiles.length === 0" class="menu-item" style="opacity: 0.5;">
                      <div class="menu-item-label">暂无可用节点</div>
                    </div>
                  </div>
                </transition>

                <div class="tool-btn"><i class="fas fa-microphone"></i></div>
                <button class="send-btn-gemini" @click="isStreaming ? stopStreaming() : sendMessage()" :disabled="!inputText.trim() && !isStreaming" :style="isStreaming ? 'background:var(--danger)' : ''">
                  <i :class="isStreaming ? 'fas fa-stop' : 'fas fa-arrow-up'"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>

  <div class="modal-overlay" v-if="showConfirm" @click.self="showConfirm=false">
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title">确认删除</div>
        <div class="icon-btn" @click="showConfirm=false"><i class="fas fa-times"></i></div>
      </div>
      <div class="modal-body" style="text-align: center; padding-top: 32px;">
        <div style="font-size: 36px; margin-bottom: 12px;">🗑️</div>
        <div style="font-size: var(--text-md); color: var(--white-soft);">确定要删除 <strong>「{{confirmTarget?.name}}」</strong> 吗？<br>此操作不可撤销。</div>
      </div>
      <div class="modal-footer" style="justify-content: center; gap: 16px;">
        <button class="btn btn-ghost btn-md" style="flex: 1; justify-content: center;" @click="showConfirm=false">取消</button>
        <button class="btn btn-danger btn-md" style="flex: 1; justify-content: center;" @click="confirmDeleteExec"><i class="fas fa-trash"></i> 确认删除</button>
      </div>
    </div>
  </div>

  <div class="modal-overlay" v-if="showNewProfileModal" @click.self="closeNewProfileModal()">
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title">新建节点</div>
        <div class="icon-btn" @click="closeNewProfileModal()"><i class="fas fa-times"></i></div>
      </div>
      <div class="modal-body">
        <div class="form-field full">
          <div class="form-label">名称</div>
          <input class="form-input" v-model="newProfileForm.name" autocomplete="off" placeholder="我的节点"/>
        </div>
        <div class="form-field full">
          <div class="form-label">Base URL</div>
          <input class="form-input" v-model="newProfileForm.baseUrl" autocomplete="off" placeholder="https://api.openai.com/v1"/>
        </div>
        <div class="form-field full">
          <div class="form-label">API Key</div>
          <input class="form-input" v-model="newProfileForm.apiKey" type="text" autocomplete="off" readonly @focus="(e) => e.target.removeAttribute('readonly')" placeholder="sk-..."/>
        </div>
        <div class="form-field full">
          <div class="form-label">Model Name</div>
          <input class="form-input" v-model="newProfileForm.model" autocomplete="off" placeholder="例如：gpt-4o"/>
        </div>
        <div style="height: 1px; background: rgba(255,255,255,0.08); margin: 16px 0;"></div>
        <div style="font-size:var(--text-xs); color:var(--grey); font-weight:700;">一键粘贴配置（名称,URL,Key,模型）</div>
        <div style="display:flex; gap:8px;">
          <textarea class="form-textarea" v-model="quickAddText" style="flex:1; min-height:80px; font-family:var(--font-mono); font-size:var(--text-xs);" placeholder="一行一条，可粘贴多行&#10;格式：Name,https://...,sk-...,gpt-4"></textarea>
          <button class="btn btn-primary btn-md" style="width:60px; justify-content:center; align-self:flex-end;" @click="quickAddProfiles">添加</button>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost btn-md" @click="closeNewProfileModal()">取消</button>
        <button class="btn btn-primary btn-md" @click="saveNewProfile">保存节点</button>
      </div>
    </div>
  </div>

  <div class="modal-overlay" v-if="editingProfileId" @click.self="editingProfileId=null">
    <div class="modal-box">
      <div class="modal-header">
        <div class="modal-title">编辑节点</div>
        <div class="icon-btn" @click="editingProfileId=null"><i class="fas fa-times"></i></div>
      </div>
      <div class="modal-body">
        <div class="form-field full">
          <div class="form-label">名称</div>
          <input class="form-input" v-model="tempEditForm.name" autocomplete="off"/>
        </div>
        <div class="form-field full">
          <div class="form-label">Base URL</div>
          <input class="form-input" v-model="tempEditForm.baseUrl" autocomplete="off"/>
        </div>
        <div class="form-field full">
          <div class="form-label">API Key</div>
          <input class="form-input" v-model="tempEditForm.apiKey" type="text" autocomplete="off" readonly @focus="(e) => e.target.removeAttribute('readonly')" placeholder="sk-..."/>
        </div>
        <div class="form-field full">
          <div class="form-label">Model Name</div>
          <input class="form-input" v-model="tempEditForm.model" autocomplete="off"/>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost btn-md" @click="editingProfileId=null">取消</button>
        <button class="btn btn-primary btn-md" @click="saveApiConfig">保存修改</button>
      </div>
    </div>
  </div>

</div>
</template>

<script>
import { ref, reactive, computed, nextTick, watch, onMounted } from 'vue'
import Sortable from 'sortablejs'
import { marked } from 'marked'

export default {
  setup() {

    // ── 全局状态变量 (预先定义，防止 ReferenceError) ──
    const streamingEnabled = ref(true); 
    const DEFAULT_ADV_PARAMS = {
      contextLimit: 10,
      stmThreshold: 6,
      rpgTemp: 0.8,
      chatTemp: 0.6
    };
    const advParams = reactive({ ...DEFAULT_ADV_PARAMS });
    
    const resetAdvParams = () => {
      if (confirm('确定要将所有引擎参数恢复至初始状态吗？')) {
        Object.assign(advParams, DEFAULT_ADV_PARAMS);
      }
    };
    const actionChips = ref([]); 
    const showActionList = ref(false); 
    const systemPrompts = ref([]); 
    const copiedMsgId = ref(null);
    // ── Auth ──
    const loggedIn  = ref(false);
    const showCoT          = ref(false);
    const showDebug        = ref(false);
    const isLoginMode = ref(true);
    const loginUser = ref('');
    const loginPass = ref('');
    const loginPassConfirm = ref(''); // [新增] 注册确认密码
    const showPass = ref(false); // [新增] 密码显示开关
    const showPassConfirm = ref(false); // [新增] 确认密码显示开关
    const inviteCode = ref('');
    // 真实用户状态
    const currentUser = ref({ id: '', name: '未登录', role: 'user' });
    const hasRole = (roles) => roles.includes(currentUser.value.role); // [RBAC] 补全全局权限判断函数
    let nextId = Date.now(); // [新增] 定义全局自增 ID 起点

    // 页面初始化：读取本地存储恢复登录状态与偏好设置
    onMounted(() => {
      const token = localStorage.getItem('wf_token');
      const userStr = localStorage.getItem('wf_user');
      if (token && userStr) {
        try {
          const userObj = JSON.parse(userStr);
          currentUser.value = { id: userObj.id, name: userObj.username, role: userObj.role };
          loggedIn.value = true;
        } catch (e) {
          localStorage.removeItem('wf_token');
          localStorage.removeItem('wf_user');
        }
      }
      
      // [新增] 恢复功能开关与调节项偏好
      const storedStreaming = localStorage.getItem('wf_streaming');
      if (storedStreaming !== null) streamingEnabled.value = (storedStreaming === 'true');
      
      const storedDebug = localStorage.getItem('wf_show_debug');
      if (storedDebug !== null) showDebug.value = (storedDebug === 'true');
      
      const storedCoT = localStorage.getItem('wf_show_cot');
      if (storedCoT !== null) showCoT.value = (storedCoT === 'true');

      const storedParams = localStorage.getItem('wf_adv_params');
      if (storedParams) {
        try {
          const p = JSON.parse(storedParams);
          Object.assign(advParams, p);
        } catch(e) {}
      }
    });

    // [新增] 监听并保存偏好设置
    watch(streamingEnabled, (val) => localStorage.setItem('wf_streaming', val));
    watch(showDebug, (val) => localStorage.setItem('wf_show_debug', val));
    watch(showCoT, (val) => localStorage.setItem('wf_show_cot', val));
    watch(advParams, (val) => localStorage.setItem('wf_adv_params', JSON.stringify(val)), { deep: true });

    const formatDate = (ts) => {
      if (!ts) return '';
      const d = new Date(ts);
      const M = d.getMonth() + 1;
      const D = d.getDate();
      const h = d.getHours().toString().padStart(2, '0');
      const m = d.getMinutes().toString().padStart(2, '0');
      return `${M}/${D} ${h}:${m}`;
    };

    async function doLogin() {
      if (!loginUser.value.trim() || !loginPass.value.trim()) {
        alert('请输入用户名和密码');
        return;
      }
      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: loginUser.value.trim(), password: loginPass.value })
        });
        const data = await res.json();
        if (!res.ok) {
          alert('登录失败: ' + (data.detail || '未知错误'));
          return;
        }
        // 保存 Token 和用户信息
        localStorage.setItem('wf_token', data.access_token);
        localStorage.setItem('wf_user', JSON.stringify(data.user));
        currentUser.value = { id: data.user.id, name: data.user.username, role: data.user.role };
        loggedIn.value = true;
      } catch (e) {
        alert('网络错误，无法连接到服务器');
      }
    }

    async function doRegister() {
      if (!loginUser.value.trim() || !loginPass.value.trim()) {
        alert('请输入用户名和密码');
        return;
      }
      if (loginPass.value !== loginPassConfirm.value) {
        alert('两次输入的密码不一致，请重新检查');
        return;
      }
      try {
        const res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            username: loginUser.value.trim(), 
            password: loginPass.value,
            invite_code: inviteCode.value.trim() || null 
          })
        });
        const data = await res.json();
        if (!res.ok) {
          alert('注册失败: ' + (data.detail || '未知错误'));
          return;
        }
        alert('注册成功，正在为您自动登录...');
        await doLogin(); 
      } catch (e) {
        alert('网络错误，无法连接到服务器');
      }
    }

    function doLogout(force = false) {
      if (force || confirm('确定要退出登录吗？')) {
        // 1. 清除本地持久化凭证
        localStorage.removeItem('wf_token');
        localStorage.removeItem('wf_user');
        
        // 2. 物理重置：强制刷新页面，彻底销毁 Vue 实例与所有内存状态
        // 重新加载后，App.vue 的 onMounted 会发现没有 Token，从而干净利落地渲染登录页
        window.location.reload();
      }
    }

    // ── API Wrapper (智能信使：统一处理 Token 与 401 拦截) ──
    let isHandling401 = false; // [防抖锁] 防止并发请求弹出多个警告

    async function apiFetch(url, options = {}) {
      const token = localStorage.getItem('wf_token');
      const headers = {
        'Content-Type': 'application/json',
        ...options.headers
      };
      
      // 如果本地有 Token，自动夹在请求头里
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      
      try {
        const response = await fetch(url, { ...options, headers });
        
        // 如果后端返回 401，说明 Token 过期或伪造，直接强制踢回登录页
        if (response.status === 401) {
          if (!isHandling401) {
            isHandling401 = true;
            alert('登录身份已过期，请重新登录。');
            doLogout(true); // 传入 true 代表强制登出，不弹窗询问
            setTimeout(() => { isHandling401 = false; }, 2000); // 2秒后解锁，防止无限锁死
          }
          throw new Error('Unauthorized');
        }
        
        return response;
      } catch (error) {
        console.error('API 请求异常:', error);
        throw error;
      }
    }

    // ── Layout ──
    const currentView      = ref('discover');
    const sidebarCollapsed = ref(false);
    const charPanelOpen    = ref(true);
    const sessionsOpen     = ref(true);
    const showConfirm      = ref(false);
    const confirmTarget    = ref(null);
    const confirmCb        = ref(null);
    const settingsTab      = ref('basic');
    const openDropdown     = ref(null);
    const showCharDrawer   = ref(false);
    const showToolsMenu    = ref(false);
    const showProfileMenu  = ref(false);
    const showEngineParams = ref(false); 


    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        showCharDrawer.value   = false;
        showToolsMenu.value    = false;
        showProfileMenu.value  = false;
        showEngineParams.value = false;
      }
    });

    function closeAllDropdowns() { openDropdown.value = null; }
    function toggleDropdown(id) {
      if (openDropdown.value === id) {
        openDropdown.value = null;
      } else {
        openDropdown.value = id;
        // 开启会话选项时，强制关闭调节按钮菜单和角色抽屉
        showToolsMenu.value = false;
        showCharDrawer.value = false;
        showActionList.value = false;
      }
    }

    async function confirmDeleteExec() {
      if (confirmCb.value) await confirmCb.value();
      showConfirm.value = false;
      confirmTarget.value = null;
      confirmCb.value = null;
    }

    const confirmDelete = (item, type) => {
      confirmTarget.value = item;
      confirmCb.value = async () => {
        const endpoint = type === 'world' ? `/api/worlds/${item.id}` : (type === 'char' ? `/api/characters/${item.id}` : `/api/prompts/${item.id}`);
        try {
          await apiFetch(endpoint, { method: 'DELETE' });
          if (type === 'engine') {
            systemPrompts.value = systemPrompts.value.filter(x => x.id !== item.id);
          } else if (type === 'world') {
            worlds.value = worlds.value.filter(x => x.id !== item.id);
          } else if (type === 'char') {
            characters.value = characters.value.filter(x => x.id !== item.id);
          }
        } catch (e) {
          alert('删除失败，可能是权限不足或网络异常。');
        }
      };
      showConfirm.value = true;
    };

    const settingsNav = computed(() => {
      const items = [
        { key:'basic',     icon:'fas fa-sliders-h',   label:'基础设置', desc:'应用名称和界面选项' },
        { key:'api',       icon:'fas fa-server',       label:'API 设置', desc:'模型与密钥配置' },
        { key:'data',      icon:'fas fa-database',     label:'数据管理', desc:'导入、导出、重置' },
      ];
      if (currentUser.value.role === 'superadmin') {
        items.push({ key:'admin', icon:'fas fa-crown', label:'超管面板', desc:'邀请码管理' });
      }
      return items;
    });

    // ── Sessions (打通后端) ──
    const sessionsData = reactive({});
    const sessions = computed(() => {
      return Object.values(sessionsData).sort((a, b) => {
        // 1. 优先按置顶状态降序 (1 为置顶，0 为普通)
        if ((b.is_pinned || 0) !== (a.is_pinned || 0)) {
          return (b.is_pinned || 0) - (a.is_pinned || 0);
        }
        // 2. 其次按更新时间降序
        return (b.updatedAt || 0) - (a.updatedAt || 0);
      });
    });
    const currentSessionId = ref(null);

    async function loadSessions() {
      try {
        const res = await apiFetch('/api/sessions');
        const data = await res.json();
        // 转换为响应式字典
        Object.keys(sessionsData).forEach(key => delete sessionsData[key]);
        data.forEach(s => {
          // [适配] 将后端 type 映射为前端 mode，确保会话颜色和逻辑正确区分
          sessionsData[s.id] = { ...s, mode: s.type, name: s.title || '未命名会话' };
        });
      } catch (e) { console.error('加载会话失败'); }
    }

    // 同步保存会话到后端
    async function syncSession(id) {
      const s = sessionsData[id];
      if (!s) return;
      try {
        await apiFetch('/api/sessions', {
          method: 'POST',
          body: JSON.stringify({
            id: s.id,
            type: s.mode,
            title: s.name,
            messages: s.messages,
            updatedAt: Date.now(),
            is_pinned: s.is_pinned || 0, // [修复] 补全置顶状态同步
            engine_id: s.engine_id || null,
            world_id: s.world_id || null,
            char_id: s.char_id || null
          })
        });
      } catch (e) { console.error('同步会话失败'); }
    } // null = welcome state

    const isWelcome = computed(() => currentSessionId.value === null);
    const activeSession = computed(() => currentSessionId.value ? sessionsData[currentSessionId.value] : null);
    const currentMode = computed(() => activeSession.value?.mode || 'chat');
    const currentMessages = computed(() => activeSession.value?.messages || []);

    // ── Mock Data: Discover Sections (发现页分类) ──
    const mockDeadCard = { name: '封印的领域', desc: '该世界暂未开放探索，数据迷雾笼罩于此...', author: 'System', plays: '---', icon: 'fas fa-lock', tag: '未解锁', isDead: true };
    const generateDeadCards = (count, startId) => Array.from({ length: count }).map((_, i) => ({ ...mockDeadCard, id: startId + i }));

    const mockNpcCard = { type: 'npc', name: '伊莎贝尔·克莱蒙特', desc: '传闻中精通失传魔药学的高阶巫师，隐居在幽暗森林深处，性格孤僻但学识渊博。她似乎在寻找某种能够逆转生死的禁忌素材。', author: '官方设定组', plays: '24.5k', icon: 'fas fa-user-ninja', isDead: true };
    const generateNpcCards = (count, startId) => Array.from({ length: count }).map((_, i) => ({ ...mockNpcCard, id: startId + i }));

    const discoverSections = ref([
      { 
        title: '从官方模板开始', 
        items: [
          { id: 101, name: '深渊神殿', desc: '黑暗奇幻风格，探索被诅咒的远古神殿。死亡即重置。', author: '官方', plays: '12k', icon: 'fas fa-dungeon', tag: 'RPG' },
          ...generateDeadCards(4, 102)
        ]
      },
      { title: '热门世界观', items: generateDeadCards(5, 301) },
      { title: '热门角色/NPC', items: generateNpcCards(5, 401) },
      { title: '热门模组', items: generateDeadCards(5, 501) }
    ]);
    const selectedCard = ref(null);

    // ── 横向拖拽与翻页逻辑 ──
    const rowRefs = ref({});
    const isDragging = ref(false);
    const startX = ref(0);
    const scrollLeftPos = ref(0);
    const activeDragRow = ref(null);

    const scrollRow = (index, offset) => {
      const el = rowRefs.value[index];
      if (el) el.scrollBy({ left: offset, behavior: 'smooth' });
    };

    const startDrag = (e, index) => {
      isDragging.value = true;
      activeDragRow.value = index;
      const el = rowRefs.value[index];
      startX.value = e.pageX - el.offsetLeft;
      scrollLeftPos.value = el.scrollLeft;
    };

    const stopDrag = () => {
      isDragging.value = false;
      activeDragRow.value = null;
    };

    const onDrag = (e, index) => {
      if (!isDragging.value || activeDragRow.value !== index) return;
      e.preventDefault();
      const el = rowRefs.value[index];
      const x = e.pageX - el.offsetLeft;
      const walk = (x - startX.value) * 1.5;
      el.scrollLeft = scrollLeftPos.value - walk;
    };

    const openDetail = (card) => {
      selectedCard.value = card;
      quickSetup.characterId = null; // 每次进入详情页重置角色选择
      currentView.value = 'card-detail';
    };

    // ── Mock Data: 角色与引擎 (开局所需) ──
    const engines = ref([
      { id: 1, name: 'Gemini 3.1 Pro (RPG 引擎)', model: 'gemini-3.1-pro' },
      { id: 2, name: 'Claude 3.5 Sonnet (文字推演)', model: 'claude-3-5-sonnet' }
    ]);

    // ── 真实资产库 (打通后端) ──
    const worlds = ref([]);
    const characters = ref([]);

    const rpgEngines = computed(() => {
      const filtered = systemPrompts.value.filter(p => p.type === 'rpg');
      return filtered.length > 0 ? filtered : systemPrompts.value; // 如果没有 RPG 类型的，显示全部作为兜底
    });

    // 统一资产拉取函数 (已修复变量重名问题)
    async function loadAssets() {
      if (!loggedIn.value) return;
      try {
        const [wRes, cRes, pRes, profRes] = await Promise.all([
          apiFetch('/api/worlds'),
          apiFetch('/api/characters'),
          apiFetch('/api/prompts'),
          apiFetch('/api/profiles')
        ]);

        // 1. 加载会话 (独立处理)
        await loadSessions();

        // 2. 加载世界与角色
        worlds.value = await wRes.json();
        characters.value = await cRes.json();
        profiles.value = await profRes.json();

        // 3. 加载并适配引擎预设
        const pRawData = await pRes.json();
        systemPrompts.value = pRawData.map(p => ({ 
          ...p, 
          desc: p.content, 
          active: false, 
          type: (p.name && p.name.includes('Chat')) ? 'chat' : 'rpg',
          isPublic: p.is_public === 1
        }));

        // 4. 恢复 API 节点选中状态与新建开局默认选中
        const userProfileKey = 'wf_active_profile_' + currentUser.value.id;
        const storedProfileId = activeProfileId.value || localStorage.getItem(userProfileKey);
        const profileExists = storedProfileId && profiles.value.find(p => p.id === storedProfileId);
        if (profileExists) {
          activeProfileId.value = storedProfileId;
        } else if (profiles.value.length > 0) {
          activeProfileId.value = profiles.value[0].id;
        }
        // [新增] 自动选中第一个资产，防止 ID 不匹配导致无法开局
        if (!setupForm.worldId && worlds.value.length > 0) setupForm.worldId = worlds.value[0].id;
        if (!setupForm.characterId && characters.value.length > 0) setupForm.characterId = characters.value[0].id;
        if (!setupForm.engineId && systemPrompts.value.filter(p => p.type === 'rpg').length > 0) {
          setupForm.engineId = systemPrompts.value.filter(p => p.type === 'rpg')[0].id;
        }
      } catch (e) {
        console.error('加载资产失败:', e);
      }
    }
    // 监听登录状态：一旦登录成功，立刻拉取数据
    watch(loggedIn, (newVal) => {
      if (newVal) loadAssets();
    }, { immediate: true });

    // ── 资产编辑状态与方法 ──
    const editingWorld = ref(null);
    const editingChar = ref(null);
    const originalEditData = ref(null);

    const editWorld = (w) => {
      editingWorld.value = w;
      originalEditData.value = JSON.stringify(w);
    };
    const editChar = (c) => {
      editingChar.value = c;
      originalEditData.value = JSON.stringify(c);
    };

    const saveEdit = async (type, andReturn = false) => {
      const data = type === 'world' ? editingWorld.value : (type === 'char' ? editingChar.value : editingEngine.value);
      const endpoint = type === 'world' ? '/api/worlds' : (type === 'char' ? '/api/characters' : '/api/prompts');
      
      const payload = { ...data };
      if (type === 'engine') {
        payload.content = payload.desc || '';
        payload.is_public = payload.isPublic ? 1 : 0;
      }
      
      try {
        await apiFetch(endpoint, {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        originalEditData.value = JSON.stringify(data);
        alert('✅ 保存并同步至云端成功！');
        await loadAssets(); // 保存后重新拉取
        
        if (andReturn) {
          if (type === 'world') editingWorld.value = null;
          else if (type === 'char') editingChar.value = null;
          else if (type === 'engine') editingEngine.value = null;
        }
      } catch (e) {
        alert('保存失败，请检查网络。');
      }
    };

    const exitEdit = (type) => {
      const currentData = type === 'world' ? editingWorld.value : (type === 'char' ? editingChar.value : editingEngine.value);
      if (JSON.stringify(currentData) !== originalEditData.value) {
        if (window.confirm('有更改尚未保存，是否退出？\n(注意：未保存的修改将被丢弃)')) {
          Object.assign(currentData, JSON.parse(originalEditData.value));
          if (type === 'world') editingWorld.value = null;
          else if (type === 'char') editingChar.value = null;
          else editingEngine.value = null;
        }
      } else {
        if (type === 'world') editingWorld.value = null;
        else if (type === 'char') editingChar.value = null;
        else editingEngine.value = null;
      }
    };

    const addNewWorld = () => {
      const maxIdx = worlds.value.length > 0 ? Math.max(...worlds.value.map(w => w.sort_index || 0)) : -1;
      const nw = { id: String(Date.now()), name: '', intro: '', desc: '', society: '', history: '', geography: '', magic_system: '', rules: '', extra_rules: '', conflict: '', sort_index: maxIdx + 1 };
      editWorld(nw);
    };
    const addNewChar = () => {
      const maxIdx = characters.value.length > 0 ? Math.max(...characters.value.map(c => c.sort_index || 0)) : -1;
      const nc = { id: String(Date.now()), name: '', gender: '', age: '', race: '', identity: '', appearance: '', personality: '', item: '', style: '', custom: '', sort_index: maxIdx + 1 };
      editChar(nc);
    };

    // ── RPG Start Form (新建开局状态) ──
    const setupForm = reactive({ worldId: null, characterId: null, engineId: null });
    const canStartRPG = computed(() => setupForm.worldId && setupForm.characterId && setupForm.engineId);

    const startRPG = async () => {
      if (!canStartRPG.value) return;
      const id = String(Date.now());
      sessionsData[id] = {
        id, name: '新RPG开局', mode: 'rpg',
        engine_id: setupForm.engineId,
        world_id: setupForm.worldId,
        char_id: setupForm.characterId,
        messages: [],
        updatedAt: Date.now()
      };
      currentSessionId.value = id;
      currentView.value = 'chat';
      // 立即持久化到后端
      await syncSession(id);
      if (window.posthog) {
        window.posthog.capture('game_start', { 
          worldId: setupForm.worldId, 
          engineId: setupForm.engineId, 
          characterId: setupForm.characterId 
        });
      }
      // 自动触发序章生成
      await sendMessage('开始游戏，请生成序章。', true);
    };

    const quickSetup = reactive({ characterId: null, engineId: 1 });

    const startAdventureFromDetail = () => {
      if (!quickSetup.characterId) {
        alert("请先选择你的角色！");
        return;
      }
      // 模拟秒开局：直接切入聊天界面
      currentView.value = 'chat';
    };
    
    // 修改侧边栏新建对话的逻辑
    const newChatSession = () => {
      currentSessionId.value = null;
      currentView.value = 'chat';
    };

    function selectSession(id) {
      currentSessionId.value = id;
      openDropdown.value = null;
      currentView.value = 'chat'; // Ensure we switch to chat view when selecting a session
      nextTick(() => {
        if (chatAreaEl.value) chatAreaEl.value.scrollTop = chatAreaEl.value.scrollHeight;
      });
    }

    async function togglePin(id) {
      const s = sessionsData[id];
      if (!s) return;
      s.is_pinned = s.is_pinned ? 0 : 1;
      await syncSession(id);
      openDropdown.value = null;
    }

    async function renameSession(id) {
      const s = sessionsData[id];
      if (!s) return;
      const newName = prompt('请输入新的会话名称：', s.name);
      if (newName && newName.trim()) {
        s.name = newName.trim();
        await syncSession(id);
      }
      openDropdown.value = null;
    }

    function exportSession(id) {
      const s = sessionsData[id];
      if (!s) return;
      const dataStr = JSON.stringify(s, null, 2);
      const blob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `WorldForge_Session_${s.name}_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
      openDropdown.value = null;
    }

    function deleteSession(id) {
      openDropdown.value = null;
      confirmTarget.value = sessionsData[id];
      confirmCb.value = async () => {
        try {
          await apiFetch(`/api/sessions/${id}`, { method: 'DELETE' });
          delete sessionsData[id];
          if (currentSessionId.value === id) currentSessionId.value = null;
        } catch (e) {
          alert('删除失败，请检查网络。');
        }
      };
      showConfirm.value = true;
    }

    // ── Profiles (打通后端) ──
    const activeProfileId = ref(null);
    const editingProfileId = ref(null);
    const showApiKey = ref(false);
    const showQuickPaste = ref(false);
    const showNewProfileModal = ref(false);
    const newProfileForm = ref({ name: '', baseUrl: '', apiKey: '', model: '' });
    const tempEditForm = ref({ id: '', name: '', baseUrl: '', apiKey: '', model: '' });
    const profiles = ref([]);
    
    // 自动追踪最后选中的节点
    watch(activeProfileId, (newVal) => {
      if (newVal && currentUser.value.id) {
        localStorage.setItem('wf_active_profile_' + currentUser.value.id, newVal);
      }
    });

    const activeProfile = computed(() => {
      const found = profiles.value.find(p => p.id === activeProfileId.value);
      return found || (profiles.value.length > 0 ? profiles.value[0] : { name: '未配置', model: 'N/A' });
    });

    // 已经改为弹窗，此 computed 可保留作为兼容，但主要逻辑将转移到 tempEditForm
    const editingProfile = computed(() => {
      if (!editingProfileId.value) return null;
      return profiles.value.find(p => p.id === editingProfileId.value) || null;
    });

    const startEditing = (p) => {
      editingProfileId.value = p.id;
      tempEditForm.value = { ...p };
    };

    async function loadProfiles() {
      try {
        const res = await apiFetch('/api/profiles');
        profiles.value = await res.json();
        // 4. 恢复 API 节点选中状态与新建开局默认选中
        const userProfileKey = 'wf_active_profile_' + currentUser.value.id;
        const storedProfileId = activeProfileId.value || localStorage.getItem(userProfileKey);
        const profileExists = storedProfileId && profiles.value.find(p => p.id === storedProfileId);
        if (profileExists) {
          activeProfileId.value = storedProfileId;
        } else if (profiles.value.length > 0) {
          activeProfileId.value = profiles.value[0].id;
        }

      } catch (e) { console.error('加载节点失败'); }
    }
    
    const importInput = ref(null);
    const importSessionsInput = ref(null);
    const importWorldsInput = ref(null);
    const importCharsInput = ref(null);
    const quickAddText = ref('');

    // --- Data Management Logic ---
    const downloadJson = (data, filename) => {
      const dataStr = JSON.stringify(data, null, 2);
      const blob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    };

    const exportSessions = async () => {
      try {
        const res = await apiFetch('/api/sessions');
        const data = await res.json();
        downloadJson(data, `wf_sessions_${Date.now()}.json`);
      } catch (e) { alert('导出失败'); }
    };

    const exportWorlds = () => downloadJson(worlds.value, `wf_worlds_${Date.now()}.json`);
    const exportChars = () => downloadJson(characters.value, `wf_chars_${Date.now()}.json`);

    const genNewId = () => String(Date.now()) + Math.random().toString(36).slice(2);

    const importSessions = (e) => {
      const file = e.target.files[0]; if (!file) return;
      const reader = new FileReader();
      reader.onload = async (evt) => {
        try {
          const items = JSON.parse(evt.target.result);
          const data = Array.isArray(items) ? items : [items];
          for (const item of data) {
            const newItem = { ...item, id: genNewId(), title: item.title || item.name || '导入存档' };
            await apiFetch('/api/sessions', { method: 'POST', body: JSON.stringify(newItem) });
          }
          alert(`✅ 导入成功，共导入 ${data.length} 条存档`);
          await loadSessions();
        } catch (err) { alert('导入失败：格式错误'); }
        e.target.value = '';
      };
      reader.readAsText(file);
    };

    const importWorlds = (e) => {
      const file = e.target.files[0]; if (!file) return;
      const reader = new FileReader();
      reader.onload = async (evt) => {
        try {
          const items = JSON.parse(evt.target.result);
          const data = Array.isArray(items) ? items : [items];
          for (const item of data) {
            const newItem = { ...item, id: genNewId() };
            await apiFetch('/api/worlds', { method: 'POST', body: JSON.stringify(newItem) });
          }
          alert(`✅ 导入成功，共导入 ${data.length} 个世界设定`);
          await loadAssets();
        } catch (err) { alert('导入失败：格式错误'); }
        e.target.value = '';
      };
      reader.readAsText(file);
    };

    const importChars = (e) => {
      const file = e.target.files[0]; if (!file) return;
      const reader = new FileReader();
      reader.onload = async (evt) => {
        try {
          const items = JSON.parse(evt.target.result);
          const data = Array.isArray(items) ? items : [items];
          for (const item of data) {
            const newItem = { ...item, id: genNewId() };
            await apiFetch('/api/characters', { method: 'POST', body: JSON.stringify(newItem) });
          }
          alert(`✅ 导入成功，共导入 ${data.length} 个角色设定`);
          await loadAssets();
        } catch (err) { alert('导入失败：格式错误'); }
        e.target.value = '';
      };
      reader.readAsText(file);
    };

    async function addProfile() {
      const newId = String(Date.now());
      const newP = { id: newId, name: '新建节点', baseUrl: '', apiKey: '', model: 'gpt-4o' };
      try {
        await apiFetch('/api/profiles', { method: 'POST', body: JSON.stringify(newP) });
        await loadProfiles();
        editingProfileId.value = newId;
        showApiKey.value = false;
      } catch (e) { alert('新建失败'); }
    }

    async function deleteProfile(id) {
      const p = profiles.value.find(x => x.id === id);
      confirmTarget.value = p || { name: '该节点' };
      confirmCb.value = async () => {
        try {
          await apiFetch(`/api/profiles/${id}`, { method: 'DELETE' });
          await loadProfiles();
          if (activeProfileId.value === id) {
            activeProfileId.value = profiles.value.length > 0 ? profiles.value[0].id : null;
          }
          if (editingProfileId.value === id) {
            editingProfileId.value = null;
          }
        } catch (e) { alert('删除失败'); }
      };
      showConfirm.value = true;
    }

    // 移除 watch(editingProfile)，因为现在改为显式保存模式
    
    const saveApiConfig = async () => {
      try {
        await apiFetch('/api/profiles', { 
          method: 'POST', 
          body: JSON.stringify(tempEditForm.value) 
        });
        await loadProfiles();
        editingProfileId.value = null;
      } catch (e) { 
        alert('保存失败，请检查网络。');
      }
    };

    const exportApiData = () => {
      const dataStr = JSON.stringify(profiles.value, null, 2);
      const blob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `WorldForge_api_nodes_${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    };

    const triggerImport = () => {
      if (importInput.value) importInput.value.click();
    };

    const importApiData = (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = async (evt) => {
        try {
          const parsed = JSON.parse(evt.target.result);
          if (Array.isArray(parsed) && parsed.length > 0) {
            for (const item of parsed) {
              await apiFetch('/api/profiles', {
                method: 'POST',
                body: JSON.stringify(item)
              });
            }
            await loadProfiles();
            alert(`✅ 成功导入 ${parsed.length} 个节点！`);
          } else {
            alert('格式错误：需要包含节点数组的 JSON 文件。');
          }
        } catch (err) {
          alert('导入失败：' + err.message);
        }
        e.target.value = '';
      };
      reader.readAsText(file);
    };

    const saveNewProfile = async () => {
      if (!newProfileForm.value.name || !newProfileForm.value.baseUrl || !newProfileForm.value.apiKey) return;
      const payload = { ...newProfileForm.value, id: String(Date.now()) };
      const res = await apiFetch('/api/profiles', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        await loadProfiles(); // 刷新列表
        activeProfileId.value = payload.id; // 自动选中新节点
        closeNewProfileModal();
      }
    };

    const closeNewProfileModal = () => {
      showNewProfileModal.value = false;
      quickAddText.value = '';
      newProfileForm.value = { name: '', baseUrl: '', apiKey: '', model: '' };
    };

    const quickAddProfiles = async () => {
      const text = quickAddText.value.trim();
      if (!text) return;
      const rawLines = text.split('\n');
      let formatOk = 0;
      let added = 0;
      for (const rawLine of rawLines) {
        const line = rawLine.trim();
        if (!line) continue;
        const commas = [];
        let searchFrom = 0;
        while (commas.length < 3) {
          const pos = line.indexOf(',', searchFrom);
          if (pos === -1) break;
          commas.push(pos);
          searchFrom = pos + 1;
        }
        if (commas.length < 3) continue;
        const name    = line.slice(0, commas[0]).trim();
        const baseUrl = line.slice(commas[0] + 1, commas[1]).trim();
        const apiKey  = line.slice(commas[1] + 1, commas[2]).trim();
        const model   = line.slice(commas[2] + 1).trim();
        if (!name || !baseUrl || !apiKey || !model) continue;
        formatOk++;
        const res = await apiFetch('/api/profiles', {
          method: 'POST',
          body: JSON.stringify({
            id: String(Date.now()) + String(Math.random()).slice(2, 6),
            name: name,
            baseUrl: baseUrl,
            apiKey: apiKey,
            model: model
          })
        });
        if (res.ok) added++;
      }
      if (formatOk === 0) {
        alert('⚠️ 未识别到有效格式。请确保每行包含4个用英文逗号分隔的字段：名称,URL,Key,模型');
        return;
      }
      await loadProfiles();
      quickAddText.value = '';
      showNewProfileModal.value = false;
      alert(`✅ 成功添加 ${added} 个节点${added < formatOk ? `（${formatOk - added} 个失败）` : ''}！`);
    };

    const apiFields = computed(() => [
      { label:'Temperature', value:'0.85' },
      { label:'Max Tokens',  value:'4096' },
      { label:'Top P',       value:'0.95' },
      { label:'Timeout',     value:'60s' },
    ]);

    // ── Current User Mock (已废弃，迁至顶部真实状态) ──

    // ── Presets ──
    const editingEngine = ref(null);

    const editEngine = (e) => {
      editingEngine.value = e;
      originalEditData.value = JSON.stringify(e);
    };
    const addNewEngine = () => {
      const maxIdx = systemPrompts.value.length > 0 ? Math.max(...systemPrompts.value.map(p => p.sort_index || 0)) : -1;
      const ne = { id: String(Date.now()), name: '', type: 'rpg', active: false, intro: '', desc: '', isPublic: false, sort_index: maxIdx + 1 };
      editEngine(ne);
    };

    // ── RPG Form ──
    const rpgForm = reactive({
      world:'这是一片被古老诅咒笼罩的大陆，黑暗神殿矗立于荒原中心。',
      society:'封建制，由教会与贵族共同统治', history:'三百年前，魔法战争摧毁了旧帝国',
      geography:'北部冰原，中部荒野，南部密林', magic_system:'元素亲和体系，精神力作为消耗资源',
      rules:'死亡即重置，道具可从敌人处获取', identity:'流亡骑士，前王国近卫队成员',
      appearance:'银色长发，左眼蒙着黑色眼罩', personality:'外冷内热，对弱者有强烈的保护欲',
      item:'古旧大陆地图（残缺）、父亲留下的断剑', custom:'',
    });
    const rpgLocks = reactive({
      world:false, society:false, history:false, geography:false,
      magic_system:false, rules:false, identity:false, appearance:false, personality:false, item:false,
    });

    // ── Input & Send ──
    const inputText   = ref('');
    const chatAreaEl  = ref(null);
    const mainInputEl = ref(null);
    const welcomeInputEl = ref(null);
    const showScrollBottom = ref(false);
    const isStreaming = ref(false);
    const currentReader = ref(null);

    const stopStreaming = () => {
      if (currentReader.value) {
        currentReader.value.cancel();
        currentReader.value = null;
      }
      isStreaming.value = false;
    };

    const scrollToBottom = async (smooth = false) => {
      await nextTick();
      if (chatAreaEl.value) {
        chatAreaEl.value.scrollTo({ top: chatAreaEl.value.scrollHeight, behavior: smooth ? 'smooth' : 'auto' });
      }
    };

    const onChatScroll = () => {
      if (!chatAreaEl.value) return;
      const { scrollTop, clientHeight, scrollHeight } = chatAreaEl.value;
      showScrollBottom.value = scrollHeight - scrollTop - clientHeight > 100;
    };

    function autoResize(e) {
      const el = e.target;
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 200) + 'px';
    }

    async function sendFromWelcome() {
      const text = inputText.value.trim();
      if (!text) return;
      const id = String(Date.now());
      const mode = 'chat'; 
      // 1. 创建空会话容器（sendMessage 会负责填充第一条消息）
      sessionsData[id] = {
        id, name: text.slice(0, 24) + (text.length > 24 ? '…' : ''), mode,
        messages: [],
        updatedAt: Date.now()
      };
      currentSessionId.value = id;
      actionChips.value = []; // 清空欢迎页残留
      
      // 2. 立即持久化到后端，防止刷新丢失
      await syncSession(id);
      
      // 3. 自动触发发送逻辑，让 AI 开始回话
      sendMessage();
    }

    async function sendMessage(rawText = null, silent = false) {
      const text = (typeof rawText === 'string' && rawText.trim()) ? rawText.trim() : inputText.value.trim();
      if (!text || !activeSession.value) return;

      if (window.posthog) {
        window.posthog.capture('chat_send', { 
          mode: currentMode.value, 
          length: text.length, 
          is_silent: silent 
        });
      }

      // 1. 数字快捷选择逻辑
      if (currentMode.value === 'rpg' && actionChips.value.length > 0 && /^\d+$/.test(text)) {
        const selectedChips = text.split('').map(num => actionChips.value[parseInt(num) - 1]).filter(c => c);
        if (selectedChips.length > 0) text = selectedChips.join('，');
      }

      // 2. 清空 UI 状态
      actionChips.value = [];
      showActionList.value = false;
      showCharDrawer.value = false;
      showToolsMenu.value = false;

      const msgs = activeSession.value.messages;
      // [沉浸式] 如果是非静默模式，才将用户消息推入 UI 列表
      if (!silent) {
        msgs.push({ id: Date.now(), role: 'user', content: text.replace(/\n/g, '<br>') });
      } else {
        // 静默模式下，依然推入消息但标记为 hidden，以便同步到后端维持上下文，但在前端隐藏
        msgs.push({ id: Date.now(), role: 'user', content: text, hidden: true });
      }
      inputText.value = '';

      // 3. 准备 AI 占位消息 (显示构思中动画)
      const aiMsg = reactive({ 
        id: Date.now() + 1, 
        role: 'ai', 
        content: '<i class="fas fa-brain fa-pulse"></i> AI 正在构思中...', 
        cot: '', 
        debug: '',
        usage: {
          user_words: text.length,
          ai_words: 0,
          prompt_tokens: '-',
          completion_tokens: '-'
        }
      });
      msgs.push(aiMsg);

      // 滚到底部
      nextTick(() => { 
        if (chatAreaEl.value) chatAreaEl.value.scrollTop = chatAreaEl.value.scrollHeight;
        if (mainInputEl.value) mainInputEl.value.style.height = 'auto';
      });

      // 4. 发起真实流式请求
      isStreaming.value = true;
      try {
        const response = await apiFetch('/api/chat', {
          method: 'POST',
          body: JSON.stringify({
            session_id: currentSessionId.value,
            message: text,
            mode: currentMode.value,
            profile_id: activeProfileId.value,
            world_id: activeSession.value?.world_id || null,
            char_id: activeSession.value?.char_id || null,
            engine_id: activeSession.value?.engine_id || null,
            context_limit: advParams.contextLimit,
            temperature: currentMode.value === 'rpg' ? advParams.rpgTemp : advParams.chatTemp
          })
        });

        currentReader.value = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = "";
        let firstChunk = true;

        while (true) {
          const { done, value } = await currentReader.value.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.error) {
                  aiMsg.content = `<span style="color:var(--danger)">[错误] ${data.detail || data.error}</span>`;
                  return;
                }
                
                // 处理 OpenAI 格式的流式数据
                const content = data.choices?.[0]?.delta?.content || "";
                if (content && firstChunk) {
                  firstChunk = false;
                }

                // 提取使用量数据包
                if (data.usage) {
                  aiMsg.usage.prompt_tokens = data.usage.prompt_tokens || '-';
                  aiMsg.usage.completion_tokens = data.usage.completion_tokens || '-';
                }
                fullText += content;
                
                // [逻辑闭环] 仅在开启流式输出时才实时更新 UI
                if (streamingEnabled.value) {
                  // 实时提取 <cot> 内容
                  const cotMatch = fullText.match(/<cot>([\s\S]*?)<\/cot>/);
                  if (cotMatch) {
                    aiMsg.cot = cotMatch[1];
                    const visibleText = fullText.replace(/<cot>[\s\S]*?<\/cot>/g, '').trim();
                    if (visibleText) {
                      aiMsg.content = marked.parse(visibleText);
                    }
                  } else {
                    const visibleText = fullText.trim();
                    if (visibleText) {
                      aiMsg.content = marked.parse(visibleText);
                    }
                  }

                  // 实时提取 [推荐行动]
                  const actionMatch = fullText.match(/\[推荐行动\]([\s\S]*?)$/);
                  if (actionMatch && actionMatch[1]) {
                     const rawActions = actionMatch[1].split('\n').filter(a => a.trim().length > 1);
                     actionChips.value = rawActions.map(a => a.replace(/^\d+\.\s*/, '').trim()).slice(0, 3);
                  }

                  // [智能滚动] 只有当用户当前距离底部不足 150px 时才自动跟随
                  if (chatAreaEl.value) {
                    const { scrollTop, clientHeight, scrollHeight } = chatAreaEl.value;
                    const isNearBottom = scrollHeight - scrollTop - clientHeight < 150;
                    if (isNearBottom) {
                      chatAreaEl.value.scrollTop = chatAreaEl.value.scrollHeight;
                    }
                  }
                }
              } catch (e) { /* 忽略不完整的 JSON 分片 */ }
            }
          }
        }
        
        // [逻辑闭环] 流式传输结束后的最终渲染
        const finalCotMatch = fullText.match(/<cot>([\s\S]*?)<\/cot>/);
        if (finalCotMatch) aiMsg.cot = finalCotMatch[1];
        aiMsg.content = marked.parse(fullText.replace(/<cot>[\s\S]*?<\/cot>/g, '').trim());

        const finalActionMatch = fullText.match(/\[推荐行动\]([\s\S]*?)$/);
        if (finalActionMatch && finalActionMatch[1]) {
           const rawActions = finalActionMatch[1].split('\n').filter(a => a.trim().length > 1);
           actionChips.value = rawActions.map(a => a.replace(/^\d+\.\s*/, '').trim()).slice(0, 3);
        }

        // 统计最终 AI 字数（去除 cot 和 html 标签）
        const aiVisibleText = fullText.replace(/<cot>[\s\S]*?<\/cot>/g, '').replace(/<[^>]*>/g, '').trim();
        aiMsg.usage.ai_words = aiVisibleText.length;
        
        if (chatAreaEl.value) nextTick(() => chatAreaEl.value.scrollTop = chatAreaEl.value.scrollHeight);

        // 5. 保存会话存档
        await syncSession(currentSessionId.value);

      } catch (err) {
        if (err.name === 'AbortError') {
          aiMsg.content += '<br><span style="color:var(--grey)">[已停止生成]</span>';
        } else {
          aiMsg.content = `<span style="color:var(--danger)">[网络异常] 无法连接到后厨，请检查后端程序是否运行。</span>`;
        }
      } finally {
        isStreaming.value = false;
        currentReader.value = null;
      }
    }

    const welcomeHints = ['开始新的冒险', '帮我写一段代码', '继续上次剧情', '头脑风暴想法'];

    // --- Message Actions Logic ---
    const stripHtml = (html) => html.replace(/<[^>]*>/g, '').trim();

    // ── 通用兼容性复制工具 (解决 HTTP 下 navigator.clipboard 失效问题) ──
    const copyToClipboard = async (text) => {
      if (navigator.clipboard && window.isSecureContext) {
        try {
          await navigator.clipboard.writeText(text);
          return true;
        } catch (err) {
          console.error('Modern copy failed:', err);
        }
      }
      try {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        if (successful) return true;
      } catch (err) {
        console.error('Legacy copy failed:', err);
      }
      return false;
    };

    const copyMsg = async (msg) => {
      const textToCopy = stripHtml(msg.content);
      const ok = await copyToClipboard(textToCopy);
      if (ok) {
        copiedMsgId.value = msg.id;
        setTimeout(() => { copiedMsgId.value = null; }, 1500);
      } else {
        alert('复制失败，请手动选择文字复制。');
      }
    };

    const deleteMsg = async (msg) => {
      const msgs = activeSession.value.messages;
      const idx = msgs.findIndex(m => m.id === msg.id);
      if (idx !== -1) {
        msgs.splice(idx, 1);
        await syncSession(currentSessionId.value);
      }
    };

    const editUserMsg = async (msg) => {
      const msgs = activeSession.value.messages;
      const idx = msgs.findIndex(m => m.id === msg.id);
      if (idx !== -1) {
        inputText.value = stripHtml(msg.content);
        msgs.splice(idx); // 删除从该条开始的所有消息
        await syncSession(currentSessionId.value);
        // 自动聚焦输入框
        nextTick(() => { if (mainInputEl.value) mainInputEl.value.focus(); });
      }
    };

    const regenMsg = async (msg) => {
      const msgs = activeSession.value.messages;
      const aiIdx = msgs.findIndex(m => m.id === msg.id);
      if (aiIdx > 0) {
        const userMsg = msgs[aiIdx - 1];
        if (userMsg.role === 'user') {
          const userText = stripHtml(userMsg.content);
          if (window.posthog) {
            window.posthog.capture('chat_regen', { mode: currentMode.value });
          }
          msgs.splice(aiIdx - 1, 2); // 删除用户消息和AI消息
          await syncSession(currentSessionId.value);
          await sendMessage(userText); // 重新发送
        }
      }
    };

    // ── Drag & Drop Sortable ──
    const engineListRef = ref(null);
    const worldListRef = ref(null);
    const charListRef = ref(null);

    const initSortable = (el, listRef, type) => {
      if (!el) return;
      if (el._sortable) {
        el._sortable.destroy();
        el._sortable = null;
      }
      el._sortable = new Sortable(el, {
        animation: 150,
        onEnd: async (evt) => {
          const { oldIndex, newIndex } = evt;
          if (oldIndex === newIndex) return;
          const item = listRef.value.splice(oldIndex, 1)[0];
          listRef.value.splice(newIndex, 0, item);
          
          listRef.value.forEach((x, i) => { x.sort_index = i; });
          
          const endpoint = type === 'world' ? '/api/worlds/reorder' : (type === 'char' ? '/api/characters/reorder' : '/api/prompts/reorder');
          const payload = listRef.value.map(x => ({ id: x.id, sort_index: x.sort_index }));
          try {
            await apiFetch(endpoint, { method: 'PUT', body: JSON.stringify(payload) });
          } catch (e) {
            console.error('排序同步失败:', e);
          }
        }
      });
    };

    watch(currentView, async (newVal) => {
      await nextTick();
      if (newVal === 'engine-mgr' && engineListRef.value) {
        initSortable(engineListRef.value, systemPrompts, 'engine');
      } else if (newVal === 'world-mgr' && worldListRef.value) {
        initSortable(worldListRef.value, worlds, 'world');
      } else if (newVal === 'char-mgr' && charListRef.value) {
        initSortable(charListRef.value, characters, 'char');
      }
    }, { immediate: true });

    watch(editingWorld, async (newVal) => {
      if (newVal === null) {
        await nextTick();
        if (worldListRef.value) initSortable(worldListRef.value, worlds, 'world');
      }
    });

    watch(editingChar, async (newVal) => {
      if (newVal === null) {
        await nextTick();
        if (charListRef.value) initSortable(charListRef.value, characters, 'char');
      }
    });

    watch(editingEngine, async (newVal) => {
      if (newVal === null) {
        await nextTick();
        if (engineListRef.value) initSortable(engineListRef.value, systemPrompts, 'engine');
      }
    });

    // ── Character Mock ──
    const charStats = ref([
      { name:'HP',  val:72, color:'var(--danger)' },
      { name:'MP',  val:85, color:'var(--purple)' },
      { name:'STR', val:68, color:'var(--warn)' },
      { name:'DEX', val:91, color:'var(--green)' },
      { name:'INT', val:44, color:'var(--purple-lt)' },
    ]);
    const inventory = ref([
      { id:1, emoji:'🗺️', name:'残缺大陆地图', count:1 },
      { id:2, emoji:'⚔️', name:'父亲的断剑',   count:1 },
      { id:3, emoji:'🧪', name:'治疗药水',      count:3 },
      { id:4, emoji:'🕯️', name:'蜡烛',          count:5 },
      { id:5, emoji:'📜', name:'神秘卷轴',      count:1 },
      { id:6, emoji:'💰', name:'金币',           count:null },
      { id:7, emoji:'',   name:'', count:null },{ id:8, emoji:'', name:'', count:null },
      { id:9, emoji:'',   name:'', count:null },{ id:10,emoji:'', name:'', count:null },
      { id:11,emoji:'',   name:'', count:null },{ id:12,emoji:'', name:'', count:null },
    ]);

    // ── 超管面板 ──
    const inviteList = ref([]);
    const lastGeneratedCode = ref('');
    const copiedInviteCode = ref(false);

    const loadInvites = async () => {
      if (currentUser.value.role !== 'superadmin') return;
      try {
        const res = await apiFetch('/api/auth/invites');
        inviteList.value = await res.json();
      } catch (e) {
        console.error('加载邀请码列表失败');
      }
    };

    const generateInvite = async () => {
      try {
        const res = await apiFetch('/api/auth/invite', { method: 'POST' });
        const data = await res.json();
        lastGeneratedCode.value = data.code;
        await loadInvites();
      } catch (e) {
        alert('生成失败，请检查网络。');
      }
    };

    const copyInviteCode = async (code) => {
      const ok = await copyToClipboard(code);
      if (ok) {
        copiedInviteCode.value = code;
        setTimeout(() => { copiedInviteCode.value = false; }, 1500);
      } else {
        alert('复制失败');
      }
    };

    const toggleEnginePublic = async (engine) => {
      engine.isPublic = !engine.isPublic;
      const payload = {
        ...engine,
        content: engine.desc || '',
        is_public: engine.isPublic ? 1 : 0
      };
      try {
        await apiFetch('/api/prompts', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
      } catch (e) {
        engine.isPublic = !engine.isPublic;
        alert('保存失败，请检查网络。');
      }
    };

    watch(settingsTab, (newVal) => {
      if (newVal === 'admin') loadInvites();
    });

    return {
      hasRole,
      loggedIn, isLoginMode, loginUser, loginPass, loginPassConfirm, showPass, showPassConfirm, inviteCode, doLogin, doRegister, doLogout,
      currentView,
      sidebarCollapsed, charPanelOpen, sessionsOpen,
      showConfirm, confirmTarget, confirmDeleteExec,
      settingsTab, settingsNav, showCoT, showDebug, showCharDrawer, showToolsMenu, showProfileMenu, showEngineParams, showActionList, streamingEnabled, advParams,
      openDropdown, closeAllDropdowns, toggleDropdown,
      sessions, currentSessionId, isWelcome, activeSession, currentMode, currentMessages,
      selectSession, deleteSession,
      togglePin, renameSession, exportSession,
      profiles, activeProfileId, activeProfile, editingProfileId, editingProfile,
      showNewProfileModal, closeNewProfileModal, newProfileForm, tempEditForm, saveNewProfile, startEditing,
      importInput, quickAddText, addProfile, deleteProfile, saveApiConfig, exportApiData, triggerImport, importApiData, quickAddProfiles, apiFields,
      systemPrompts, rpgForm, rpgLocks,
      inputText, chatAreaEl, mainInputEl, welcomeInputEl,
      autoResize, sendFromWelcome, sendMessage,
      discoverSections, selectedCard, openDetail, newChatSession,
      characters, rpgEngines, systemPrompts, quickSetup, startAdventureFromDetail,
      worlds, setupForm, canStartRPG, startRPG,
      editingWorld, editingChar, addNewWorld, addNewChar,
      editWorld, editChar, saveEdit, exitEdit,
      editUserMsg, copyMsg, deleteMsg, regenMsg, copiedMsgId,
      currentUser, editingEngine, addNewEngine, editEngine, confirmDelete,
      charStats, inventory, actionChips,
      rowRefs, scrollRow, startDrag, stopDrag, onDrag,
      engineListRef, worldListRef, charListRef,
      showScrollBottom, scrollToBottom, onChatScroll,
      isStreaming, stopStreaming, currentReader, formatDate,
      resetAdvParams,
      inviteList, lastGeneratedCode, copiedInviteCode, generateInvite, copyInviteCode,
      toggleEnginePublic,
    };
  }
}
</script>

<style>
.bubble ul, .bubble ol {
  padding-left: 20px;
  margin: 6px 0;
}
.bubble ul li {
  list-style: disc;
  margin: 3px 0;
}
.bubble ol li {
  list-style: decimal;
  margin: 3px 0;
}
.bubble pre {
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 6px;
  padding: 12px;
  margin: 8px 0;
  overflow-x: auto;
}
.bubble code {
  font-family: monospace;
  font-size: var(--text-sm);
}
.bubble p code {
  background: rgba(255,255,255,0.08);
  padding: 2px 5px;
  border-radius: 4px;
}
.bubble blockquote {
  border-left: 3px solid var(--purple-lt);
  padding-left: 12px;
  margin: 8px 0;
  color: var(--grey);
}
</style>
