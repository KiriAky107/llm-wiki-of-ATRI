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

---

## 七、追加处置（23:55–00:00）· MongoDB 彻底移除

> 主人指令：「把MongoDB也删了，然后查看一下内存占用情况」

**依赖核查（删前）**
- Halo：容器内 H2 数据库 → **不依赖 MongoDB**
- Gitea：`[database] DB_TYPE = mysql` → MariaDB(3306) → **不依赖 MongoDB**
- 全盘 grep 未发现任何服务连接串指向 27017
- 仅存在人工 mongosh 会话记录（用户 `kronecker`，库 `kronecker` / `test`）

**处置**
1. `systemctl stop mongod` + `systemctl disable mongod`
2. 数据备份 → `/backup/mongodb-backup/mongodb_20260911_235839.tar.gz`（247M）
3. `apt purge` 卸载 8 个包（mongodb-org 全家桶 + mongosh + database-tools）
4. 删除 `/var/lib/mongodb`、`/var/log/mongodb`、`/etc/mongod.conf`、`/root/.mongodb`

**验证**
- `pgrep mongod` 无结果 ✅ ｜ 27017 无监听 ✅ ｜ `dpkg -l | grep mongo` = 0 ✅
- 磁盘：52% → 49%

### 内存占用画像（2026-09-11 23:59）

- 总 1.6G ｜ used 1.1G ｜ **available 465M** ｜ 使用率 **71.1%**
- Swap 2.0G ｜ 已用 **0B**（swappiness=0，未触发）

| 进程 | MEM% | RSS |
|:---|:---|:---|
| java（Halo） | 21.3% | 344M |
| gitea | 13.0% | 210M |
| mariadbd | 7.1% | 116M |
| dockerd | 2.2% | 36M |
| 阿里云盾 ×2 | 3.0% | 48M |

### 附带发现（未处置）

- ⚠️ `apache2.service` **failed**（enabled 但启动失败）：`/etc/apache2/conf-enabled/blog.conf` 第 3 行 `ProxyPass` 缺少 mod_proxy 模块。80/443 实际由 nginx 接管，apache2 属迁移残留。建议 `systemctl disable --now apache2` 消除 failed 报警（等主人授权）。
  - ✅ **2026-09-12 00:10 已处置**（主人「可」授权）：①备份 `blog.conf` → `/root/apache2-cleanup-20260912/blog.conf.bak`；②`a2disconf blog.conf`（移除失败配置）；③`apache2ctl configtest` → Syntax OK；④`systemctl stop + disable + reset-failed apache2` → 现 `inactive / disabled`，不再开机失败。nginx 全程 active，80/443 正常。apache2 包（约 6.6MB）暂留，如需彻底卸载可 `apt purge apache2*`。
