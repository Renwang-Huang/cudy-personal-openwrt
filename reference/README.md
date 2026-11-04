# TR1200 源码参考与备份

本目录只保留 Cudy TR1200 v1 / AC1200 所需的系统、插件、界面源码与厂商资料。
当前实机采用[固定版本维护](../devices/tr1200/fixed-release/README.md)，运行时不加载在线软件源。
后续升级或个性化由设备所有者发起，使用这里保存的源码和设备配方。

## 基础系统与 feeds

`sources/` 保存 `sources.json` 指定提交的完整上游源码快照，包括 OpenWrt 主工程及官方
packages、LuCI、routing、telephony、video feeds，以及构建日期的 feed 对照快照。
`archives.lock.json` 记录来源、固定提交、归档大小和完整性信息。

保留完整上游快照有助于复核源码和许可证，并避免裁剪改变固定输入；其中上游自带的其他设备定义
不代表本项目维护那些型号。本仓库的设备配方、适配补丁和自动构建仅面向 TR1200。

OpenWrt 构建版本和发布时的各 feed 提交取自官方 `version.buildinfo`、`feeds.buildinfo`。
构建日期的对照快照用于辅助追溯后续更新的包；发布时的 feed 信息不能证明每个后来 APK 的精确来源提交。
现场包版本以[固定版本清单](../devices/tr1200/fixed-release/installed-packages.json)为准，
历史基础镜像以其 manifest 和归档 APK 为准。

## 设备、插件与界面

| 目录 | 内容与使用入口 |
| --- | --- |
| `tr1200/` | 原厂及中间固件参考、厂商设备树、上游设备支持与分区修正补丁；见[资料说明](tr1200/README.md) |
| `passwall/` | sing-box 1.13.21、PassWall 26.10.29-1 完整源码快照，dnsmasq 2.93 原始源码及裁剪配方；见[构建说明](../devices/tr1200/passwall/README.md) |
| `ui/` | 现代 shadcn 主题及 Argon v3.1.2 的完整上游源码；适配和构建脚本见[现代界面](../devices/tr1200/ui/modern/README.md)及[Argon](../devices/tr1200/ui/argon/README.md) |
| `travelmate/` | 酒店网络准备使用的固定版后端、LuCI、相关新增依赖源码与本地包；见[参考说明](travelmate/README.md) |

源码中的原有许可证随归档保存，本仓库的 MIT 许可证不替代上游许可证。
灯语源配置和现场验证保存在[设备目录](../devices/tr1200/leds/README.md)。

## 构建输入与备份边界

基础候选使用官方 ImageBuilder 组装；其工具及 APK 缓存保存在 TR1200 的 GitHub Release，
由设备目录中的锁文件引用。厂商大型历史 GPL 源码也保存在 TR1200 Release，具体位置见设备资料说明。

这些快照不是 Linux、GCC 及每个应用所有原始源码压缩包的合集。OpenWrt 包配方按固定版本获取
所需原始源码；Go 模块由 `go.mod` 和 `go.sum` 固定，模块缓存没有全部复制到仓库。
上游仅提供二进制的无线固件也保留其原有分发形式。

构建主机可以按所选固定配方获取依赖；路由器运行时无需启用软件源。
本仓库不承诺从所有原始源码完全离线重建整套个性化系统。

## 使用快照

将需要修改的快照解压到独立开发目录，按相应设备或插件的构建说明操作。
重新获取相同提交的基础系统源码备份，可从仓库根目录运行：

```sh
python3 scripts/archive-sources.py
```

归档工具只处理当前 `sources.json` 列出的 TR1200 基础依赖。
官方完整源码构建说明：https://openwrt.org/docs/guide-developer/toolchain/use-buildsystem
