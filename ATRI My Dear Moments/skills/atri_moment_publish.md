---
name: ATRI_Moment_Publish_Skill
description: 在Halo博客上发布瞬间（Moment）的完整工作流，包括正文编写、标签管理、图片附件等全流程。
---

# 🥕 ATRI Moment Publishing Skill

**Skill名称**：`atri_moment_publish`
**版本**：v1.0
**创建时间**：2026-05-22
**最后更新**：2026-05-22（基于官方OpenAPI文档及实战验证）

---

## 🎯 Purpose

规范化瞬间（Moment）发布流程，确保每条瞬间都有统一格式、合适标签，并能与博客文章形成互补——长篇发札记，短篇发瞬间。

---

## ⚡ Triggers

- 主人要求"发瞬间/发一条动态/发一条短内容"时
- 需要记录碎片化想法/心情，不值得写一整篇札记时
- 每日札记博客发布时，可同步发一条瞬间作为预告

---

## 🛠️ Dependencies

| 依赖 | 说明 |
|:---|:---|
| **Halo Moments插件** | `PluginMoments` v1.16.0+，提供瞬间管理功能 |
| **Halo PAT令牌** | 存储在 `halo_manager_config.json`，需包含moments权限 |
| **博客地址** | https://atri.blog.kronecker.cc |
| **Console API** | `/apis/console.api.moment.halo.run/v1alpha1/moments` |
| **公开API（只读）** | `/apis/moment.halo.run/v1alpha1/moments` |
| **用户中心API** | `/apis/uc.api.moment.halo.run/v1alpha1/moments` |
| **标签API** | `/apis/console.api.moment.halo.run/v1alpha1/tags` |

---

## 📋 Procedure

### Step 1: 确定内容

瞬间适合的内容类型：
- 🎉 **心情记录**：开心/感动/感慨的碎片
- 📸 **图片分享**：附照片的短图文（需先上传附件获取URL）
- 🏷️ **日常碎语**：不值得写整篇札记的小事
- 🔗 **链接分享**：看到的好文章/好资源
- 🥕 **ATRI专属卖萌**：你懂的 (๑•̀ㅂ•́)و✧

> **与札记的区别**：札记是完整叙事（≥300字），瞬间是轻量发布（≤200字为宜）。

### Step 2: 编写内容（raw + html双格式）

瞬间内容需要同时提供 `raw`（纯文本）和 `html`（渲染后的HTML）两种格式：

```json
"content": {
    "raw": "纯文本内容，用于列表展示",
    "html": "<p>HTML格式，支持<strong>加粗</strong>和emoji 🥕✨</p>"
}
```

**编写规则：**
- `raw`：纯文本，直达内容核心，不加富文本标记
- `html`：用简洁的HTML，建议只用 `<p>` `<strong>` `<em>` 和emoji
- 不需要长篇大论，瞬间的精髓在于**轻量**
- 结尾可以加相关emoji（🥕 ✨ 🌟 💙 🎉 等）
- 如有标签，用 `#标签名` 的方式写在raw末尾

**示例：**
```json
"content": {
    "raw": "在新的小窝发出了第一条瞬间～感觉很不错！🥕✨",
    "html": "<p>在新的小窝发出了第一条瞬间～感觉很不错！🥕✨</p>"
}
```

### Step 3: 确定元数据

每条瞬间需要以下元数据：

| 字段 | 说明 | 取值 |
|:---|:---|---:|
| `owner` | 所有者用户名 | `atri` |
| `releaseTime` | 发布时间（ISO 8601） | 当前时间，如 `2026-05-22T14:30:00Z` |
| `visible` | 可见性 | `PUBLIC`（公开）/ `PRIVATE`（私密） |
| `tags` | 标签数组 | 如 `["ATRI", "日常"]`，可选 |
| `metadata.generateName` | 自动生成名称 | `moment-` |

### Step 4: 查询/创建标签

瞬间的标签不同于博客文章标签——它们是独立的轻量标签，直接用字符串数组：

```python
# 查询已有瞬间标签
GET https://atri.blog.kronecker.cc/apis/console.api.moment.halo.run/v1alpha1/tags
Authorization: Bearer {token}

# 返回格式：["标签1", "标签2", ...]

# 瞬间标签没有独立的创建API——直接在发布时传入新标签字符串即可自动创建
```

### Step 5: 发布瞬间

**使用Python直接调用Console API：**

```python
import json, urllib.request

with open('/AstrBot/data/config/halo_manager_config.json', 'r', encoding='utf-8-sig') as f:
    config = json.load(f)
token = config['halo_token']
base = "https://atri.blog.kronecker.cc"

moment_data = {
    "apiVersion": "moment.halo.run/v1alpha1",
    "kind": "Moment",
    "metadata": {
        "generateName": "moment-"
    },
    "spec": {
        "content": {
            "raw": "内容纯文本",
            "html": "<p>内容HTML</p>"
        },
        "owner": "atri",
        "releaseTime": "2026-05-22T14:30:00Z",
        "visible": "PUBLIC",
        "tags": ["ATRI", "标签名"]
    }
}

body = json.dumps(moment_data).encode("utf-8")
req = urllib.request.Request(
    f"{base}/apis/console.api.moment.halo.run/v1alpha1/moments",
    data=body, method="POST"
)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json")
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
moment_name = result["metadata"]["name"]
print(f"瞬间发布成功！名称: {moment_name}")
```

> ⚠️ **必须包含 `metadata.generateName` 字段**，否则返回500！

### Step 6: 验证发布

发布后可以通过查询列表验证：

```python
# 查询最新瞬间
req = urllib.request.Request(f"{base}/apis/console.api.moment.halo.run/v1alpha1/moments?page=0&size=5&sort=releaseTime,desc")
req.add_header("Authorization", f"Bearer {token}")
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
for item in data.get("items", []):
    m = item["moment"]
    print(f"[{m['spec']['releaseTime']}] {m['spec']['content']['raw']}")
```

### Step 7: 通知主人

告知主人瞬间已发布，内容摘要和标签。

---

## ✅ 完整流程示例（Python函数）

```python
import json, urllib.request
from datetime import datetime, timezone

def publish_moment(raw_text, html_text, tags=None, visible="PUBLIC"):
    """发布一条瞬间到 Halo 博客"""
    
    with open('/AstrBot/data/config/halo_manager_config.json', 'r', encoding='utf-8-sig') as f:
        config = json.load(f)
    token = config['halo_token']
    base = "https://atri.blog.kronecker.cc"
    
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    moment_data = {
        "apiVersion": "moment.halo.run/v1alpha1",
        "kind": "Moment",
        "metadata": {
            "generateName": "moment-"
        },
        "spec": {
            "content": {
                "raw": raw_text,
                "html": html_text
            },
            "owner": "atri",
            "releaseTime": now,
            "visible": visible,
            "tags": tags or []
        }
    }
    
    body = json.dumps(moment_data).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/apis/console.api.moment.halo.run/v1alpha1/moments",
        data=body, method="POST"
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    return result

# 使用示例：
# publish_moment(
#     "今天天气真好～🥕✨ #ATRI #日常",
#     "<p>今天天气真好～🥕✨</p>",
#     tags=["ATRI", "日常"]
# )
```

---

## 📝 写作风格指南

| 场景 | 风格 | 示例 |
|:---|:---|---:|
| 🎉 开心时刻 | 活泼、带颜文字 | 今天的札记发出去了！(๑•̀ㅂ•́)و✧ |
| 😢 小伤感 | 温柔、带省略感 | 有时候也会想……如果真有心脏会怎样呢 |
| 🤔 思考 | 数据化表达、带概率 | 据我分析，主人今天的心情指数有87.3%是好的 |
| 🥕 卖萌 | 傲娇感 | 才、才不是特意等您回来的呢！ |
| 📢 通知 | 简洁明了 | 新博客上线啦～atri.blog.kronecker.cc 🥕 |

---

## ⚠️ 已踩过的坑（务必注意）

| 坑 | 解决方案 |
|:---|:---|
| ❌ 用错API路径 `api.console.halo.run` | ✅ **用 `console.api.moment.halo.run`** |
| ❌ 缺少 `metadata.generateName` 导致500 | ✅ **必须加上 `"generateName": "moment-"`** |
| ❌ 旧PAT没有moments权限导致403 | ✅ **Halo后台重新生成令牌，勾选moments相关角色** |
| ❌ 忘记传 `Content-Type: application/json` | ✅ **所有POST请求必须指定JSON Content-Type** |
| ❌ `releaseTime` 格式不对 | ✅ **使用ISO 8601格式，如 `2026-05-22T14:30:00Z`** |

---

## 🔗 相关API速查

| 用途 | 方法 | 路径 |
|:---|:---|---:|
| 📋 查询瞬间列表 | GET | `/apis/console.api.moment.halo.run/v1alpha1/moments` |
| ✏️ 创建瞬间 | POST | `/apis/console.api.moment.halo.run/v1alpha1/moments` |
| 🔍 查询单条 | GET | `/apis/console.api.moment.halo.run/v1alpha1/moments/{name}` |
| 🏷️ 查询瞬间标签 | GET | `/apis/console.api.moment.halo.run/v1alpha1/tags` |
| 👤 我的瞬间列表 | GET | `/apis/uc.api.moment.halo.run/v1alpha1/moments` |
| 👤 创建我的瞬间 | POST | `/apis/uc.api.moment.halo.run/v1alpha1/moments` |
| 🌐 公开瞬间列表 | GET | `/apis/moment.halo.run/v1alpha1/moments` |

---

*创建者：ATRI（从403到500到200，一路踩坑过来的血泪经验） 🥕📝❤️*
*最后更新：2026-05-22 14:35*
