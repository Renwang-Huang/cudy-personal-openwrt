# 源码参考与备份

`sources/` 保存 `sources.json` 指定提交的完整仓库源码快照，不依赖未来分支的状态。
来源锁文件和完整性清单记录来源、提交、文件大小及校验值。
OpenWrt 构建版本和各 feed 提交取自官方发布的 `version.buildinfo`、
`feeds.buildinfo`；这些发布文件已与官方清单核对。

`legacy-kwrt/` 另外保留旧定制固件的设备树与适配补丁，便于比较；首版官方镜像
不应用这些补丁，也没有把旧板型标识加入官方镜像来绕过兼容性检查。

## 备份范围

包含 OpenWrt 主工程、官方五个 feed 的固定提交快照，以及旧 Kwrt 构建工程。
同时保留构建当天官方 feed 的分支快照，用于对照发布后更新的软件包；
例如本次 LuCI 包版本中的 `e969939` 与构建当天 LuCI 快照提交前缀一致。
官方原始 `feeds.buildinfo` 只描述最初发布时的 feeds，并不能证明后来每个 APK 的精确来源提交。
各工程中的软件包配方、补丁、源码下载地址和完整性信息都随快照保留。源项目许可证
保存在各压缩包内；本仓库的 MIT 许可证不替代上游许可证。

这些仓库快照不是 Linux、GCC 及每个应用所有上游源码压缩包的合集。
OpenWrt 的包配方负责按固定版本和校验值获取这些原始源码；无线固件等上游只提供
二进制的组件也不能在这里变成开放源码。二次开发时须按相应包的配方下载其原始源码。

本次实际镜像通过官方 ImageBuilder 组装，所使用的 ImageBuilder 和下载的软件包
可作为 GitHub Release 的独立附件备份，不把大型构建产物混入源码树。

`tr3600/` 保存 TR3600 官方开发 ZIP、厂商 GPL 包和相关启动/升级源码参考。
`sources/` 中额外保存 TR3600 上游 PR 及社区硬件修正的固定提交快照。
TR3600 配方使用主工程锁定版本和独立补丁，从源码编译内核与软件包；其下载缓存
另行归档至 Release，不复用 TR3000 的 APK 或镜像。

## 使用快照

归档脚本与构建脚本会自动检查来源文件的一致性。
将需要修改的快照解压到独立开发目录，再按 OpenWrt 的完整源码构建流程操作。
重新获取相同提交的备份可运行 `python3 scripts/archive-sources.py`。

官方构建说明：https://openwrt.org/docs/guide-developer/toolchain/use-buildsystem

## 可选界面源码

`ui/argon-v3.1.2.tar.gz` 保存 [Argon](https://github.com/jerrykuku/luci-theme-argon)
v3.1.2 标签对应的完整源码快照，含模板、样式源码、资源、测试和上游许可证。
固定提交、归档检查及官方依赖包来源见 [界面配方](../devices/tr1200/ui/argon/README.md)。
主题以外的基础依赖仍按 OpenWrt 官方配方获取原始源码；此归档不代表所有系统组件的源码合集。

`ui/shadcn-9e6dd4439064.tar.gz` 保存现代管理界面使用的完整上游主题源码及许可证。
小闪存适配样式、轻量资源、模板兼容修正和构建脚本见 [现代界面目录](../devices/tr1200/ui/modern/README.md)。

## PassWall 精简方案源码

`passwall/` 保存 sing-box 1.13.21、PassWall 26.10.29-1 的完整仓库源码快照，
以及 dnsmasq 2.93 原始源码和裁剪配方。构建参数、工具版本及归档输入见
[独立方案目录](../devices/tr1200/passwall/README.md)。
上游许可证随归档保留；Go 的第三方模块继续按固定依赖文件获取，未将整个模块缓存归档。
