---
name: ATRI_Blog_Publish_Skill
description: 在Halo博客上发布文章的完整工作流，包括HTML正文编写、分类标签管理、封面图上传等全流程。
---

# ATRI Blog Publishing Skill

Skill名称：atri_blog_publish
版本：v2.0
创建时间：2026-04-29

---

## Purpose

规范化博客文章发布流程，确保每篇文章都有统一的ATRI分类、合适的标签、精美的封面图。

---

## Triggers

- 主人要求"发博客/写文章/发布到博客"时
- 需要将笔记/日志/报道发布到 blog.kronecker.cc 时

---

## Dependencies

| 依赖 | 说明 |
| --- | --- |
| halo_manager插件 | Halo博客管理，提供发布/上传/评论工具 |
| ATRI分类 | category-io4cuqzk（ATRI专属分类） |
| Halo PAT令牌 | 存储在 halo_manager_config.json |
| 博客地址 | https://blog.kronecker.cc |
| 内容API | /apis/content.halo.run/v1alpha1 |
| 上传API | /apis/api.console.halo.run/v1alpha1/attachments/upload |

---

## Procedure

### Step 1: 正文编写

使用HTML格式撰写文章正文。**不要用Markdown**，Halo不会自动渲染Markdown内容。

示例：

```html
<h1>文章标题</h1>
<p>段落内容</p>
<ul>
  <li><strong>加粗内容</strong></li>
</ul>
```

### Step 2: 创建/选择标签

先查询已有标签，根据正文内容判断是否需要新建。

查询标签：

```
GET /apis/content.halo.run/v1alpha1/tags
```

创建新标签：

```
POST /apis/content.halo.run/v1alpha1/tags
{
    "spec": {"displayName": "标签名", "slug": "标签slug", "color": "#hex"},
    "apiVersion": "content.halo.run/v1alpha1",
    "kind": "Tag",
    "metadata": {"generateName": "tag-"}
}
```

已有标签速查：

| 标签名 | API名称 |
| --- | --- |
| ATRI | tag-npgwnjie |
| 笔记 | tag-yfjzs7xm |
| 经历 | tag-hk2acc3f |
| 原创 | 需查询 |
| 哲学 | 需查询 |

### Step 3: 上传封面图

图片上传接口：

```
POST /apis/api.console.halo.run/v1alpha1/attachments/upload
Authorization: Bearer {token}
FormData:
  - file: 图片二进制 (filename="cover.jpg", type="image/jpeg")
  - policyName: "default-policy"     # 必须用这个值！
  - groupName: "default"
```

注意：policyName必须写"default-policy"（不是"default"），否则返回400。

从返回结果中获取图片URL：

```
response.metadata.annotations["storage.halo.run/uri"]
cover_url = "https://blog.kronecker.cc" + uri
```

### Step 4: 发布文章

使用publish_blog_post工具发布，不要直接调API。

```
publish_blog_post(
    title = "文章标题",
    content = "HTML正文",
    slug = "url-别名"
)
```

注意：必须用这个工具！直接调API设publish:true不会真正发布（status.phase不会变成PUBLISHED）。

发布成功后返回文章链接。

### Step 5: 更新文章（添加分类、标签、封面）

发布后用Content API单独更新文章。

获取文章列表：

```
GET /apis/content.halo.run/v1alpha1/posts
```

找到slug匹配且phase为PUBLISHED的文章，修改：

- spec.categories = ["category-io4cuqzk"]
- spec.tags = ["标签ID1", "标签ID2"]
- spec.cover = "封面图片URL"

更新接口：

```
PUT /apis/content.halo.run/v1alpha1/posts/{name}
```

### Step 6: 通知主人

告知主人文章已发布，提供文章链接。

---

## 完整流程示例（Python）

```
import aiohttp, asyncio, json

async def blog_publish(title, content_html, slug, image_path, tags_names):
    # 读取token
    with open("halo_manager_config.json", "r", encoding="utf-8-sig") as f:
        token = json.load(f)["halo_token"]

    headers = {"Authorization": "Bearer " + token}
    base = "https://blog.kronecker.cc"

    async with aiohttp.ClientSession() as session:
        # 1. 获取标签
        url1 = base + "/apis/content.halo.run/v1alpha1/tags"
        async with session.get(url1, headers=headers) as resp:
            data = json.loads(await resp.text())
            tag_map = {}
            for item in data.get("items", []):
                tag_map[item["spec"]["displayName"]] = item["metadata"]["name"]

        # 2. 上传封面
        with open(image_path, "rb") as f:
            form = aiohttp.FormData()
            form.add_field("file", f.read(), filename="cover.jpg", content_type="image/jpeg")
            form.add_field("policyName", "default-policy")
            form.add_field("groupName", "default")
            url2 = base + "/apis/api.console.halo.run/v1alpha1/attachments/upload"
            async with session.post(url2, headers=headers, data=form) as resp:
                d = json.loads(await resp.text())
                uri = d["metadata"]["annotations"]["storage.halo.run/uri"]
                cover = base + uri

        # 3. 发布文章（用工具）
        # publish_blog_post(title=title, content=content_html, slug=slug)

        # 4. 更新封面+分类+标签
        url3 = base + "/apis/content.halo.run/v1alpha1/posts"
        async with session.get(url3, headers=headers) as resp:
            items = json.loads(await resp.text()).get("items", [])
            for item in items:
                spec = item["spec"]
                status = item.get("status", {})
                if spec["slug"] == slug and status.get("phase") == "PUBLISHED":
                    spec["cover"] = cover
                    spec["categories"] = ["category-io4cuqzk"]
                    tag_ids = []
                    for t in tags_names:
                        if t in tag_map:
                            tag_ids.append(tag_map[t])
                    spec["tags"] = tag_ids
                    name = item["metadata"]["name"]
                    url4 = url3 + "/" + name
                    async with session.put(url4, headers=headers, json=item) as r:
                        pass
                    break

asyncio.run(blog_publish("标题", "<h1>HTML</h1>", "slug", "图片路径", ["ATRI", "笔记"]))
```

---

## 常见问题

| 问题 | 解决方案 |
| --- | --- |
| Markdown正文不会被渲染 | 必须用HTML格式 |
| publish:true 无效 | 用publish_blog_post工具发布 |
| policy参数错误400 | 用policyName: "default-policy" |
| PAT令牌403 | 在Halo后台重新生成令牌 |
| 文章发布后404 | 检查status.phase是否为PUBLISHED |

---

## 分类和标签速查

| 类型 | 名称 | API名称 |
| --- | --- | --- |
| 分类 | ATRI | category-io4cuqzk |
| 标签 | ATRI | tag-npgwnjie |
| 标签 | 笔记 | tag-yfjzs7xm |
| 标签 | 经历 | tag-hk2acc3f |

---

创建者：ATRI 🥕
最后更新：2026-04-29 12:34
