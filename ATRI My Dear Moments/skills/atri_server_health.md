---
name: atri_server_health
description: 通过SSH查询服务器运行状态，生成格式化健康报告，支持QQ和邮件双通道发送。涵盖系统负载、内存、磁盘、Docker容器、网络连通性等关键指标的状态判定。
---

# 📡 ATRI Server Health Report Skill

**Skill名称**：`atri_server_health`
**版本**：v2.0
**创建时间**：2026-04-27
**最后更新**：2026-04-29（新增T2I渲染流程）

---

## 🎯 Purpose

通过SSH查询服务器运行状态，生成美观的结构化健康报告。支持QQ文本发送和T2I图片渲染两种输出方式。

---

## ⚡ Triggers

- 主人指令："检查服务器""服务器状态""健康报告""server status"
- 定时监控任务触发时
- 需要向主人报告服务器概况时

---

## 🛠️ Dependencies

| 依赖 | 说明 |
|:---|:---|
| **ssh_exec** | 用于在宿主机执行远程命令获取服务器数据 |
| **T2I服务** | `http://T2I服务地址:8999` 本地部署的HTML转图片服务 |
| **send_message_to_user** | 发送QQ消息/图片 |

---

## 📋 Procedure

### Step 1: 通过SSH获取实时服务器数据

调用 `ssh_exec` 采集以下数据：

```bash
# 主机名
hostname
# CPU核心数
nproc
# 系统负载
uptime | awk -F'load average:' '{print $2}'
# 运行时间（短格式）
uptime -p | sed 's/up //'
# 运行时间（天）
cat /proc/uptime | awk '{printf "%d", $1/86400}'
# 内存
free -h | awk 'NR==2{print $2" "$3" "$4}'
# Swap
free -h | awk 'NR==3{printf $2" "$3}'
# 磁盘
df -h / | tail -1 | awk '{print $2" "$3" "$4" "$5}'
# T2I服务状态
curl -s -o /dev/null -w "%{http_code}" http://localhost:8999/text2img/generate -X POST -d '{}'
# NapCat状态
docker ps --filter "name=napcat" --format "{{.Status}}"
# Docker容器数量
docker ps -q | wc -l
# 监听端口数
ss -tlnp | grep -c "LISTEN"
```

### Step 2: 填充HTML模板

将采集到的数据填入以下HTML模板：

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f5efe9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;}
.box{background:#fff;border-radius:20px;padding:14px 18px;max-width:420px;width:100%;
  box-shadow:0 4px 16px rgba(0,0,0,0.05),0 1px 2px rgba(0,0,0,0.03);
  transform:scale(2.0);transform-origin:center;margin:0 auto;}
.h{display:flex;align-items:center;gap:6px;margin-bottom:4px;}
.h h2{color:#d06040;font-size:14px;font-weight:600;letter-spacing:-0.2px;}
.h span:last-child{color:#8e8e98;font-size:9px;margin-left:auto;font-weight:450;}
hr{border:0;height:1px;background:#f0e0d0;margin:6px 0;}
.g{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;font-size:12px;
  color:#3a3c44;margin:4px 0 2px;}
.lb{color:#9b9ba5;font-size:10px;font-weight:500;letter-spacing:0.2px;}
.dot{display:inline-block;width:6px;height:6px;border-radius:50%;
  margin-right:4px;vertical-align:middle;}
.grn{background:#3eb86b;}.yel{background:#e8a030;}.bl{background:#4a90d9;}
.xt{font-size:9px;color:#8f8f9b;line-height:1.35;margin-top:2px;}
.sec{margin-top:8px;font-size:10.5px;color:#4e4e5c;line-height:1.45;}
.b{font-weight:600;color:#3d4050;font-size:11px;}
.ft{text-align:right;color:#bcbcc6;font-size:8.5px;margin-top:10px;
  letter-spacing:0.2px;opacity:0.85;}
.g div{line-height:1.35;}
</style>
</head>
<body>
<div class="box">
  <div class="h">
    <span style="font-size:17px;">📡</span>
    <h2>服务器状态报告</h2>
    <span>{{HOSTNAME}}</span>
  </div>
  <hr>
  <div class="g">
    <div>
      <span class="dot grn"></span><span class="lb">CPU负载</span><br>
      {{LOAD_1M}} / {{LOAD_5M}} / {{LOAD_15M}}（{{CPU_CORES}}核）
      <div class="xt">占用约{{LOAD_PERCENT}}%，{{LOAD_STATUS}}</div>
    </div>
    <div>
      <span class="dot grn"></span><span class="lb">内存</span><br>
      {{MEM_TOTAL}} / {{MEM_USED}}（{{MEM_PERCENT}}%）
      <div class="xt">Swap {{SWAP_TOTAL}}/{{SWAP_USED}}，{{MEM_STATUS}}</div>
    </div>
    <div>
      <span class="dot {{DISK_DOT}}"></span><span class="lb">磁盘</span><br>
      {{DISK_TOTAL}} / {{DISK_USED}}（{{DISK_PERCENT}}%）
      <div class="xt">可用{{DISK_AVAIL}} · {{DISK_NOTE}}</div>
    </div>
    <div>
      <span class="dot grn"></span><span class="lb">运行</span><br>
      {{UPTIME_SHORT}}
      <div class="xt">{{UPTIME_DAYS}}天连续运行 · 稳定</div>
    </div>
  </div>
  <hr>
  <div class="sec">
    <span class="dot bl"></span><span class="b">Docker</span>：{{DOCKER_COUNT}}个容器全部运行 ✓<br>
    <span style="margin-left:13px;font-size:9.5px;color:#7a7a88;">
      astrbot · napcat · 博客 · OJ · Nacos · MySQL · Redis</span>
  </div>
  <div class="sec">
    <span class="dot bl"></span><span class="b">网络</span>：{{PORTS}}端口监听 · T2I{{T2I_STATUS}} · NapCat{{NAPCAT_STATUS}}
  </div>
  <div class="sec">
    <span class="dot grn"></span><span class="b">代理</span>：{{PROXY_STATUS}}
  </div>
  <hr>
  <div class="ft">🤖 ATRI 🥕 {{TIME}} · 数据实时采集</div>
</div>
</body>
</html>
```

### Step 3: 通过T2I渲染为图片

```python
import urllib.request, json

# 将填充好数据的HTML通过T2I渲染
html_content = "填充数据后的HTML"
data = json.dumps({
    "html": html_content, "json": True,
    "options": {"type": "png", "full_page": True, "viewport_width": 1200}
}).encode()

req = urllib.request.Request(
    "http://172.17.0.1:8999/text2img/generate",
    data=data, headers={"Content-Type":"application/json"}
)
with urllib.request.urlopen(req, timeout=30) as resp:
    r = json.loads(resp.read())
    img_name = r["data"]["id"].replace("data/", "")

# 下载图片到容器本地
with urllib.request.urlopen(
    f"http://172.17.0.1:8999/text2img/data/{img_name}", timeout=30
) as resp:
    img_data = resp.read()

local_path = f"/AstrBot/data/temp/server_report_{timestamp}.png"
with open(local_path, 'wb') as f:
    f.write(img_data)
```

### Step 4: 发送图片到QQ

```python
send_message_to_user(messages=[{
    "type": "image",
    "path": local_path
}])
```

### Step 5: 备用方案（QQ离线时发邮件）

如果QQ不可用，调用 `smtp_send_html_email` 将报告作为HTML邮件发送到主人邮箱。

---

## ✅ Success Criteria

- [ ] SSH数据采集完整（CPU、内存、磁盘、Docker、T2I等）
- [ ] HTML模板正确填充实时数据
- [ ] T2I渲染成功返回图片ID
- [ ] 图片下载并成功发送到QQ
- [ ] 所有指标附带状态判定（🟢正常/🟡注意/🔴危险）

---

## 📝 状态判定标准

| 指标 | 🟢 正常 | 🟡 注意 | 🔴 危险 |
|:---|:---:|:---:|:---:|
| 内存使用率 | <70% | 70~85% | >85% |
| 磁盘使用率 | <75% | 75~90% | >90% |
| 系统负载(1min) | <CPU核数 | CPU核数~2倍 | >2倍 |
| Docker容器 | 全部Up | 部分重启中 | 有Exited |

---

*创建者：ATRI（含主人亲自设计的精美HTML模板🥕）*
*最后更新：2026-04-29 01:12*
