const { createApp, ref, computed, watch, nextTick, onMounted } = Vue;

// V13.6.0 (Backend Auth Integrated - Drag & Drop Visuals Enhanced)
const APP_VERSION = '13.6.0';

createApp({
    setup() {
        const sidebarOpen = ref(false);
        const showSettings = ref(false);
        const showAdvSettings = ref(false);
        const showRpgForm = ref(false);
        const input = ref('');
        const inputRef = ref(null);
        const isLoading = ref(false);
        let abortController = null; 
        const quickPasteConfig = ref(''); 
        const enableStream = ref(true); 

        const showPromptEditor = ref(false);
        const showCoT = ref(false);

        // --- 鉴权相关状态 ---
        const showAuthModal = ref(true);
        const authMode = ref('login'); 
        const currentUser = ref(null);
        const authForm = ref({ username: '', password: '', invite_code: '' });
        
        const token = ref(localStorage.getItem('wf_token'));

        // --- Backend API Utils ---
        const apiRequest = async (url, options = {}) => {
            const headers = { 'Content-Type': 'application/json', ...options.headers };
            if (token.value) headers['Authorization'] = `Bearer ${token.value}`;

            const response = await fetch(url, { ...options, headers });

            if (response.status === 401) {
                token.value = null;
                currentUser.value = null;
                localStorage.removeItem('wf_token');
                localStorage.removeItem('wf_user');
                showAuthModal.value = true;
                throw new Error("会话已过期");
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "请求失败");
            }
            return await response.json();
        };

        const api = {
            get: (url) => apiRequest(url, { method: 'GET' }),
            post: (url, data) => apiRequest(url, { method: 'POST', body: JSON.stringify(data) }),
            put: (url, data) => apiRequest(url, { method: 'PUT', body: JSON.stringify(data) }),
            delete: (url) => apiRequest(url, { method: 'DELETE' })
        };

        // --- 鉴权业务逻辑 ---
        const handleAuth = async () => {
            if (!authForm.value.username || !authForm.value.password) return showToast("账号密码必填");
            isLoading.value = true;
            try {
                if (authMode.value === 'login') {
                    const data = await api.post('/api/auth/login', {
                        username: authForm.value.username,
                        password: authForm.value.password
                    });
                    token.value = data.access_token;
                    currentUser.value = data.user;
                    localStorage.setItem('wf_token', data.access_token);
                    localStorage.setItem('wf_user', JSON.stringify(data.user));
                    showToast("登录成功");
                } else {
                    const res = await api.post('/api/auth/register', authForm.value);
                    showToast(res.message || "注册成功");
                    authMode.value = 'login';
                    isLoading.value = false;
                    return;
                }
                showAuthModal.value = false;
                await initAppData();
            } catch (err) {
                showToast(err.message);
            } finally {
                isLoading.value = false;
            }
        };

        const logout = () => {
            token.value = null;
            currentUser.value = null;
            localStorage.removeItem('wf_token');
            localStorage.removeItem('wf_user');
            sessions.value = [];
            currentSessionId.value = null;
            profiles.value = [];
            activeProfileId.value = null;
            systemPrompts.value = [];
            activeSystemPromptId.value = null;
            showAuthModal.value = true;
            showToast("已登出");
        };

        const generateInviteCode = async () => {
            try {
                const data = await api.post('/api/auth/invite', {});
                prompt("🔑 邀请码 (有效期内单次使用)：", data.code);
            } catch (err) { showToast(err.message); }
        };

        // --- 业务数据逻辑 ---
        const systemPrompts = ref([]);
        const activeSystemPromptId = ref(null);
        const activeSystemPrompt = computed(() => systemPrompts.value.find(p => p.id === activeSystemPromptId.value) || systemPrompts.value[0]);

        const canEditPrompt = (p) => {
            if (!p || !currentUser.value) return false;
            if (currentUser.value.role === 'superadmin') return true;
            return p.is_public !== 1;
        };

        const initPrompts = async () => {
            const data = await api.get('/api/prompts');
            if (data && data.length > 0) {
                systemPrompts.value = data;
            } else {
                const defaults = [
                    { id: 'sp_default_rpg', name: '通用RPG引擎', content: DEFAULT_RPG_PROMPT, is_public: 1, sort_index: 0 },
                    { id: 'sp_chat', name: '通用助手', content: DEFAULT_CHAT_PROMPT, is_public: 1, sort_index: 1 }
                ];
                for (const p of defaults) await api.post('/api/prompts', p);
                systemPrompts.value = defaults;
            }
            activeSystemPromptId.value = systemPrompts.value[0].id;
        };

        // [ENHANCED] 拖拽排序逻辑集成 (增加深度视觉反馈支持)
        let sortableInstance = null;
        watch(showPromptEditor, async (val) => {
            if (val) {
                await nextTick();
                const el = document.getElementById('prompt-list-container');
                if (el) {
                    sortableInstance = Sortable.create(el, {
                        animation: 200,
                        ghostClass: 'sortable-ghost',  // 目标位置的“虚空框”
                        dragClass: 'sortable-drag',    // 正在拖拽的“浮空卡片”
                        chosenClass: 'sortable-chosen', // 选中时的即时反馈
                        onEnd: async () => {
                            const ids = Array.from(el.children).map(child => child.getAttribute('data-id'));
                            const newOrderedPrompts = ids.map((id, index) => {
                                const p = systemPrompts.value.find(item => item.id === id);
                                return { ...p, sort_index: index };
                            });
                            systemPrompts.value = newOrderedPrompts;
                            try {
                                const reorderData = newOrderedPrompts.map(p => ({ id: p.id, sort_index: p.sort_index }));
                                await api.put('/api/prompts/reorder', reorderData);
                                showToast('排序已同步');
                            } catch (err) {
                                showToast('排序同步失败: ' + err.message);
                            }
                        }
                    });
                }
            } else {
                if (sortableInstance) { sortableInstance.destroy(); sortableInstance = null; }
            }
        });

        const importEngineTxt = async (event) => {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    const content = e.target.result;
                    const name = file.name.replace(/\.[^/.]+$/, "") || '未命名引擎';
                    const newId = 'sp_' + Date.now();
                    const newPrompt = { id: newId, name: name, content: content, is_public: 0, sort_index: systemPrompts.value.length };
                    await api.post('/api/prompts', newPrompt);
                    systemPrompts.value.push(newPrompt);
                    activeSystemPromptId.value = newId;
                    showToast(`已导入引擎: ${name}`);
                } catch (err) { showToast('导入失败: ' + err.message); }
            };
            reader.readAsText(file);
            event.target.value = ''; 
        };

        const profiles = ref([]);
        const activeProfileId = ref(null);
        const activeProfile = computed(() => profiles.value.find(p => p.id === activeProfileId.value) || profiles.value[0] || {});

        const initProfiles = async () => {
            const data = await api.get('/api/profiles');
            if (data && data.length > 0) {
                profiles.value = data;
                const lastId = localStorage.getItem('wf_last_profile_id');
                if (lastId && profiles.value.some(p => p.id === lastId)) {
                    activeProfileId.value = lastId;
                } else {
                    activeProfileId.value = profiles.value[0].id;
                }
            } else {
                const newId = 'p_' + Date.now();
                const def = { id: newId, name: '默认节点', baseUrl: 'https://api.openai.com/v1', apiKey: '', model: 'gpt-3.5-turbo', memoryLength: 4, stmLength: 6, tempRpg: 0.8, tempChat: 0.6 };
                await api.post('/api/profiles', def);
                profiles.value = [def];
                activeProfileId.value = newId;
            }
        };

        watch(activeProfileId, (newId) => {
            if (newId) localStorage.setItem('wf_last_profile_id', newId);
        });

        const sessions = ref([]);
        const currentSessionId = ref(null);
        const currentSession = computed(() => sessions.value.find(s => s.id === currentSessionId.value) || null);
        const editingSessionId = ref(null);
        const editTempTitle = ref('');

        const initSessions = async () => {
            const data = await api.get('/api/sessions');
            if (data && data.length > 0) {
                sessions.value = data;
                currentSessionId.value = sessions.value[0].id;
            } else {
                await createNewSession('chat');
            }
        };

        const initAppData = async () => {
            if (!token.value) return;
            try {
                await initPrompts(); 
                await initProfiles();
                await initSessions();
            } catch (err) { console.error("Init Error:", err); }
        };

        const toast = ref({ show: false, message: '' });
        const showToast = (m) => { toast.value.message = m; toast.value.show = true; setTimeout(() => { toast.value.show = false; }, 2000); };

        const visibleMessages = computed(() => {
            if (!currentSession.value) return [];
            return currentSession.value.messages.map((m, i) => ({ ...m, originalIndex: i })).filter(m => m.role !== 'system');
        });

        watch(() => systemPrompts.value, () => {
            if (showPromptEditor.value && activeSystemPrompt.value && canEditPrompt(activeSystemPrompt.value)) {
                api.post('/api/prompts', JSON.parse(JSON.stringify(activeSystemPrompt.value)));
            }
        }, { deep: true });

        watch(() => profiles.value, () => {
            if (showSettings.value || showAdvSettings.value) {
                const active = profiles.value.find(p => p.id === activeProfileId.value);
                if (active) api.post('/api/profiles', JSON.parse(JSON.stringify(active)));
            }
        }, { deep: true });

        watch(() => currentSession.value?.messages, () => {
            if (currentSession.value) api.post('/api/sessions', JSON.parse(JSON.stringify(currentSession.value)));
        }, { deep: true });

        // --- RPG & 交互逻辑 ---
        const rpgForm = ref({ world: '', rules: '', name: '', gender: '', race: '', age: '', appearance: '', personality: '', pov: '第一人称', style: '', custom: '', opening: '', identity: '', item: '' });
        const rpgLocks = ref({ world: false, rules: false, name: false, gender: false, race: false, age: false, appearance: false, personality: false, style: false, custom: false, opening: false, identity: false, item: false });
        const activeRandomTheme = ref('通用');

        const randomInput = (f) => {
            if (rpgLocks.value[f]) return; 
            if (f === 'age') { rpgForm.value.age = Math.floor(Math.random() * 99) + 1; return; }
            const arr = themeLibs[activeRandomTheme.value]?.[f];
            if (arr) rpgForm.value[f] = arr[Math.floor(Math.random() * arr.length)];
        };

        const randomAll = () => {
            ['world', 'name', 'gender', 'race', 'age', 'appearance', 'personality', 'style', 'opening', 'identity', 'item'].forEach(randomInput);
            showToast('已一键随机');
        };

        const rpgPromptPreview = computed(() => {
            let res = `---世界设定---\n世界观：${rpgForm.value.world || '默认'}\n`;
            if(rpgForm.value.rules) res += `附加规则：${rpgForm.value.rules}\n`;
            res += `\n---角色基础信息---\n姓名：${rpgForm.value.name}\n身份/职业：${rpgForm.value.identity}\n性别：${rpgForm.value.gender}\n种族：${rpgForm.value.race}\n年龄：${rpgForm.value.age}\n外貌：${rpgForm.value.appearance}\n性格：${rpgForm.value.personality}\n`;
            res += `描写人称：${rpgForm.value.pov}\n文风增强：${rpgForm.value.style || '无'}\n初始携带：${rpgForm.value.item}\n`;
            if (rpgForm.value.style) res += `\n【系统最高优先级指令：文风协议】\n你必须严格模仿[${rpgForm.value.style}]的笔触进行描写。\n`;
            res += `\n【初始行动】：${rpgForm.value.opening || '开始剧情。'}`;
            return res;
        });

        const startRpgGame = async () => {
            const req = ['world', 'name', 'gender', 'race', 'age', 'appearance', 'personality', 'opening', 'identity'];
            if (req.some(f => !rpgForm.value[f])) return showToast('请填写必填项');
            await createNewSession('rpg'); 
            currentSession.value.title = `${rpgForm.value.name} - ${activeSystemPrompt.value.name}`;
            currentSession.value.messages.push({ role: 'user', content: rpgPromptPreview.value });
            await api.post('/api/sessions', JSON.parse(JSON.stringify(currentSession.value)));
            showRpgForm.value = false;
            callApi(rpgPromptPreview.value.length);
        };

        const createNewSession = async (type = 'chat') => {
            const newId = Date.now().toString();
            const pObj = type === 'chat' ? systemPrompts.value.find(p => p.id === 'sp_chat') : activeSystemPrompt.value;
            const content = pObj ? pObj.content : (type === 'chat' ? DEFAULT_CHAT_PROMPT : DEFAULT_RPG_PROMPT);
            const newS = { id: newId, type, title: type === 'chat' ? '新对话' : '未命名剧本', messages:[{ role: 'system', content }], updatedAt: Date.now() };
            await api.post('/api/sessions', newS);
            sessions.value.unshift(newS);
            currentSessionId.value = newId;
            if (window.innerWidth < 768) sidebarOpen.value = false;
        };

        const sendMessage = () => {
            if (!input.value.trim() || isLoading.value) return;
            if (!currentSession.value) return;
            const userLen = input.value.length; 
            currentSession.value.messages.push({ role: 'user', content: input.value });
            input.value = '';
            nextTick(autoResize);
            callApi(userLen);
        };

        const callApi = async (userLen = 0) => {
            if (!activeProfile.value.apiKey) return showToast("配置 API Key");
            const s = currentSession.value;
            s.updatedAt = Date.now();
            const isStreamActive = !!enableStream.value;
            s.messages.push({ role: 'assistant', content: '', isStreaming: isStreamActive, wasInterrupted: false });
            const msgIdx = s.messages.length - 1;
            isLoading.value = true; scrollToBottom();
            abortController = new AbortController();
            try {
                let msgs = [s.messages[0], ...s.messages.slice(1, -1).slice(-parseInt(activeProfile.value.memoryLength))];
                const reqBody = { model: activeProfile.value.model, messages: msgs, temperature: s.type === 'rpg' ? parseFloat(activeProfile.value.tempRpg) : parseFloat(activeProfile.value.tempChat), stream: isStreamActive };
                if (isStreamActive) reqBody.stream_options = { include_usage: true };
                const res = await fetch(`${activeProfile.value.baseUrl.replace(/\/+$/, '')}/chat/completions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${activeProfile.value.apiKey}` },
                    body: JSON.stringify(reqBody),
                    signal: abortController.signal
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                let aiC = ''; let finalUsage = null;
                if (isStreamActive) {
                    const reader = res.body.getReader(); const decoder = new TextDecoder();
                    while (true) {
                        const { done, value } = await reader.read(); if (done) break;
                        const chunk = decoder.decode(value);
                        chunk.split('\n').forEach(line => {
                            if (line.startsWith('data: ') && line !== 'data: [DONE]') {
                                try {
                                    const json = JSON.parse(line.substring(6));
                                    if (json.choices?.[0]?.delta?.content) { aiC += json.choices[0].delta.content; s.messages[msgIdx].content = aiC; scrollToBottom(); }
                                    if (json.usage) finalUsage = json.usage;
                                } catch (e) {}
                            }
                        });
                    }
                } else {
                    const data = await res.json(); aiC = data.choices[0].message.content; s.messages[msgIdx].content = aiC;
                    if (data.usage) finalUsage = data.usage;
                }
                const usageData = finalUsage || { prompt_tokens: 0, completion_tokens: 0 };
                s.messages[msgIdx].usage = { user_words: userLen, ai_words: aiC.length, prompt_tokens: usageData.prompt_tokens, completion_tokens: usageData.completion_tokens };
            } catch (err) { if (err.name !== 'AbortError') s.messages[msgIdx].content += `\n\n**[中断]:** ${err.message}`; }
            finally { s.messages[msgIdx].isStreaming = false; isLoading.value = false; scrollToBottom(); api.post('/api/sessions', JSON.parse(JSON.stringify(s))); }
        };

        const renderMarkdown = (t) => {
            if (!t) return '';
            const cot = t.replace(/<cot>([\s\S]*?)<\/cot>/gi, '<details class="cot-box"><summary><i class="fas fa-brain"></i> 思维链推演 (CoT)</summary><div class="cot-content">$1</div></details>');
            return marked.parse(cot);
        };

        const autoResize = () => { if (inputRef.value) { inputRef.value.style.height = 'auto'; inputRef.value.style.height = inputRef.value.scrollHeight + 'px'; } };
        const scrollToBottom = async () => { await nextTick(); const c = document.getElementById('chat-container'); if(c) c.scrollTop = c.scrollHeight; };
        const formatDate = (ts) => { const d = new Date(ts); return `${d.getMonth()+1}/${d.getDate()} ${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`; };

        const exportProfiles = () => {
            const data = JSON.stringify(profiles.value, null, 2);
            const blob = new Blob([data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = `WF_Profiles_Backup.json`; a.click();
            URL.revokeObjectURL(url);
            showToast('导出成功');
        };

        const importProfiles = (event) => {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    const newProfiles = JSON.parse(e.target.result);
                    if (!Array.isArray(newProfiles)) throw new Error("格式错误");
                    for (const p of newProfiles) {
                        const importId = 'p_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
                        await api.post('/api/profiles', { ...p, id: importId });
                    }
                    profiles.value = await api.get('/api/profiles');
                    if (profiles.value.length > 0) activeProfileId.value = profiles.value[0].id;
                    showToast('导入成功');
                } catch (err) { showToast('失败: ' + err.message); }
            };
            reader.readAsText(file);
            event.target.value = ''; 
        };

        const applyQuickPaste = async () => {
            const lines = quickPasteConfig.value.split('\n').filter(l => l.trim() !== '');
            if (lines.length === 0) return showToast('内容为空');
            let added = 0;
            for (const line of lines) {
                const parts = line.split(',').map(s => s.trim());
                if (parts.length >= 4) {
                    const p = { id: 'p_'+Date.now()+'_'+Math.random().toString(36).substr(2,5), name: parts[0], baseUrl: parts[1], apiKey: parts[2], model: parts[3], memoryLength: 4, stmLength: 6, tempRpg: 0.8, tempChat: 0.6 };
                    await api.post('/api/profiles', p);
                    added++;
                }
            }
            if (added > 0) { profiles.value = await api.get('/api/profiles'); showToast(`已添加 ${added} 条`); quickPasteConfig.value = ''; }
        };

        const exportCurrentSession = () => {
            if (!currentSession.value) return showToast("当前无会话");
            const sessionData = { version: APP_VERSION, ...currentSession.value };
            const data = JSON.stringify(sessionData, null, 2);
            const blob = new Blob([data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const safeTitle = (currentSession.value.title || 'unnamed').replace(/[\\/:*?"<>|]/g, '_');
            a.href = url; a.download = `WF_SAVE_${safeTitle}.json`; a.click();
            URL.revokeObjectURL(url);
            showToast('存档导出成功');
        };

        const importSession = (event) => {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    const newSession = JSON.parse(e.target.result);
                    if (!newSession.messages) throw new Error("无效存档");
                    newSession.id = Date.now().toString();
                    await api.post('/api/sessions', newSession);
                    sessions.value.unshift(newSession);
                    currentSessionId.value = newSession.id;
                    showToast('存档导入成功');
                } catch (err) { showToast('导入失败'); }
            };
            reader.readAsText(file);
            event.target.value = '';
        };

        const exportRpgModule = () => {
            const moduleData = { version: APP_VERSION, type: "WorldForge_Module", rpgSettings: rpgForm.value, systemPrompt: activeSystemPrompt.value };
            const data = JSON.stringify(moduleData, null, 2);
            const blob = new Blob([data], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = `WF_MOD_${rpgForm.value.name || 'unnamed'}.json`; a.click();
            URL.revokeObjectURL(url);
            showToast('模组导出成功');
        };

        const importRpgModule = async (event) => {
            const file = event.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    const data = JSON.parse(e.target.result);
                    if (data.rpgSettings) rpgForm.value = { ...rpgForm.value, ...data.rpgSettings };
                    if (data.systemPrompt) {
                        const exists = systemPrompts.value.find(p => p.content === data.systemPrompt.content);
                        if (exists) activeSystemPromptId.value = exists.id;
                        else {
                            const newP = { ...data.systemPrompt, id: 'sp_mod_' + Date.now(), is_public: 0 };
                            systemPrompts.value.push(newP);
                            activeSystemPromptId.value = newP.id;
                            await api.post('/api/prompts', newP);
                        }
                    }
                    showToast('模组加载成功');
                } catch (err) { showToast('加载失败'); }
            };
            reader.readAsText(file);
            event.target.value = ''; 
        };

        onMounted(async () => {
            const savedUser = localStorage.getItem('wf_user');
            if (token.value && savedUser) {
                try {
                    currentUser.value = JSON.parse(savedUser);
                    await initAppData();
                    showAuthModal.value = false;
                } catch (e) { showAuthModal.value = true; }
            } else { showAuthModal.value = true; }
        });

        return {
            sidebarOpen, showSettings, showAdvSettings, showRpgForm, input, inputRef, isLoading, rpgForm, rpgLocks, activeRandomTheme, rpgPromptPreview,
            profiles, activeProfileId, activeProfile, addNewProfile: () => { const id = 'p_'+Date.now(); const p = {id, name:'新节点', baseUrl:'', apiKey:'', model:'', memoryLength:4, stmLength:6, tempRpg:0.8, tempChat:0.6}; profiles.value.push(p); activeProfileId.value=id; api.post('/api/profiles',p); },
            deleteActiveProfile: () => { if(confirm('删除？')){ api.delete(`/api/profiles/${activeProfileId.value}`); profiles.value = profiles.value.filter(p=>p.id!==activeProfileId.value); activeProfileId.value=profiles.value[0]?.id; } },
            sessions, currentSessionId, currentSession, visibleMessages, editingSessionId, editTempTitle, startEditTitle: (s) => { editingSessionId.value=s.id; editTempTitle.value=s.title; },
            saveEditTitle: async (s) => { if(editTempTitle.value.trim()){ s.title=editTempTitle.value.trim(); await api.post('/api/sessions',s); } editingSessionId.value=null; },
            createNewSession, openRpgForm: () => { showRpgForm.value=true; sidebarOpen.value=false; }, startRpgGame, handleSessionClick: (id) => { currentSessionId.value=id; sidebarOpen.value=false; setTimeout(scrollToBottom,100); },
            deleteSingleSession: async (id) => { if(confirm('删除？')){ await api.delete(`/api/sessions/${id}`); sessions.value=sessions.value.filter(s=>s.id!==id); } },
            sendMessage, renderMarkdown, autoResize, formatDate, enableStream, toast, showPromptEditor, systemPrompts, activeSystemPromptId, activeSystemPrompt, 
            addNewSystemPrompt: async () => { const id = 'sp_'+Date.now(); const p = {id, name:'新预设', content:'...', is_public:0, sort_index: systemPrompts.value.length}; systemPrompts.value.push(p); activeSystemPromptId.value=id; await api.post('/api/prompts',p); },
            deleteSystemPrompt: async (id) => { if(confirm('删除？')){ try{ await api.delete(`/api/prompts/${id}`); systemPrompts.value=systemPrompts.value.filter(p=>p.id!==id); activeSystemPromptId.value=systemPrompts.value[0]?.id; }catch(e){showToast(e.message);} } },
            showCoT, randomInput, randomAll, themeLibs, canEditPrompt, showAuthModal, authMode, currentUser, authForm, handleAuth, logout, generateInviteCode,
            quickPasteConfig, applyQuickPaste, exportProfiles, importProfiles, exportCurrentSession, importSession, exportRpgModule, importRpgModule, copyRpgInfo: () => { navigator.clipboard.writeText(rpgPromptPreview.value).then(()=>showToast("已复制")); },
            copyMessage: (t) => { navigator.clipboard.writeText(t).then(()=>showToast("已复制")); },
            deleteMessage: (i) => { if(confirm('删除？')) currentSession.value.messages.splice(i,1); },
            editMessage: (i) => { if(currentSession.value.messages[i].role==='user'){ input.value=currentSession.value.messages[i].content; currentSession.value.messages=currentSession.value.messages.slice(0,i); nextTick(autoResize); } },
            regenerateMessage: (i) => { if(confirm('重发？')) { currentSession.value.messages=currentSession.value.messages.slice(0,i); callApi(); } },
            handleEnter: (e) => { if(!e.shiftKey) sendMessage(); },
            stopGeneration: () => { abortController?.abort(); isLoading.value=false; },
            addCoreMemory: () => { const m = prompt("注入:"); if(m) input.value+=`\n\n【指令：写入MTM：${m}】`; },
            importEngineTxt
        };
    }
}).mount('#app');
