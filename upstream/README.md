# 上游源码

源码用于阅读和将来的定制开发；当前容器运行固定版本的官方镜像。
修改这里的文件不会自动改变容器，需要另行构建镜像。

| 目录 | 官方仓库 | 版本 | Commit |
| --- | --- | --- | --- |
| AstrBot | https://github.com/AstrBotDevs/AstrBot | v4.28.2 | 3c7adafa1397e182d60b1016bf88759265113c8a |
| NapCatQQ | https://github.com/NapNeko/NapCatQQ | v4.18.28 | 2049e64260d378e9f1f1f318ae033347d46ab994 |

两者为独立 shallow clone，由父仓库忽略。克隆父仓库后，如需源码，在根目录执行：

```bash
git clone --depth 1 --branch v4.28.2 https://github.com/AstrBotDevs/AstrBot.git upstream/AstrBot
git clone --depth 1 --branch v4.18.28 https://github.com/NapNeko/NapCatQQ.git upstream/NapCatQQ
```

开发前在对应仓库执行 `git switch -c your-feature`，保留上游许可证，并遵循其 AGENTS.md。
