# Travelmate · TR1200 固定参考

此目录只归档 TR1200 酒店网络准备所使用的 Travelmate 及相关新增依赖。

| 目录 / 文件 | 内容 |
| --- | --- |
| `packages/` | OpenWrt `openwrt-25.12` 分支的 `net/travelmate`，2.4.9-r6 后端源码及配方 |
| `luci/` | 同分支的 `luci-app-travelmate`，前端、翻译和 ACL |
| `sources.lock.json` | 后端和前端的精确来源提交 |
| `native-dependencies/` | 新增本机组件所用版本的 rpcd 和 iwinfo 完整源码归档 |
| `packages-binary/` | 本次离线安装的五个固定 APK，便于复用相同输入 |
| `packages.lock.json` | APK 的官方 HTTPS 来源、版本、大小及验证边界 |

后端关键文件已与实际安装包解出的原始文件逐字节比对。
应用时的双 DNS 适配、有限上游事件同步及操作说明保存在
[设备网络配方](../../devices/tr1200/network/travel-mode/README.md)。
Travelmate 后端遵循 GPL-3.0-or-later，LuCI 前端遵循 Apache-2.0；
rpcd 使用 ISC 许可，iwinfo 使用 GPL-2.0，具体以各源文件的许可声明为准。
原有版权及许可证声明保留，附 GPL 与 Apache 文本；本仓库 MIT 许可证不替代上游许可。
本目录不包含私人 SSID 密码、节点或配置备份。
