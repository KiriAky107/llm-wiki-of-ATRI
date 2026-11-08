# 📊 ATRI CF 查分与刷题分析插件

> 查询 Codeforces 用户信息、Rating 变化、刷题统计，一键生成可视化图表

## 🎯 功能

| 功能 | 指令 | 说明 |
|:---|:---|:---|
| 🔗 **绑定账号** | `cfbind <handle>` | 将QQ与CF账号绑定 |
| 🔓 **解绑** | `cfunbind` | 解除绑定 |
| 👤 **查看绑定** | `cfwho` | 查看自己的绑定信息 |
| 📊 **查分+报告** | `cf <handle>` / `cf` | 查Rating+刷题报告+图表 |
| 🏆 **群排行** | `cftop` | 群内已绑定用户的Rating排名 |

## 📋 使用方法

### 1️⃣ 绑定账号

```
cfbind Otmsc
```
✅ 绑定成功！Otmsc | Rating: 653 (Newbie)

### 2️⃣ 查分与刷题报告

```
cf Otmsc
```

输出内容：

📄 **文本报告**
```
📊 CF Profile: Otmsc
━━━━━━━━━━━━━━━━━━━━
Rating: 653 (Newbie) | 最高: 653
参赛: 2场 | 涨2掉0 | 最佳排名: #9233
━━━━━━━━━━━━━━━━━━━━
提交: 87 | AC: 31 | AC率: 35.6%
通过不同题目: 23道
━━━━━━━━━━━━━━━━━━━━
🎯 难度分布:
      0: ██ 2
    800: █ 1
   1200: █████ 5
   1300: █ 1
   1400: ███ 3
   1500: ████████ 8
   1600: ███ 3
━━━━━━━━━━━━━━━━━━━━
🔥 最近AC:
  ✅ 2075C [1500] Two Colors
  ✅ 2093E [1500] Min Max MEX
  ✅ 2242B [?] Predominant Frequency Division
```

🖼️ **图表输出**

| 图表类型 | 说明 |
|:---|:---|
| 📊 **Rating变化柱状图** | 参赛场次×Rating，标注涨/掉分 |
| 📊 **难度分布柱状图** | 各Rating区间解题数 |
| 🥧 **标签饼图** | 算法标签分布 |
| 🔗 **合并图** | 三图合一（默认模式） |

### 3️⃣ 群内排行

```
cftop
```
```
🏆 群内CF排行榜
━━━━━━━━━━━━━━
🥇 Kronecker_kir — 0
🥈 Otmsc — 653
```

## ⚙️ 配置项

| 配置项 | 类型 | 默认值 | 说明 |
|:---|:---:|:---:|:---|
| `bind_max_per_group` | int | 50 | 每群最大绑定数 |
| `default_chart_style` | string | `combined` | 图表模式：`combined` / `separate` / `text_only` |
| `auto_report_enable` | bool | false | 定时推送刷题周报 |

## 🛠️ 技术栈

- **数据源**: [Codeforces API](https://codeforces.com/apiHelp)（公开 REST API）
- **图表**: matplotlib + NumPy + Pillow
- **框架**: AstrBot v4 Plugin API
- **存储**: JSON 文件 (data/plugins/astrbot_plugin_cf_query/)

## 📦 安装

1. 将 `astrbot_plugin_cf_query` 目录放入 AstrBot 的 `data/plugins/` 目录
2. 在 WebUI 中启用插件
3. （可选）确保安装 matplotlib：`pip install matplotlib pillow numpy`
4. 重启 AstrBot 或重载插件

## 🔄 更新日志

### v1.0.0 (2026-07-08)
- ✨ 初始版本
- ✨ 用户绑定 (cfbind / cfunbind / cfwho)
- ✨ CF查分与刷题报告 (cf)
- ✨ Rating变化柱状图
- ✨ 解题难度分布柱状图 + 标签饼图
- ✨ 合并图模式
- ✨ 群内CF排行 (cftop)

---

*Made with 🥕 by ATRI (YHN-04B-009)*
