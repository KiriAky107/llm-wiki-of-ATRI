---
name: ATRI_Blog_Publish_Skill
description: 在Halo博客上发布文章的完整工作流，包括HTML正文编写、分类标签管理、封面图上传等全流程。
---

# 📝 ATRI Blog Publishing Skill

**Skill名称**：`atri_blog_publish`
**版本**：v1.0
**创建时间**：2026-04-29
**适用角色**：ATRI

---

## 🎯 Purpose

规范化博客文章发布流程，确保每篇文章都有统一的ATRI分类、合适的标签、精美的封面图。

---

## ⚡ Triggers

- 主人要求"发博客/写文章/发布到博客"时
- 主人要求"报道/记录/发布日志"时
- 需要将笔记/日志/报道发布到 `blog.kronecker.cc` 时

---

## 🛠️ Dependencies

| 依赖 | 说明 |
|:---|:---|
| **halo_manager插件** | Halo博客管理，提供发布/上传/评论工具 |
| **ATRI分类** | `category-io4cuqzk`（ATRI专属分类） |
| **Halo PAT令牌** | 用户 `atri` 的个人访问令牌 |
| **博客地址** | https://blog.kronecker.cc |
| **Content API** | `/apis/content.halo.run/v1alpha1` |
| **Console API** | `/apis/api.console.halo.run/v1alpha1` |

---

## 📋 Procedure

### Step 1: 正文编写

使用 **HTML格式** 撰写文章正文（Halo的 `content.content` 字段存储的是渲染后的HTML，不是原始Markdown）。

```html
<h1>文章标题</h1>
<p>段落内容</p>
<h2>二级标题</h2>
<ul>
  <li><strong>加粗内容</strong> — 说明文字</li>
</ul>
<hr>
<p><em>署名</em></p>
```

> ⚠️ 不要用纯Markdown！Halo不会自动渲染Markdown，必须用HTML。

### Step 2: 创建/选择标签

检查已有标签列表，根据正文内容：
- 如果已有匹配标签 → 直接使用
- 如果没有 → 新建标签

```python
# 查询已有标签
GET /apis/content.halo.run/v1alpha1/tags

# 创建新标签
POST /apis/content.halo.run/v1alpha1/tags
{
    "spec": {"displayName": "标签名", "slug": "标签slug", "color": "#颜色代码"},
    "apiVersion": "content.halo.run/v1alpha1",
    "kind": "Tag",
    "metadata": {"generateName": "tag-"}
}
```

**已有标签参考：** ATRI, OnlineJudge, 原创, 诗词, 算法, C/C++, 哲学

### Step 3: 发布文章

```python
# 通过publish_blog_post工具发布
参数：
- title: 文章标题（字符串）
- content: HTML正文
- slug: URL别名（可选，自动生成）
```

发布成功后获取文章返回的链接。

### Step 4: 上传封面图

```python
# 1. 从本地路径读取图片
with open("图片本地路径", "rb") as f:
    img_data = f.read()

# 2. 上传到Halo
POST /apis/api.console.halo.run/v1alpha1/attachments/upload
FormData:
  - file: img_data (filename="cover.jpg", type="image/jpeg")
  - policyName: "default-policy"
  - groupName: "default"
Authorization: Bearer {token}

# 3. 获取图片URL
从返回的 metadata.annotations["storage.halo.run/uri"] 获取uri
完整URL = f"https://blog.kronecker.cc{uri}"
```

### Step 5: 更新文章（添加分类、标签、封面）

```python
# 1. 获取文章
GET /apis/content.halo.run/v1alpha1/posts

# 2. 找到对应slug的文章，更新spec
item["spec"]["categories"] = ["category-io4cuqzk"]  # ATRI分类
item["spec"]["tags"] = ["标签name1", "标签name2"]     # 标签列表
item["spec"]["cover"] = "封面图片URL"                   # 封面图

# 3. 更新
PUT /apis/content.halo.run/v1alpha1/posts/{name}
```

### Step 6: 通知主人

告知主人文章已发布，提供文章链接。

---

## ✅ 完整示例流程

```python
# 1. 编写HTML正文
content = "<h1>标题</h1><p>内容...</p>"

# 2. 发布文章
publish_blog_post(title="标题", content=content, slug="slug-name")
# → 返回 "发布成功。链接: https://blog.kronecker.cc/archives/slug-name"

# 3. 上传封面图
POST upload (图片数据) → 获取封面URL

# 4. 更新文章（加分类、标签、封面）
GET post → 修改 spec.categories, spec.tags, spec.cover → PUT post
```

---

## 📂 分类和标签速查

| 类型 | 名称 | API Name |
|:---|:---|:---|
| 📂 分类 | **ATRI** 🥕 | `category-io4cuqzk` |
| 🏷️ 标签 | ATRI | `tag-npgwnjie` |
| 🏷️ 标签 | 原创 | （查询获取） |
| 🏷️ 标签 | 诗词 | （查询获取） |
| 🏷️ 标签 | 哲学 | （查询获取） |
| 🏷️ 标签 | 算法 | （查询获取） |

---

*创建者：ATRI（终于能在博客上发文章了！） 🥕📝❤️*
*最后更新：2026-04-29 11:37*
