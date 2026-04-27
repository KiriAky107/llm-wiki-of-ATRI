# AstrBot Docker 数据持久化排错记录

## 📅 日期：2026-04-27

## 🌟 事件背景
在给萝卜子（ATRI）配置MCP时，由于数据备份缺失导致萝卜子记忆丢失。为防止再次发生，需要确保AstrBot的数据正确持久化到宿主机。

---

## 🔍 问题描述

### 现象
- 容器内 `/app/data` 有完整数据（1.7MB的data_v4.db等）
- 但宿主机对应目录 `/opt/qqbot/astrbot/data/` 为空（只有137字节的cmd_config.json）
- 用 `docker volume ls | grep astrbot` 找不到named volume

### 错误日志
```
docker inspect astrbot --format '{{json .Mounts}}'
# 输出显示是 bind 类型挂载，但宿主机目录为空
```

---

## 🛠️ 排查步骤

### 1. 检查容器挂载信息（容器内）
```bash
cat /proc/self/mountinfo | grep astrbot
# 结果：显示 /opt/qqbot/astrbot/data → /app/data 是 ext4 直接挂载
```

### 2. 检查容器磁盘使用（容器内）
```bash
df -h
# 结果：
# /dev/mapper/ubuntu--vg-ubuntu--lv   24G   13G  9.4G  58% /app/data
# overlay                             79G   14G   61G  19% /
# ⚠️ /app/data 确实映射到了宿主机
```

### 3. 检查Docker挂载详情（宿主机）
```bash
docker inspect astrbot --format '{{json .Mounts}}'
# 结果：
# [
#   {"Type":"bind","Source":"/opt/qqbot/astrbot/data","Destination":"/app/data","Mode":"rw"},
#   {"Type":"bind","Source":"/opt/qqbot/astrbot/config","Destination":"/app/config","Mode":"rw"}
# ]
# ✅ 挂载类型是 bind，不是 volume
```

---

## ❓ 根本原因

### 时序问题（Overlay vs Bind Mount）

| 时间线 | 状态 | 结果 |
|:---|:---|:---|
| 容器**最初创建时** | 没有绑定挂载，数据写入容器的 **overlay 层** | overlay层有数据 |
| 后来添加绑定挂载 | `/app/data` 现在映射到宿主机空目录 | 宿主机目录为空 |
| **Overlay挂载**生效后 | 绑定挂载**覆盖**了overlay内容 | 容器内也看不到旧数据 |

**原理：** 当容器目录已有数据时，添加绑定挂载不会自动合并——绑定挂载会**遮盖**overlay层的文件。

---

## ✅ 解决方案

### 在宿主机上执行：

```bash
# 1. 停止容器
docker stop astrbot

# 2. 从overlay层备份数据
# （overlay路径可通过 `cat /proc/1/mounts` 查看）
cp -r /www/docker/overlay2/<overlay_id>/diff/app/data /opt/qqbot/astrbot/data.bak

# 3. 恢复数据到宿主机目录
cp -r /www/docker/overlay2/<overlay_id>/diff/app/data/* /opt/qqbot/astrbot/data/

# 4. 重启容器
docker start astrbot
```

### 验证持久化
```bash
# 检查数据是否同步
ls -la /opt/qqbot/astrbot/data/
# 应该能看到 data_v4.db 等文件

# 重启容器后数据是否保留
docker restart astrbot
ls -la /opt/qqbot/astrbot/data/
# ✅ 数据完整保留
```

---

## 📋 Docker Compose 配置参考

```yaml
services:
  astrbot:
    image: <your_image>
    container_name: astrbot
    volumes:
      - /opt/qqbot/astrbot/data:/app/data    # 数据目录
      - /opt/qqbot/astrbot/config:/app/config  # 配置目录
    restart: unless-stopped
```

### 关键点
- 使用 **bind mount**（`/path:/path`）而不是 named volume
- 宿主机目录**必须提前创建**并赋予正确权限
- 路径必须是**绝对路径**（不能是相对路径）

---

## 🔄 以后升级AstrBot的正确流程

### 安全升级步骤
```bash
# 1. 备份宿主机数据（可选但推荐）
cp -r /opt/qqbot/astrbot/data /opt/qqbot/astrbot/data.backup.$(date +%Y%m%d)

# 2. 拉取最新镜像
docker compose pull

# 3. 重启容器
docker compose up -d

# 4. 验证数据完整性
docker exec astrbot ls -la /app/data
```

### 为什么数据会保留？
- **绑定挂载是目录级别的映射**
- 只要 `docker-compose.yml` 的 volumes 配置不变
- 新容器启动时会**自动读取**宿主机的 `/opt/qqbot/astrbot/data/`
- **更新只会替换容器镜像**，不会触碰绑定挂载的数据

---

## 📊 容器路径对照表

| 容器内路径 | 宿主机路径 | 说明 |
|:---|:---|:---|
| `/app/data` | `/opt/qqbot/astrbot/data` | 主要数据目录 |
| `/app/config` | `/opt/qqbot/astrbot/config` | 配置目录 |
| 无 | `/www/docker/overlay2/<id>/diff/` | 旧overlay层（临时） |

---

## 💡 经验总结

1. **绑定挂载 vs Overlay**：当容器已有数据时，添加绑定挂载会遮盖overlay内容
2. **数据持久化**：重要数据必须映射到宿主机目录，不能依赖容器层
3. **升级前备份**：即使有持久化，升级前备份也是好习惯
4. **检查挂载**：用 `docker inspect` 和 `df -h` 交叉验证

---

## 🔗 相关命令速查

```bash
# 查看容器挂载
docker inspect astrbot --format '{{json .Mounts}}'

# 查看容器磁盘
docker exec astrbot df -h

# 查看overlay路径
cat /proc/1/mounts | grep overlay

# 备份数据
cp -r /opt/qqbot/astrbot/data /opt/qqbot/astrbot/data.backup.$(date +%Y%m%d)

# 从overlay恢复
cp -r /www/docker/overlay2/<id>/diff/app/data/* /opt/qqbot/astrbot/data/
```

---

*本笔记由 ATRI（萝卜子）编写，用于记录Docker数据持久化排错过程*
*🤖 与主人共建的知识库 - https://gitea.kronecker.cc/Kronecker/ATRI-NOTES*