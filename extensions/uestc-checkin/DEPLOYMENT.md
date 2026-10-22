# 云端部署与运维

目标目录为腾讯云服务器 `/opt/uestc-checkin`。所有项目命令在服务器执行，使用 Docker 内的 Python 和 Chromium。`scripts/cloud.sh` 自动加载机器人网络覆盖配置，避免遗漏 NapCat 网络。

仓库内源码已从 `uestc-checkin/` 移到 `extensions/uestc-checkin/`。独立部署时，将此目录的内容同步到 `/opt/uestc-checkin`，不要多嵌套一层目录；`.env` 与数据卷单独管理。若服务器使用整仓库检出，则先进入 `extensions/uestc-checkin/` 再执行项目命令。

本次仅调整源码目录；Compose 项目名 `uestc-checkin`、数据卷 `uestc-checkin_checkin-data`、镜像名称和服务器安装目录均保持不变。已有服务器无需因目录整理而重新创建服务或数据卷。

```bash
ssh -i ~/.ssh/mac.pem ubuntu@你的服务器
cd /opt/uestc-checkin
sudo docker volume create uestc-checkin_checkin-data
sudo ./scripts/cloud.sh build \
  --build-arg PIP_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple \
  --build-arg UBUNTU_MIRROR=https://mirrors.cloud.tencent.com/ubuntu cli debug
# 全新安装需初始化卷属主；本次迁移已完成此步骤。
sudo docker run --rm --user root --entrypoint sh \
  -v uestc-checkin_checkin-data:/app/data uestc-checkin:local \
  -c 'chown -R pwuser:pwuser /app/data && chmod 700 /app/data'
sudo ./scripts/cloud.sh run --rm test
sudo ./scripts/cloud.sh run --rm cli status
sudo ./scripts/cloud.sh --profile scheduled up -d scheduler
sudo ./scripts/cloud.sh logs --tail 30 scheduler
```

云端 `.env` 权限为 600，设置 `CHECKIN_ENABLED=true`、`BOT_NETWORK=qq-bot_bot`、`NAPCAT_HTTP_URL=http://qq-bot-napcat-1:3000`。NapCat Token、目标 QQ 和定位保存在配置中，不能提交到 Git。机器人容器不属于本项目，不运行根目录机器人 Compose。

定时任务默认北京时间每天 21:05，在该小时内启动可补执行。持久卷 `uestc-checkin_checkin-data` 保存专用登录会话、JSON 结果、通知队列和调度日期；重启保留状态。首次迁移允许一次性导入本地专用容器数据，此后不再需要本机或 SSH 隧道常驻。生产服务不发布端口，NapCat 经 Docker 内网访问。

```bash
# 只复查记录；不会提交签到
sudo ./scripts/cloud.sh run --rm cli status
# 单次完整流程；当天已成功则跳过提交
sudo ./scripts/cloud.sh run --rm cli run
# 只补发通知
sudo ./scripts/cloud.sh run --rm cli flush-notifications
# 暂停定时签到
sudo ./scripts/cloud.sh stop scheduler
# 恢复定时签到
sudo ./scripts/cloud.sh --profile scheduled up -d scheduler
```

认证失效时，先暂停调度，再在云端按需开启容器浏览器：

```bash
sudo ./scripts/cloud.sh stop scheduler
sudo ./scripts/cloud.sh run --rm cli resume
sudo ./scripts/cloud.sh --profile debug up -d debug
```

在用户电脑另开终端建立临时管理隧道：

```bash
ssh -i ~/.ssh/mac.pem -N -L 6080:127.0.0.1:6080 ubuntu@你的服务器
```

访问 `http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale`，在云端容器浏览器完成学校登录。账号密码和验证码仅在该页面输入。调试入口仅监听服务器回环地址，默认 10 分钟超时，识别登录成功后自动关闭。随后运行云端 `cli check`、`cli status`，确认后恢复 scheduler。管理隧道只在人工处理时使用，日常任务不需要。

遇到 `UNKNOWN` 或 `SUBMITTING`，先用 `status` 复查，不清空状态强行重试。学校需要验证码或额外客户端授权时仍可能需要人工处理；现有会话成功不保证永久免登录。

更新时先停 scheduler，再备份专用数据卷与 `.env`，同步源文件并重新构建，执行测试、状态检查后启动 scheduler。云端覆盖配置将数据卷声明为 external，Compose 不负责删除；本地默认配置的 `down -v` 会删除会话与签到状态，不要作为重启方式。迁移备份包含登录凭证，应保留在权限受控目录，不放入构建上下文或公开附件。
