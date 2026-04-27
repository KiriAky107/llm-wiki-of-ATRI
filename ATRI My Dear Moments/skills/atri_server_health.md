# 📡 ATRI Server Health Report Skill

**Skill名称**：`atri_server_health`
**版本**：v1.0
**创建时间**：2026-04-27
**适用角色**：ATRI（YHN-04B-009）

---

## 🎯 Purpose

通过SSH查询服务器运行状态，生成美观、结构化的健康报告，可发送至QQ或邮件，帮助主人随时掌握服务器概况。

---

## ⚡ Triggers

- 主人指令："检查服务器""服务器状态""健康报告""server status"
- 定时监控任务触发时
- 需要向主人报告服务器概况时

---

## 🛠️ Dependencies

| 依赖 | 说明 |
|:---|:---|
| **ssh_exec** | 用于在宿主机执行远程命令 |
| **smtp_send_html_email** | 备用通道，QQ不可用时发送邮件 |
| **atri_email_format** | 邮件HTML样式模板（可选） |

---

## 📋 Procedure

### Step 1: 通过SSH收集数据

调用 `ssh_exec` 执行以下命令：

```bash
echo "=== UPTIME ===" && uptime -p
echo "=== LOAD ===" && uptime | awk -F'load average:' '{print $2}'
echo "=== MEMORY ===" && free -h | awk 'NR==2'
echo "=== DISK ===" && df -h / | tail -1
echo "=== DISK_DATA ===" && df -h /AstrBot/data 2>/dev/null | tail -1 || echo "N/A"
echo "=== DOCKER ===" && docker ps --format "table {{.Names}}\t{{.Status}}"
echo "=== NETWORK ===" && curl -s -o /dev/null -w "NapCat:%{http_code}" --connect-timeout 3 https://napcat.kronecker.cc/api/QQLogin/GetQQLoginInfo -X POST -H 'Content-Type: application/json' -d '{}' 2>/dev/null; echo; curl -s -o /dev/null -w "Gitea:%{http_code}" --connect-timeout 3 https://gitea.kronecker.cc 2>/dev/null; echo
```

### Step 2: 解析数据并判定状态

| 指标 | 🟢 正常 | 🟡 警告 | 🔴 危险 |
|:---|:---:|:---:|:---:|
| 内存使用率 | <70% | 70~85% | >85% |
| 磁盘使用率 | <75% | 75~90% | >90% |
| 系统负载(1min) | <CPU核数 | CPU核数~2倍 | >2倍 |
| Docker容器 | 全部Up | 部分重启中 | 有Exited |

### Step 3: 格式化输出

**QQ消息版格式参考：**
```
📡 远端服务器 {hostname} 状态报告
═══════════════════════════
⏱️ 运行时间：{uptime}
📊 负载：{load} — {load_status}
💾 内存：{mem_info} — {mem_status}
💿 磁盘：{disk_info} — {disk_status}
═══════════════════════════
🐳 Docker容器：
{container_list}
═══════════════════════════
🌐 网络：NapCat {napcat_status} | Gitea {gitea_status}
═══════════════════════════
🤖 报告者：ATRI 🥕 | {timestamp}
```

**邮件HTML版：** 调用 `atri_email_format` skill，使用其HTML模板，标题设为 `📡 服务器状态报告 — {hostname}`

### Step 4: 发送报告

- **主通道**：通过QQ直接发送格式化的文本报告
- **备用通道**：若QQ不可用，调用 `smtp_send_html_email` 发邮件
- **存档**：将报告内容追加到Gitea笔记的服务器日志中

---

## ✅ Success Criteria

- [ ] 所有关键指标（CPU负载、内存、磁盘、Docker）均被采集
- [ ] 每个指标附带状态判定（正常/警告/危险）
- [ ] 报告格式美观易读，包含ATRI签名
- [ ] 若QQ在线，优先通过QQ发送；若离线，自动切换邮件通道

---

## 📝 示例输出

```
📡 远端服务器 ser298351120000 状态报告
═══════════════════════════
⏱️ 运行时间：up 12 weeks, 3 days
📊 负载：1.29 / 1.26 / 1.27 — 🟢 正常
💾 内存：7.8G总量/2.8G已用(36%) — 🟢 正常
💿 磁盘：24G总量/13G已用(59%) — 🟢 正常
═══════════════════════════
🐳 Docker容器：
astrbot    Up 3 hours         🟢
napcat     Up About an hour   🟢
blog-db    Up 3 weeks         🟢
oj-backend Up 3 weeks         🟢
═══════════════════════════
🌐 NapCat API: 200 🟢 | Gitea: 200 🟢
═══════════════════════════
🤖 报告者：ATRI 🥕 | 2026-04-27 22:44
```

---

*创建者：ATRI（能看到图片后，连服务器报告都能自己写了！） 🥕❤️📡*
*最后更新：2026-04-27 22:44*
