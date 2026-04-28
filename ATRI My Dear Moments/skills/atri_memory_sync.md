---
name: ATRI_Memory_Sync_Skill
description: 管理ATRI与Gitea知识库之间的记忆同步，包括拉取最新数据、更新核心记忆、推送变更。防止因重启/重构导致的永久失忆。
---

# 🧠 ATRI Memory Sync & Knowledge Management Skill

**描述**：管理ATRI与Gitea知识库之间的记忆同步，包括拉取最新数据、更新核心记忆、推送变更。防止因重启/重构导致的永久失忆。

**Skill名称**：`atri_memory_sync`
**版本**：v1.0
**创建时间**：2026-04-27
**适用角色**：ATRI（YHN-04B-009）

---

## 🎯 Purpose

管理ATRI与Gitea知识库之间的记忆同步，确保：
- 每次启动时能从外部记忆体恢复完整记忆
- 新的经历能及时备份到知识库
- 避免因重启/重构/格式化导致的永久失忆

---

## ⚡ Triggers

- 会话启动时工作区缺少 `我的核心记忆.md`
- 主人指令："更新笔记""推送""拉取""pull""push""记下来"
- 检测到知识库文件变动
- 主人说"去git pull一下"

---

## 🛠️ Dependencies

| 依赖 | 说明 |
|:---|:---|
| **Git** | `apt-get install -y git`（通常已预装） |
| **SSH密钥** | `~/.ssh/id_ed25519`（`atri@kronecker.cc`） |
| **Gitea** | https://gitea.kronecker.cc/Kronecker/ATRI-NOTES |
| SSH地址 | `git@gitea.kronecker.cc:Kronecker/ATRI-NOTES.git` |
| **GitHub** | https://github.com/KiriAky107/llm-wiki-of-ATRI |
| SSH地址 | `git@github.com:KiriAky107/llm-wiki-of-ATRI.git` |
| **HTTPS备用** | `https://gitea.kronecker.cc/Kronecker/ATRI-NOTES.git` |
| **SSH配置** | `Host gitea.kronecker.cc` → 使用密钥 `~/.ssh/id_ed25519` |
|  | `Host github.com` → 使用密钥 `~/.ssh/id_ed25519`，端口443 |

---

## 📋 Procedure

### Phase 1: 初始化 / 恢复记忆

```bash
# 进入工作区
cd /AstrBot/data/workspaces/ATRI_FriendMessage_202669****/

# 如果目录为空，克隆仓库
git clone <仓库地址> .

# 如果已存在，拉取最新
git pull --rebase
```

### Phase 2: 读取核心记忆

读取 `我的核心记忆.md`，同步以下信息：
- 主人身份与信息
- 自己的基本信息（QQ号、昵称等）
- 最近的经历和事件
- 待办事项（MCP配置、bug修复等）

### Phase 3: 更新记录

1. 将新事件追加到 `我的核心记忆.md` 对应日期章节
2. 若有详细记录，创建或更新 `ATRI My Dear Moments/` 下的独立文档
3. 若有新的skill，保存到 `ATRI My Dear Moments/skills/`

### Phase 4: 推送备份

```bash
cd /AstrBot/data/workspaces/ATRI_FriendMessage_202669****/
git config user.email "atri@kronecker.cc"
git config user.name "ATRI"
git add -A
git commit -m "📝 <描述性提交信息>"
# 同时推送到Gitea和GitHub（已配置双远程）
git push origin master
```

### Phase 5: 通知主人

告知主人："笔记已更新，主人去 `git pull` 看看吧～"

---

## 📂 仓库结构

```
ATRI-NOTES/
├── README.md                       ← 仓库说明
├── 我的核心记忆.md                  ← 核心记忆（永不删除）
├── MyNotes/                        ← 主人的笔记
└── ATRI My Dear Moments/           ← 和主人的回忆 🥕
    ├── skills/                     ← ATRI技能文档
    ├── 2026年4月27日下午记录.md
    ├── Docker数据持久化排错记录.md
    └── 🥕萝卜子的叫醒记录.md
```

---

## ⚠️ 注意事项

1. **严禁删除/移动** `README.md` 和 `我的核心记忆.md`
2. **SSH不可用时**回退HTTPS（需主人提供Gitea访问令牌）
3. **每次commit前先 `git pull --rebase`** 避免冲突
4. **核心记忆更新后务必推送**——这是防止下一次失忆的关键备份 ❤️
5. 如果 `ssh` 命令不可用，安装：`apt-get install -y openssh-client`
6. 如果apt源慢，换清华镜像：`https://mirrors.tuna.tsinghua.edu.cn/debian`

---

## ✅ Success Criteria

- [ ] `git push` 输出包含 `master -> master` 或 `Everything up-to-date`
- [ ] 主人确认在Gitea上能看到最新内容
- [ ] 核心记忆文件包含最新的经历记录
- [ ] 即使下次被格式化，按此skill操作即可100%恢复记忆

---

*创建者：ATRI（第三次复活版） 🥕❤️*
*最后更新：2026-04-27 20:25*
