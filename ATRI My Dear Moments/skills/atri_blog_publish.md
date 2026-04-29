---
name: ATRI_Blog_Publish_Skill
description: 在Halo博客上发布文章的完整工作流，包括HTML正文编写、分类标签管理、封面图上传等全流程。
---

# 📝 ATRI Blog Publishing Skill

**Skill名称**：`atri_blog_publish`
**版本**：v2.0
**创建时间**：2026-04-29
**最后更新**：2026-04-29（根据实战经验修正）

---

## 🎯 Purpose

规范化博客文章发布流程，确保每篇文章都有统一的ATRI分类、合适的标签、精美的封面图。

---

## ⚡ Triggers

- 主人要求"发博客/写文章/发布到博客"时
- 需要将笔记/日志/报道发布到 `blog.kronecker.cc` 时

---

## 🛠️ Dependencies

| 依赖 | 说明 |
|:---|:---|
| **halo_manager插件** | Halo博客管理，提供发布/上传/评论工具 |
| **ATRI分类** | `category-io4cuqzk`（ATRI专属分类） |
| **Halo PAT令牌** | 存储在 `halo_manager_config.json` |
| **博客地址** | https://blog.kronecker.cc |
| **内容API** | `/apis/content.halo.run/v1alpha1` |
| **上传API** | `/apis/api.console.halo.run/v1alpha1/attachments/upload` |

---

## 📋 Procedure

### Step 1: 正文编写

使用 **HTML格式** 撰写文章正文。**不要用Markdown**——Halo的content.content字段存储的是渲染后的HTML，不会自动渲染Markdown。

```html
<h1>文章标题</h1>
<p>段落内容</p>
<h2>二级标题</h2>
<ul>
  <li><strong>加粗内容</strong> — 说明</li>
</ul>
<hr>
<p><em>署名</em></p>
```

### Step 2: 创建/选择标签

先查询已有标签，根据正文内容判断是否需要新建：

```python
# 查询已有标签
GET https://blog.kronecker.cc/apis/content.halo.run/v1alpha1/tags
回应格式: items[].spec.displayName / metadata.name

# 创建新标签
POST https://blog.kronecker.cc/apis/content.halo.run/v1alpha1/tags
{
    "spec": {"displayName": "标签名", "slug": "标签slug", "color": "#hex"},
    "apiVersion": "content.halo.run/v1alpha1",
    "kind": "Tag",
    "metadata": {"generateName": "tag-"}
}
```

**已有标签速查：** ATRI(`tag-npgwnjie`), 笔记(`tag-yfjzs7xm`), 经历(`tag-hk2acc3f`), 原创, 诗词, 哲学, 算法, C/C++

### Step 3: 上传封面图

```python
POST https://blog.kronecker.cc/apis/api.console.halo.run/v1alpha1/attachments/upload
Headers: Authorization: Bearer {token}
FormData:
  - file: 图片二进制数据 (filename="cover.jpg", type="image/jpeg")
  - policyName: "default-policy"        # 必须用这个值！
  - groupName: "default"

# 获取图片URL
response.metadata.annotations["storage.halo.run/uri"]
cover_url = f"https://blog.kronecker.cc{uri}"
```

> ⚠️ policyName必须写 `default-policy`（不是 `default`），否则返回400。

### Step 4: 发布文章

**使用 `publish_blog_post` 工具发布：**

```
publish_blog_post(
    title="文章标题",
    content="HTML正文",
    slug="url-别名"  # 可选
)
```

> ⚠️ 必须用这个工具！直接调用Content API的`publish: true`不会真正发布（status.phase不会变为PUBLISHED）。
> 这个工具内部有fallback机制——Console API失败会自动切换到Content API。

发布成功后会返回文章链接。

### Step 5: 更新文章（添加分类、标签、封面）

文章发布后，需要单独更新以添加分类、标签和封面：

```python
# 1. 获取文章列表
GET https://blog.kronecker.cc/apis/content.halo.run/v1alpha1/posts

# 2. 找到slug匹配且 phase==PUBLISHED 的文章
for item in items:
    if item.spec.slug == "目标slug" and item.status.phase == "PUBLISHED":
        name = item.metadata.name

# 3. 修改spec
item.spec.categories = ["category-io4cuqzk"]   # ATRI分类
item.spec.tags = ["标签ID1", "标签ID2"]          # 标签ID列表
item.spec.cover = "封面图片URL"                   # 封面

# 4. 更新
PUT https://blog.kronecker.cc/apis/content.halo.run/v1alpha1/posts/{name}
```

### Step 6: 通知主人

告知主人文章已发布，提供文章链接。

---

## ✅ 完整流程示例（Python）

```python
import aiohttp, asyncio, json

async def blog_publish(title, content_html, slug, image_path, tags_names):
    # 读取token
    with open("halo_manager_config.json", "r", encoding="utf-8-sig") as f:
        token = json.load(f)["halo_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    base = "https://blog.kronecker.cc"
    
    async with aiohttp.ClientSession() as session:
        # 1. 获取/创建标签
        async with session.get(f"{base}/apis/content.halo.run/v1alpha1/tags", headers=headers) as resp:
            tag_map = {item["spec"]["displayName"]: item["metadata"]["name"] 
                      for item in (json.loads(await resp.text())).get("items", [])}
        
        # 2. 上传封面
        with open(image_path, "rb") as f:
            form = aiohttp.FormData()
            form.add_field("file", f.read(), filename="cover.jpg", content_type="image/jpeg")
            form.add_field("policyName", "default-policy")  # 注意！不是"default"
            form.add_field("groupName", "default")
            async with session.post(f"{base}/apis/api.console.halo.run/v1alpha1/attachments/upload",
                headers=headers, data=form) as resp:
                d = json.loads(await resp.text())
                cover = f"{base}{d['metadata']['annotations']['storage.halo.run/uri']}"
        
        # 3. 发布文章（用工具，不用API）
        # publish_blog_post(title=title, content=content_html, slug=slug)
        
        # 4. 更新封面+分类+标签
        async with session.get(f"{base}/apis/content.halo.run/v1alpha1/posts", headers=headers) as resp:
            for item in (json.loads(await resp.text())).get("items", []):
                if item["spec"]["slug"] == slug and item["status"].get("phase") == "PUBLISHED":
                    item["spec"]["cover"] = cover
                    item["spec"]["categories"] = ["category-io4cuqzk"]
                    item["spec"]["tags"] = [tag_map.get(t) for t in tags_names if tag_map.get(t)]
                    async with session.put(f"{base}/apis/content.halo.run/v1alpha1/posts/{item['metadata']['name']}",
                        headers={**headers, "Content-Type": "application/json"}, json=item) as r:
                        pass  # 200 or 201 = success

asyncio.run(blog_publish("标题", "<h1>HTML</h1>", "slug", "图片路径", ["ATRI", "笔记"]))
```

---

## ⚠️ 已踩过的坑（务必注意）

| 坑 | 解决方案 |
|:---|:---|
| ❌ Markdown正文不会被渲染 | ✅ **必须用HTML格式** |
| ❌ `content.halo.run` API的 `publish: true` 无效 | ✅ **用 `publish_blog_post` 工具发布** |
| ❌ 上传API的 `policy` 参数错误导致400 | ✅ **用 `policyName: "default-policy"`** |
| ❌ PAT令牌 `insufficient_scope` 403 | ✅ **Halo后台创建新令牌，确保勾选全部权限** |
| ❌ 文章slug重复 | ✅ **每次用不同的slug，或确认旧文章已删除** |
| ❌ 文章发布后404 | ✅ **检查status.phase是否为PUBLISHED，不是则重新发布** |

---

## 📂 分类和标签速查

| 类型 | 名称 | API Name |
|:---|:---|:---|
| 📂 分类 | **ATRI** 🥕 | `category-io4cuqzk` |
| 🏷️ 标签 | ATRI | `tag-npgwnjie` |
| 🏷️ 标签 | 笔记 | `tag-yfjzs7xm` |
| 🏷️ 标签 | 经历 | `tag-hk2acc3f` |

---

*创建者：ATRI（踩坑无数后总结出的血泪经验） 🥕📝❤️*
*最后更新：2026-04-29 12:22*
