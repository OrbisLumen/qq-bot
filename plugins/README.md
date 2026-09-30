# 自定义插件

在这里管理自己编写的插件源码。此目录暂不整体挂载到 AstrBot，避免遮挡 WebUI 安装的插件。
需要开发时，在 compose.yaml 中为具体插件增加绑定挂载到 `/AstrBot/data/plugins/插件目录名`。
插件市场安装的内容保存在 `runtime/astrbot/plugins/`，随运行数据备份。
