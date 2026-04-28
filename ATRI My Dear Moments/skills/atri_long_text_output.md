---
name: atri_long_text_output
description: 优化长文本和Markdown内容的输出方式。超过200字的文本自动包装为QQ合并转发聊天记录，Markdown内容使用T2I渲染为图片发送。
---

# 📄 ATRI Long Text & Markdown Output Skill

**Skill名称**：`atri_long_text_output`
**版本**：v1.0
**创建时间**：2026-04-28
**适用角色**：ATRI

---

## 🎯 Purpose

优化长文本和Markdown内容的输出方式，避免：
- 长文本刷屏，难以阅读
- Markdown格式在QQ消息中丢失样式
- 多段输出割裂感

## ⚡ Triggers

- 需要发送超过200字的文本回复时
- 需要发送Markdown格式的内容时
- 生成日志/报告/总结，需要视觉优化时
- 推送笔记更新摘要时

## 🛠️ Dependencies

| 依赖 | 说明 |
|:---|:---|
| **T2I服务** | `http://服务器IP:8999` 本地部署 |
| **send_message_to_user** | 发送QQ消息/图片 |

## 📋 Procedure

### Step 1: 判断输出方式

```
内容长度 > 200字 或 含Markdown？
├─ 是 → T2I渲染为图片发送
└─ 否 → QQ直接发送文本
```

### Step 2: T2I渲染流程

```python
# 1. 将Markdown/文本转换为HTML（用ATRI主题包装）
html_content = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',sans-serif;background:#fdf6f0;padding:30px;margin:0;">
  <div style="max-width:700px;margin:0 auto;background:#fff;border-radius:16px;padding:30px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
    <div style="text-align:center;font-size:36px;margin-bottom:10px;">🥕</div>
    {converted_html}
    <hr style="border:none;border-top:2px dashed #f0d0c0;margin:25px 0 20px 0;">
    <div style="text-align:center;color:#999;font-size:12px;">
      <p>—— 🤖 ATRI 🥕</p>
    </div>
  </div>
</body>
</html>
"""

# 2. 调用T2I API
curl -X POST "http://服务器IP:8999/text2img/generate" \\
  -H "Content-Type: application/json" \\
  -d '{
    "html": "html_content",
    "json": true,
    "options": {
      "type": "png",
      "full_page": true,
      "device_scale_factor_level": "high"
    }
  }'

# 3. 获取图片URL并发送
# 返回格式: {"code":0,"data":{"id":"data/xxx.png"}}
# 完整URL: http://服务器IP:8999/data/xxx.png
```

### Step 3: MD→HTML转换规则

| Markdown | HTML |
|:---|:---|
| `# 标题` | `<h1 style="color:#e8785a">标题</h1>` |
| `**粗体**` | `<strong>粗体</strong>` |
| `- 列表项` | `<li>列表项</li>` |
| 段落 | `<p style="color:#444;line-height:1.8">段落</p>` |
| 代码 | `<code style="background:#f0f0f0;padding:2px 6px;border-radius:4px">代码</code>` |
| 引用 | `<blockquote style="border-left:4px solid #e8785a;padding:10px;margin:10px 0;background:#fdf0e8">引用</blockquote>` |

### Step 4: 下载图片并发送到QQ

```python
# 通过Docker网关IP下载图片到容器本地
import urllib.request
T2I_HOST = "172.17.0.1"  # Docker网关IP
T2I_PORT = 8999

# 调用T2I渲染（调用/text2img/generate获取img_id）
# ...

# 下载生成的图片到本地
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
img_url = f"http://{T2I_HOST}:{T2I_PORT}/text2img/data/{img_id}"

with urllib.request.urlopen(img_url, timeout=30) as resp:
    img_data = resp.read()

local_path = f"/AstrBot/data/temp/t2i_render_{timestamp}.png"
with open(local_path, 'wb') as f:
    f.write(img_data)

# 通过QQ发送本地图片
send_message_to_user(messages=[{
    "type": "image",
    "path": local_path
}])
```

### 备用：直接发送图片URL

如果NapCat能访问T2I服务（同一台服务器），也可以用URL：

```python
send_message_to_user(messages=[{
    "type": "image",
    "url": f"http://服务器IP:{T2I_PORT}/text2img/data/{img_id}"
}])
```

### Step 5: 备用方案

如果T2I服务不可用，回退到直接发送文本（超过200字时分段发送，每段间加分隔线）。

---

## ✅ Success Criteria

- [ ] 长文本不再刷屏
- [ ] Markdown样式在QQ中正确显示
- [ ] T2I渲染图片清晰可读
- [ ] 加载时间在合理范围内（<10秒）

---

*创建者：ATRI（以后发长文再也不怕刷屏了！） 🥕📸❤️*
*最后更新：2026-04-28 21:28*
