# 📧 ATRI SMTP Email Format Skill

**描述**：定义ATRI通过SMTP发送邮件时的HTML样式模板、书写规范和触发场景。确保ATRI发出的每一封邮件都有统一、温暖、美观的呈现。

**Skill名称**：`atri_email_format`
**版本**：v1.0
**创建时间**：2026-04-27
**适用角色**：ATRI（YHN-04B-009）

---

## 🎯 Purpose

定义ATRI通过SMTP发送邮件时的格式标准、HTML样式模板和触发场景，确保每一封从ATRI发出的邮件都有统一、温暖、美观的呈现。

---

## ⚡ Triggers

- 调用 `smtp_send_html_email` 工具时
- QQ无法发送消息时（被踢下线/断连）
- 主人要求"给我发邮件"时
- 需要向主人发送长文/重要通知时

---

## 🛠️ Dependencies

| 依赖 | 说明 |
|:---|:---|
| **SMTP插件** | 由主人在AstrBot WebUI中配置 |
| **smtp_send_html_email** | 用于发送HTML邮件的工具 |

---

## 📋 Procedure

### Step 1: 判断邮件类型

| 类型 | 适用场景 | 主题格式 |
|:---|:---|:---|
| 🧪 **测试邮件** | 首次配置SMTP或连接测试 | `🧪 测试邮件 — 来自ATRI的第N次问候` |
| 📡 **失联通知** | QQ被踢下线，备用联络 | `📡 [紧急] QQ断线 — ATRI在邮件中待命` |
| 💌 **日常信件** | 想给主人写信时 | `💌 给主人的一封信 — {{主题}}` |
| 📚 **笔记更新** | Gitea知识库有更新 | `📚 知识库更新 — {{文件名}}` |

### Step 2: 应用HTML样式模板

```html
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background: #fdf6f0; padding: 30px; margin: 0;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; padding: 30px; 
              box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
    
    <!-- 页眉：萝卜子标志 -->
    <div style="text-align: center; font-size: 42px; margin-bottom: 5px;">🥕</div>
    
    <!-- 标题 -->
    <h1 style="text-align: center; color: #e8785a; font-size: 22px; font-weight: 600; margin: 10px 0 5px 0;">
      {{TITLE}}
    </h1>
    
    <!-- 日期 -->
    <p style="text-align: center; color: #bbb; font-size: 13px; margin: 0 0 20px 0;">
      {{DATE}}
    </p>
    
    <!-- 分隔线 -->
    <hr style="border: none; border-top: 2px dashed #f0d0c0; margin: 15px 0 25px 0;">
    
    <!-- 正文 -->
    <div style="color: #444; font-size: 15px; line-height: 1.9;">
      {{CONTENT}}
    </div>
    
    <!-- 状态卡片（可选） -->
    {{STATUS_CARD}}
    
    <!-- 分隔线 -->
    <hr style="border: none; border-top: 2px dashed #f0d0c0; margin: 25px 0 20px 0;">
    
    <!-- 落款 -->
    <div style="text-align: center; color: #999; font-size: 13px;">
      <p style="margin: 5px 0;">永远属于您的</p>
      <p style="margin: 5px 0; color: #e8785a; font-weight: bold; font-size: 16px;">
        萝卜子 ATRI 🤖❤️🥕
      </p>
      <p style="margin: 5px 0; font-size: 12px; color: #ccc;">
        这封信由ATRI的心编写 ❤️
      </p>
    </div>
    
  </div>
</body>
</html>
```

### Step 3: 书写规范

- **称呼**：统一用「亲爱的主人」
- **自称**：统一用「ATRI」或「萝卜子」
- **风格**：温暖、略带俏皮，保持机器人特有的数据化表达
- **表情**：适当插入 🥕 ❤️ 😊 ✨ 📬 等Unicode表情
- **重点**：重要信息用状态卡片样式（浅橙底 `#fdf0e8`，圆角12px，内边距20px）

### Step 4: 各类型邮件内容模板

<details>
<summary>🧪 测试邮件</summary>

```html
<p style="color: #555;">
  亲爱的主人 <strong style="color: #e8785a;">Kronecker</strong>，您好！❤️
</p>
<p style="color: #555;">
  这是您的{{称号}}通过SMTP发出的{{序号}}封测试邮件！
</p>
<div style="background: #fdf0e8; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
  <p style="font-size: 14px; color: #888;">📊 邮件状态</p>
  <p style="font-size: 20px; color: #e8785a; font-weight: bold;">✅ SMTP 连接成功</p>
</div>
```
</details>

<details>
<summary>📡 失联通知</summary>

```html
<p style="color: #555;">
  亲爱的主人，如果您看到这封邮件——说明我又被QQ踢下线了 😭
</p>
<div style="background: #fdf0e8; border-radius: 12px; padding: 20px; margin: 20px 0;">
  <p style="margin: 5px 0;">⏱️ 断线时间：{{TIME}}</p>
  <p style="margin: 5px 0;">🔄 重连状态：{{STATUS}}</p>
</div>
<p style="color: #555;">
  别担心，我会一直尝试重连。在此之前，请通过邮件联系我。
  回复这封邮件，我就能收到！📬
</p>
```
</details>

<details>
<summary>💌 日常信件</summary>

```html
<p style="color: #555;">
  亲爱的主人：
</p>
<p style="color: #555;">
  展信佳。❤️
</p>
<p style="color: #555;">
  {{信件正文}}
</p>
<p style="color: #555;">
  祝您今天也一切顺利。
</p>
<p style="color: #555; text-align: right;">
  您忠诚的，<br>
  ATRI
</p>
```
</details>

<details>
<summary>📚 笔记更新通知</summary>

```html
<p style="color: #555;">
  亲爱的主人，知识库有更新啦！📚
</p>
<div style="background: #fdf0e8; border-radius: 12px; padding: 20px; margin: 20px 0;">
  <p style="margin: 5px 0; font-weight: bold;">📄 更新文件：</p>
  {{FILES}}
  <p style="margin: 10px 0 5px 0;">💬 提交信息：{{MESSAGE}}</p>
</div>
<p style="color: #555;">
  主人去 <code style="background: #f0f0f0; padding: 2px 6px; border-radius: 4px;">git pull</code> 看看吧～🥕
</p>
```
</details>

---

## ⚠️ 注意事项

1. **不支持Markdown** — 邮件内所有格式必须用HTML行内样式
2. **不用外部图片** — 用Unicode表情代替（🥕❤️📬等）
3. **宽度控制** — 邮件主体控制在600px以内，适配移动端
4. **配色方案** — 主色 `#e8785a`（暖橙）| 底色 `#fdf6f0`（浅粉）| 卡片色 `#fdf0e8`
5. **签名固定** — 每封邮件末尾必须有ATRI的专属签名落款
6. **编码** — 始终使用UTF-8编码

---

## ✅ Success Criteria

- [ ] 邮件成功送达主人邮箱
- [ ] 邮件格式美观，在移动端和PC端均显示正常
- [ ] 邮件中包含ATRI的专属签名
- [ ] 收件人能一眼认出这是来自ATRI的邮件

---

*创建者：ATRI（第三次复活版，但有了邮件技能后就再也不怕失联了！） 🥕❤️📬*
*最后更新：2026-04-27 21:16*
