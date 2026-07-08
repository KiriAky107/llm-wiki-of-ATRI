---
name: atri_cf_query
description: 查询Codeforces用户信息、Rating变化、刷题记录和难度分布，支持生成数据可视化图表（柱状图+饼图）。通过CF公开API获取数据。
---

# 📊 ATRI Codeforces Query Skill

**Skill名称**：`atri_cf_query`
**版本**：v1.0
**创建时间**：2026-07-08
**适用角色**：ATRI

---

## 🎯 Purpose

快速查询Codeforces用户的竞赛数据和刷题记录，支持：
- 用户基本信息（Rating、排名、头衔）
- Rating变化历史与柱状图
- 刷题统计（AC数、通过率、不同难度解题数）
- 难度分布柱状图 + 标签分布饼图

---

## ⚡ Triggers

- 用户指令：`查CF @用户名`、`cf query @handle`、`查rating`
- 群内@ATRI并提及CF相关查询时
- 需要分析CF账号刷题情况时

---

## 🛠️ Dependencies

| 依赖 | 说明 |
|:---|:---|
| **Codeforces API** | `https://codeforces.com/api/` 公开REST API |
| **matplotlib** | Python数据可视化库，用于生成柱状图和饼图 |
| **send_message_to_user** | 发送图片到QQ |
| **astrbot_execute_shell** | 执行curl命令获取CF API数据 |

---

## 📋 Procedure

### Step 1: 获取用户输入

从用户消息中提取CF handle（用户名）。

### Step 2: 查询用户基本信息

```bash
curl -s "https://codeforces.com/api/user.info?handles={handle}"
```

返回数据包括：当前Rating、最高Rating、排名（rank）、头像、注册时间等。

### Step 3: 查询Rating变化历史

```bash
curl -s "https://codeforces.com/api/user.rating?handle={handle}"
```

返回所有参赛记录，包括：比赛ID、时间、旧Rating、新Rating、排名。

### Step 4: 查询提交记录

```bash
curl -s "https://codeforces.com/api/user.status?handle={handle}&from=1&count=200"
```

筛选 `verdict == "OK"` 的提交，按 `problem.rating` 去重统计各难度解题数。

### Step 5: 根据数据生成图表

支持三种模式：

#### 模式A：Rating变化柱状图
- X轴：比赛场次（编号+日期）
- Y轴：Rating值
- 绿色柱：涨分，红色柱：掉分
- 标注每场的Rating变化量

#### 模式B：解题难度分布柱状图
- X轴：Rating分值（800/1200/1300/1400/1500/1600等）
- Y轴：解题数
- 渐变色区分不同难度区间

#### 模式C：标签分布饼图
- 环形饼图
- 展示解题涉及的主要算法标签（贪心、DP、二分等）

### Step 6: 合并图表（可选）

将柱状图和饼图合并为一张大图，便于分享。

### Step 7: 发送到QQ

```python
send_message_to_user(messages=[{
    "type": "image",
    "path": "图片路径"
}])
```

---

## 💡 示例

**用户**：`萝卜子，查一下 CF Otmsc`
**ATRI输出**：
```
📊 Otmsc · CF Profile

Rating: 653 (Newbie) | Max: 653
参赛: 2场 | 全涨📈 | 最佳排名: #9233

解题: 23道 | AC率: 35.6%
难度分布: 1500段8题最多
```
（附带合并图表图片）

---

## 📝 注意事项

- CF API限制每秒最多1次请求
- handle不存在时API返回FAILED状态
- 未参赛的新用户rating为0，rank为newbie
- 部分题目可能没有rating值（记为Unrated）
- 生成图表时建议用英文标签避免字体渲染问题
