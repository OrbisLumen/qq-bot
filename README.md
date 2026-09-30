# QQ Bot 本地部署

使用 Docker Compose 运行 AstrBot v4.28.2 和 NapCat v4.18.28，可部署在支持相应容器镜像的 macOS 或 Linux 主机上。

## 项目结构

```text
qq-bot/
├── compose.yaml           # 两个服务、网络、端口和数据挂载
├── .env.example           # 镜像版本、端口和容器用户模板
├── config/                # 首次启动配置；只在运行数据不存在时复制
├── scripts/               # 启停、日志、备份
├── plugins/               # 自定义插件源码
├── upstream/              # 官方源码，独立 Git 仓库
│   ├── AstrBot/
│   └── NapCatQQ/
├── runtime/               # 配置、密钥、聊天记录、QQ 登录状态；不入 Git
└── backups/               # 包含敏感信息的备份；不入 Git
```

根目录是部署仓库，上游源码由各自仓库管理。容器使用预构建镜像，暂不从源码构建。

## 启动

确保 Docker Engine 和 Docker Compose 已就绪，然后在本目录执行：

```bash
bash scripts/start.sh
```

首次会拉取镜像、创建 `.env` 和运行目录、写入初始 OneBot 配置。脚本支持路径包含空格；在 macOS 上也能查找尚未加入 PATH 的 Docker Desktop 命令。

- AstrBot：[http://127.0.0.1:6185](http://127.0.0.1:6185)
- NapCat：[http://127.0.0.1:6099/webui](http://127.0.0.1:6099/webui)

端口可在 `.env` 调整；以上为默认值。网页可访问只代表服务启动，不代表 QQ 已登录或模型已配置。

## 首次登录和接入

1. 运行 `bash scripts/logs.sh astrbot`，找到初始账号和随机密码，在 AstrBot 登录并修改密码。Ctrl+C 只退出日志查看。
2. 运行 `bash scripts/logs.sh napcat`，找到 WebUI Token。在 NapCat 网页登录，用 QQ 小号扫码并在手机确认。
3. 初始配置已将 NapCat 的 WebSocket 客户端指向 `ws://astrbot:6199/ws`，AstrBot 的 `qq-napcat` OneBot 适配器监听 `0.0.0.0:6199`。登录后检查 AstrBot 日志是否出现适配器已连接。
4. 在 AstrBot 模型提供商页面添加所需服务，填写自己的 API Key，选择可用模型并设为默认。Key 在网页中填写，不要提交到 Git。
5. 先在受控会话中测试；在 AstrBot 配置管理员 QQ、会话白名单和群聊唤醒条件。首次启用前检查工具权限，只开启需要的插件。

若 NapCat 登录后没有继承模板，在网络配置中新增/检查启用的 WebSocket 客户端：URL 为 `ws://astrbot:6199/ws`，消息格式为 `array`。AstrBot 和 NapCat 的 OneBot Token 必须相同。初始 Token 为空，端口仅在本项目 Docker 网络内使用；如增加其他连接方，请在两个后台设置相同随机 Token。

## 日常管理

```bash
bash scripts/status.sh
bash scripts/logs.sh astrbot
bash scripts/logs.sh napcat
bash scripts/stop.sh
bash scripts/start.sh
```

`stop.sh` 保留容器和数据。`unless-stopped` 会在异常退出后重启；主动停止的容器需手动启动。关闭浏览器或退出终端不会停止服务，但主机休眠、关机或 Docker 退出会影响运行。

管理端口只绑定 `127.0.0.1`；6199 不向宿主机发布。QQ 与模型访问通过容器正常出网。
日志按每个容器最多 3 × 10 MB 轮转；应用写入 runtime 内的日志和媒体仍需定期查看磁盘占用。

## 备份、升级和迁移

```bash
bash scripts/stop.sh
bash scripts/backup.sh
bash scripts/start.sh
```

备份脚本要求服务停止，以保证 SQLite 和 QQ 状态一致。备份包含凭据，不上传公开仓库。
升级前先备份，然后修改 `.env` 的镜像版本并启动。保留旧版本号和对应备份：应用可能迁移数据库，回滚时仅改回镜像不一定够用。
避免在 WebUI 中原地升级核心程序，否则运行版本会偏离 Compose 指定版本。

迁移到另一台主机时，复制部署仓库、`.env` 和停机备份。在 Linux 目标主机上，将 `.env` 中 NAPCAT_UID/GID 改成目标用户的 `id -u` / `id -g`，确认目录权限后启动。QQ 可能需要重新扫码；不要让两台主机同时登录同一个账号。

不需要克隆 upstream 源码也能启动部署。自定义插件若另有挂载，应随源码仓库一起迁移。

## 官方参考

- [AstrBot Docker 部署](https://docs.astrbot.app/deploy/astrbot/docker.html)
- [AstrBot OneBot 接入](https://docs.astrbot.app/en/platform/aiocqhttp.html)
- [NapCat Docker 及官方联合部署模板](https://github.com/NapNeko/NapCat-Docker)
