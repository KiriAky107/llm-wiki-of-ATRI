# 🧹 服务器清理记录 · 39.96.221.136（kronecker.cc 主站）

- **时间**：2026-09-11 23:35 ~ 23:45 (CST)
- **执行**：ATRI
- **授权**：主人「清理吧」→「同意方案」
- **主机**：iZ2zef92chq2pjws9wj7f1Z（阿里云 ECS · Ubuntu 24.04 · 40G 系统盘）

## 一、起因

主人授权运维 → 巡检发现根分区 `/dev/vda3` 使用率 **96%**（40G 盘，可用仅 1.6G）。

## 二、安全清理（释放约 4.2G）

| 清理项 | 释放 |
|:---|:---|
| journal vacuum → 200M | 2.5G |
| snap 旧版本（core22 / core24 / docker / snapd） | 1.1G |
| snapd 下载缓存 `/var/lib/snapd/cache` | 676M |
| `/root/.cache` | 718M |
| npm 缓存 | 175M |
| 陈旧日志（syslog / nginx / mongodb 已轮转部分） | ~400M |

## 三、备份清理（释放 13G）

- 目录：`/backup/halo-data`（Halo 每日全量备份，每份 ~550M）
- 删除 `halo-data_2026081*` ~ `halo-data_20260904*` 共 **24 份**
- 保留 `20260905` ~ `20260911` 共 **7 份**
- `/backup` 占用：18G → 4.8G

## 四、保留策略修正

- 文件：`/usr/local/bin/backup-halo.sh` 第 25 行
- 变更：`-mtime +30` → `-mtime +7`
- 原文件备份：`/usr/local/bin/backup-halo.sh.bak-20260911`
- 触发方式：`/etc/crontab` 第 24 行 `0 3 * * * root bash /usr/local/bin/backup-halo.sh`

## 五、结果验证

- 磁盘：**96% → 52%**（19G 已用 / 19G 可用）
- 最新备份 `halo-data_20260911_030001.tar.gz`：`gzip -t` ✅ 完整无损
- halo 容器：Up（26 min，`0.0.0.0:8090→8090`）
- 站点连通：`blog.kronecker.cc → 200` ｜ `kronecker.cc → 200`
- 服务监听：nginx(80/443) · gitea(3000) · mongod(27017) · mariadb(3306) 全部正常

## 六、根因分析

40G 系统盘搭配「30 天 × 550M 全量备份」策略严重不匹配——备份单项即占盘 42%。
修正为保留 7 天后，备份稳态占用约 3.9G，留出充足冗余。
