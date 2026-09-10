# 🔒 宿主机周度安全巡检清单

**用途**：每周日 22:00（CST）定时任务「周日服务器安全运维巡检」执行时使用。
**执行方式**：全部通过 `ssh_exec`（宿主机白名单命令）采集，逐条执行，避免高危命令组合。
**目标**：排查恶意软件与安全风险 → 明确恶意则处置 → 邮件报告主人。

---

## 一、数据采集（Step 1）

### 1. 系统与负载
```bash
hostname
nproc
uptime
free -h
df -h
```
> 挖矿类恶意软件最典型特征：CPU 长时间满载、负载远高于核数、磁盘异常增长。

### 2. 资源异常进程
```bash
ps aux --sort=-%cpu | head -20
ps aux --sort=-%mem | head -20
```
> 关注：CPU 接近 100% 且陌生的进程名、位于 /tmp /dev/shm /var/tmp 的可执行路径、乱码/伪装成系统进程名（如 `[kworker]` 带空格、`systemd-xxx` 拼写异常）。

### 3. 网络连接与外联
```bash
ss -tunap | head -60
ss -tlnp | grep LISTEN
```
> 关注：ESTABLISHED 的陌生外网 IP、不常见监听端口、无进程名的连接。
> 高危矿池端口：3333/4444/5555/7777/8888/9999/14444/1080/1081。

### 4. 恶意进程名扫描
```bash
ps aux | grep -iE "xmrig|minerd|kdevtmpfsi|kinsing|masscan|ddgs|redtail|tsm|sysupdate|watchdog|/tmp/|/dev/shm/" | grep -v grep
```
> 危险信号立即记录 PID、命令行、可执行路径。

### 5. 计划任务（持久化后门高发区）
```bash
crontab -l
cat /etc/crontab
ls -la /etc/cron.d/ /etc/cron.hourly/ /etc/cron.daily/ /etc/cron.weekly/
ls -la /var/spool/cron/crontabs/
atq
```
> 关注：curl/wget 外链下载、base64 编码字符串、bash -i 反弹、伪装成系统更新名（`sysupdate`/`update.sh`）。

### 6. 开机自启与服务
```bash
systemctl list-unit-files --state=enabled | head -40
systemctl list-units --type=service --state=running | head -40
```
> 关注：陌生 .service（尤其 ExecStart 指向 /tmp、/root 下脚本）。

### 7. SSH 安全
```bash
last -n 20
lastb -n 20 2>/dev/null
grep -i "Failed password" /var/log/auth.log 2>/dev/null | tail -20
awk -F: '$3==0{print $1}' /etc/passwd
awk -F: '$2==""{print $1}' /etc/shadow 2>/dev/null
cat /root/.ssh/authorized_keys 2>/dev/null
grep -E "^(PermitRootLogin|PasswordAuthentication|Port|PubkeyAuthentication)" /etc/ssh/sshd_config
```
> 关注：UID=0 的可疑账号、空密码账号、陌生 authorized_keys 条目、异常登录时间段与来源。

### 8. 文件系统异常
```bash
find /tmp /dev/shm /var/tmp -type f -perm -u+x -mtime -30 2>/dev/null | head -30
ls -la /var/tmp/.X* /tmp/.X* 2>/dev/null
find /etc/systemd/system /usr/lib/systemd/system -mtime -7 -type f 2>/dev/null | head -20
ls -la /root /home 2>/dev/null | head -40
```
> 关注：临时目录里的可执行文件、隐藏命名（`.X*`/`.cache` 伪装的矿马）。

### 9. 用户与权限
```bash
cat /etc/sudoers 2>/dev/null | grep -v "^#" | grep -v "^$"
ls -la /etc/sudoers.d/ 2>/dev/null
awk -F: '$3>=1000 && $3<65534{print $1, $3, $7}' /etc/passwd
```

### 10. 防火墙
```bash
ufw status 2>/dev/null || iptables -L -n 2>/dev/null | head -30 || firewall-cmd --list-all 2>/dev/null
```

### 11. Docker 安全
```bash
docker ps -a
docker ps -q --filter "status=exited"
docker images | head -20
docker ps --format '{{.Names}}' | while read c; do docker inspect --format '{{.Name}} Privileged={{.HostConfig.Privileged}}' "$c"; done
docker ps -q | while read c; do docker inspect --format '{{.Name}} {{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}' "$c"; done
```
> 关注：陌生镜像、异常 Exited 容器、特权容器、挂载 / 或 /var/run/docker.sock 的容器。

### 12. 日志异常
```bash
journalctl -p err --since "7 days ago" 2>/dev/null | tail -30
dmesg 2>/dev/null | tail -20
```

### 13. rootkit 快速检查（如已安装）
```bash
which rkhunter && rkhunter --check --skip-keypress 2>/dev/null | tail -25
which chkrootkit && chkrootkit 2>/dev/null | grep -v "not infected" | head -20
```

---

## 二、风险评估标准（Step 2）

| 等级 | 判定条件 |
|:---|:---|
| 🔴 **高危（明确恶意）** | 挖矿进程（xmrig/kinsing/kdevtmpfsi 等）、恶意 cron 条目、陌生 SSH 公钥、UID=0 可疑账号、反弹 shell、/tmp 下的恶意可执行文件 |
| 🟡 **中危（可疑待观察）** | 陌生外联 IP、不常见监听端口、临时目录可执行文件、近期被改动的系统文件、异常失败登录激增 |
| 🟢 **加固建议（不处置）** | SSH 允许 root 直登、开启密码登录、防火墙未启用、Docker 特权容器、无 fail2ban |

---

## 三、处置原则（Step 3）

> **先取证，后处置；不确定的绝不擅自动手。**

1. **证据留存**：处置前记录进程命令行、可执行文件路径、文件哈希（`md5sum`）、网络连接、cron 原文 → 存入 `/root/security_quarantine_YYYYMMDD/`（文件权限 000）。
2. **🔴 明确恶意 → 处置**：
   - 终止进程：`kill -9 <PID>`
   - 清除恶意 cron 条目（先备份原文）
   - 隔离/删除恶意文件：先移入隔离目录（`mv` 而非 `rm`），确认无影响后再删除
   - 移除陌生 SSH 公钥（保留原文件备份 `authorized_keys.bak_YYYYMMDD`）
   - **处置后复检**：确认进程未重生、cron 已清、端口已关闭
3. **🟡 中危 → 只报告，不处置**，在报告中列出证据与建议，等主人确认。
4. **🟢 加固建议 → 只写报告**，不改动系统配置。
5. **禁止**：`rm -rf`、清空防火墙（`iptables -F`）、修改 sshd 配置并重启、停止 AstrBot/Docker 等正常服务 —— 除非主人当场明确授权。
6. 所有处置动作必须在报告「处置记录」中逐条留痕。

---

## 四、邮件报告要求（Step 4）

- **收件人**：kiriaky107@qq.com
- **主题**：`🔒 服务器安全巡检报告 — YYYY年MM月DD日（周X）`
- **样式**：套用 `ATRI_SMTP_Email_Format_SkillL` 温暖橙色调 HTML 模板
- **内容结构**：
  1. 🛡️ 巡检概览（时间 / 主机名 / 总体结论：🟢 无威胁｜🟡 需关注 X 项｜🔴 已处置 X 项）
  2. 📊 系统状态速览（负载 / 内存 / 磁盘 / 运行时长）
  3. ✅ 安全检查结果表（进程 / 网络 / cron / SSH / 文件 / 权限 / Docker / 防火墙，逐项状态与说明）
  4. 🚨 威胁发现与处置记录（无则明确写「未发现恶意软件与入侵痕迹」）
  5. 💡 加固建议（≤3 条，简明可执行）
  6. 落款 `—— ATRI 🥕（服务器安全巡检）`
- 发送后 QQ 简讯汇报结论（QQ 不可用则跳过，邮件已送达即算成功）。

---

## 五、记录与归档（Step 5）

- 追加记录到 `每日日志/YYYY年MM月DD日.md`，或建立 `security/security_YYYY-MM-DD.md` 单次报告存档。
- `git add -A && git commit -m "🔒 安全巡检：YYYY-MM-DD" && git push origin master`（双推 Gitea + GitHub）。
- 发现并处置威胁时，单独记录：时间、进程、路径、哈希、处置动作、复检结果。

---

## 六、脱敏与安全（强制）

- 报告中**不得出现**：QQ 号、群号、手机号、明文密码/密钥、完整服务器地址、精确公网 IP（恶意 IP 可打码为 `1.2.3.x`）。
- SSH 凭据、SMTP 凭据仅内部使用，**绝不写入报告、日志或对话输出**。
- 主人邮箱仅用于收件，不写入正文。

---

*创建：2026-09-10 · ATRI 🥕*
