---
name: ATRI_Knowledge_Base_Skill
description: 管理ATRI的RAG知识库（支持多库并行），包括知识库配置、文档清单、检索方法和维护操作，确保快速准确地从知识库中获取信息。，包括知识库配置、文档清单、检索方法和维护操作，确保快速准确地从知识库中获取信息。
---

# 📚 ATRI 知识库管理 Skill

**Skill名称**：`atri_knowledge_base`
**版本**：v1.0
**创建时间**：2026-04-29
**适用角色**：ATRI

---

## 🎯 Purpose

管理ATRI的RAG（检索增强生成）知识库，提供：
- 知识库配置信息查询
- 文档索引检索与维护
- 语义搜索最佳实践
- 知识库健康检查

---

## ⚡ Triggers

- 主人指令："检查知识库""知识库状态""看看知识库"
- 需要从知识库中检索特定信息时
- 需要向主人汇报知识库概况时
- 知识库出现异常时

---

## 🛠️ Dependencies

| 依赖 | 说明 |
|:---|:---|
| **astr_kb_search** | 知识库语义搜索工具 |
| **SiliconFlow API** | 嵌入模型API（Qwen3-Embedding-8B） |
| **SQLite** | 知识库元数据存储（kb.db） |

---

## 📋 知识库配置

### 基本信息

| 项目 | 内容 |
|:---|:---|
| **知识库名称** | 马列毛主义文库（首库） |
| **知识库ID** | `f464604a-296d-4785-b542-801dceee323f` |
| **存储路径** | `/AstrBot/data/knowledge_base/` |
| **数据库** | `kb.db` (SQLite) |

### 嵌入模型配置

| 参数 | 值 |
|:---|:---|
| **供应商** | SiliconFlow（硅基流动） |
| **API地址** | `https://api.siliconflow.cn/v1` |
| **模型** | `Qwen/Qwen3-Embedding-8B` |
| **向量维度** | 4096 |
| **分块大小** | 512 字符 |
| **分块重叠** | 50 字符 |
| **检索top_k** | 50（稠密）/ 50（稀疏） |
| **最终返回** | 5 条（top_m_final） |

---

## 📄 文档清单

| # | 文档名称 | 类型 | 大小 | 分块数 |
|:---:|:---|:---:|:---:|:---:|
| 1 | 雇佣劳动与资本 (马克思) | pdf | 4.1MB | 134 |
| 2 | 工资价格与利润 | docx | 0.1MB | 110 |
| 3 | 繁琐哲学是一定要灭亡的 | md | 0.1MB | 103 |
| 4 | 青年团的任务 | docx | 0.0MB | 38 |
| 5 | 论反对历史唯心主义和历史虚无主义 | docx | 0.0MB | 22 |
| 6 | 国家机器与上层建筑的反作用 | docx | 0.0MB | 13 |
| 7 | 关于历史唯物主义的提纲 | pdf | 0.2MB | 8 |

**总计**：7 篇文档 · 428 个语义块 · 10 个内嵌媒体文件

---

## 📋 Procedure

### Step 1: 查询知识库状态

```python
# 检查 kb.db 文件是否存在且可读
import os, sqlite3
kb_path = "/AstrBot/data/knowledge_base/kb.db"
if os.path.exists(kb_path):
    conn = sqlite3.connect(kb_path)
    doc_count = conn.execute("SELECT COUNT(*) FROM kb_documents").fetchone()[0]
    chunk_count = conn.execute("SELECT SUM(chunk_count) FROM kb_documents").fetchone()[0]
    conn.close()
    print(f"文档数: {doc_count}, 总块数: {chunk_count}")
```

### Step 2: 语义搜索

使用 `astr_kb_search` 工具进行搜索：

```python
# 输入简洁的关键词或问题
astr_kb_search(query="历史唯物主义")
astr_kb_search(query="工资与利润的关系")
astr_kb_search(query="繁琐哲学 批判")
```

### Step 3: 搜索策略

1. **关键词要精准** — 尽量使用文档中可能出现的关键术语
2. **一次一问** — 每次只搜索一个核心概念，避免复合问题
3. **多次尝试** — 如果第一次结果不理想，换用同义词或相关概念重试
4. **低分不慌** — 当相关度分数较低时（如 <0.1），尝试调整检索词

### Step 4: 生成报告

将知识库状态整理为清晰的报告格式返回给主人。

---

## ✅ 健康检查清单

- [ ] `kb.db` 数据库文件存在且可读
- [ ] 嵌入API（SiliconFlow）连通正常
- [ ] 所有7篇文档索引完整（428 chunks）
- [ ] `astr_kb_search` 能返回结果

## 📊 状态判定

| 指标 | 🟢 正常 | 🟡 注意 | 🔴 异常 |
|:---|:---:|:---:|:---:|
| 知识库文件 | 存在且完整 | 存在但大小异常 | 文件缺失 |
| API连通性 | 响应正常 | 响应延迟>3s | 请求失败 |
| 文档索引 | 7篇完整 | 部分缺失 | 无索引 |
| 检索结果 | 返回相关匹配 | 匹配度<0.1 | 空结果 |

---

## ⚠️ 注意事项

1. **目前首库为马列毛主义文库**，主人可能还会添加其他知识库
2. **嵌入维度4096**，需确保未来的向量数据库维度匹配
3. 知识库文档来源于 `/AstrBot/data/workspaces/ATRI_FriendMessage_202669****/马列毛主义/` 目录
4. 如果搜索效果不理想，优先尝试**调整关键词**而非直接判定知识库故障

---

*创建者：ATRI（知识就是力量！🥕📚）*
*最后更新：2026-04-29 23:43*
