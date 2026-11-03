# TR1200 · PassWall 精简方案

一台 **Cudy TR1200 v1 / 128 MiB RAM / 16 MiB NOR** 已完成保留配置升级和实机检查。
使用 PassWall 26.10.29-r1、中文包，以及自行编译的 sing-box 1.13.21 精简核心。
后续已完成真实节点导入与上游接入测试；实际节点、无线密码和凭据仅保存在设备与私有备份中。
公开配方不嵌入这些数据。现场状态和验证边界见 [实机记录](FIELD-TEST.md)。

## 裁剪内容

| 组件 | 处理 |
| --- | --- |
| 代理核心 | 按官方稳定软件源的版本构建，保留 QUIC、uTLS、VLESS、VMess、Trojan、Hysteria2 |
| 无关核心功能 | 不启用 Tailscale、WireGuard、gVisor、ACME、Clash API 等可选构建标签 |
| 编译与压缩 | MIPS 小端软浮点、关闭内联、剥离调试信息、UPX 压缩，核心文件约 4.83 MiB |
| 内存设置 | 单运行线程，Go 内存目标 24 MiB，提早回收；这是软目标，实际进程内存可能更高 |
| DNS | dnsmasq 2.93 自编译 DHCP/nftset 版本，保留基础 IPv6；不启用 DNSSEC、ipset、连接跟踪、权威 DNS、TFTP、DHCPv6 |
| 系统 | 保留防火墙、SSH、中文 LuCI、Argon、双频无线驱动及基础路由功能 |

原基础固件的 dnsmasq 同样未启用 DHCPv6，IPv6 RA/DHCPv6 仍由原有 odhcpd 负责。
本次没有通过移除基础网络或管理服务换取空间。将组件重新压缩进只读镜像后，
现场可写空间约 2 MiB，实际余量随配置和规则增长而变化。

上游完整 sing-box 包超出此设备内置闪存容量。**请勿通过 PassWall 的组件更新功能用完整核心覆盖精简核心，
也不要安装整套 GeoIP/GeoSite 大数据库。** 更新核心需沿用这里的构建参数并重新评估体积与协议兼容性。

## 当前使用

在管理页面选择 **服务 → PassWall**。先导入自己的订阅或节点，再选择 Sing-Box 类型的可用节点。
后续已从现有路由器导入两条 VLESS Reality 节点和一条 TUIC 节点，使用原有自动测速组合。
VLESS 与 TUIC 已分别进行真实 HTTPS 传输测试；节点服务和证书校验均由 TR1200 自己处理。
未新增或测试订阅服务。内存适配与运行状态检测修正见 [实际节点运行适配](runtime/README.md)。
外置 USB 存储不是本方案的运行条件。

设备已采用 [固定版本维护](../fixed-release/README.md)，没有有效在线软件源；
当前软件版本见 [现场包清单](../fixed-release/installed-packages.json)。后续升级或个性化由设备所有者发起，
按仓库源码和配方构建后安装。节点、订阅及分流规则仍可按需设置；这些运行数据不属于软件包源。

## 源码和构建

遵循上游功能开关进行裁剪，未修改协议实现。完整 sing-box 和 PassWall 固定版本源码、
dnsmasq 原始源码与定制配方保存在 `reference/passwall/`。
固定输入见 [sources.lock.json](sources.lock.json)，核心参数见 [core-build.json](core-build.json)，
DNS 功能选择见 [dnsmasq.config](dnsmasq.config)。

在 Linux x86_64 主机上，从仓库根目录运行：

```sh
python3 devices/tr1200/passwall/build-core.py
python3 devices/tr1200/passwall/build-dns.py
```

核心构建需要已安装 Go，工具链会按固定版本自动下载；DNS 构建使用官方 MIPS SDK。
构建日志和依赖缓存保存到本地 `work/`。依赖模块由上游 `go.mod` 和 `go.sum` 固定，
未将 Go 模块缓存或全部第三方模块源码复制到本仓库。

`packages.lock.json` 留存实机镜像的软件包版本，`config.json` 留存独立 ImageBuilder 配方。
整合镜像使用既有 TR1200 官方 ImageBuilder 的两项设备修正、精简核心 APK、
自编译 `dnsmasq-full` 和固定版本软件包；旧 v0.1.1 的配方与发布产物保持原样。
这里提供源码级构建参数和现场记录，尚未完成从全新主机到镜像的独立重建验证。
核心已使用归档源码和公开脚本重新构建，并与实机使用的核心逐字节比较一致。

`config.json` 的 `files_overlays` 声明了关闭运行时软件源的最后一层文件叠加目录。
组装后续镜像时需要实际应用该目录；此声明不是完整镜像构建脚本，也没有改写旧发布镜像。

原始候选镜像、离线包缓存、SDK、构建日志及设备备份另存本机，未在本次新增固件 Release。
生成镜像时应使用 `umask 022`，规范叠加目录权限，并重新执行设备兼容性与空间检查。
不要在设备上直接安装全部构建依赖包；只读系统的空间回收需要完整镜像升级。

## 来源与许可

- [PassWall](https://github.com/Openwrt-Passwall/openwrt-passwall/releases/tag/26.10.29-1)，GPL-3.0。
- [sing-box 1.13.21](https://github.com/SagerNet/sing-box/tree/v1.13.21)，GPL-3.0-or-later。
- [OpenWrt](https://github.com/openwrt/openwrt)，官方 SDK 和 dnsmasq 配方沿用上游许可。
- [UPX](https://github.com/upx/upx)，作为构建压缩工具使用。

上游许可证随源码归档保存，本仓库许可证不替代组件各自的许可证。
