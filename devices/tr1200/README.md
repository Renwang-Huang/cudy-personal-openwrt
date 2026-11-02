# Cudy TR1200 1.0 最小定制系统

[返回项目首页](../../README.md) · [刷写前复核](AUDIT.md) · [到货与恢复操作单](RUNBOOK.md)

对应橙色 **TR1200 1.0 / AC1200 Wi-Fi Travel Router**，使用 OpenWrt 25.12.5 的
`ramips/mt76x8` / `cudy_tr1200-v1` 官方 ImageBuilder，并采用两项尚未合入的上游
设备修正：历史 board_name 兼容、backup 分区偏移。它是个人定制候选镜像，尚未通过实机验证。

| 项目 | 配置 |
| --- | --- |
| CPU | MediaTek MT7628AN，580 MHz 单核 MIPS |
| 内存 / 闪存 | 128 MiB RAM / 16 MiB SPI NOR |
| 有线 | 一个百兆 WAN、一个百兆 LAN |
| 无线 | 2.4 GHz MT7628、5 GHz MT7613BEN，Wi-Fi 5 |
| USB | USB 2.0 数据口；USB-C 供电 |
| 系统 | 中文 LuCI、HTTPS、基础路由、防火墙、IPv6、无线和 USB 驱动 |
| 默认管理配置 | `10.0.0.1/24`，主机名 `TR1200-Personal` |

首版不内置密码、私钥、订阅或代理插件。首次设置使用隔离电脑和 LAN 网线，WAN 暂时断开，
避免与现有 `10.0.0.1` 路由器冲突，也避免启动期交换机串流。无线和管理密码首次启动自行设置。
USB 共享、VPN 等插件后续按空间及性能添加；保留拨动开关输入，不预设模式切换行为。

## 当前候选与验证

当前版本：[tr1200-v0.1.1-candidate](https://github.com/Renwang-Huang/cudy-personal-openwrt/releases/tag/tr1200-v0.1.1-candidate)。
系统镜像 **6,619,419 字节（约 6.31 MiB）**，包含 151 个包及依赖，估算可写区域约
9.19 MiB，未扣除 JFFS2 开销。SHA-256：

```text
7dec3ae143b5d1f41c6d969e176ff5f6e74b0abf6c9cc69a16e5ce256595a37a
```

v0.1.1 修正了旧中间固件使用 `cudy,tr1200` 时无法通过新版元数据检查的问题，
并将 backup 偏移由 `0xfe000` 修正为 `0xfe0000`。同时移除原厂 `R46` 的直接
sysupgrade 兼容身份，保留原厂至 Cudy 签名中间固件的迁移步骤。
补丁固定为 [PR #22648](https://github.com/openwrt/openwrt/pull/22648)、
[PR #23812](https://github.com/openwrt/openwrt/pull/23812) 的已归档内容。

内核机器码和根文件系统与 v0.1.0 逐字节一致，DTB 只有 backup `reg` 中的两个字节改变。
本地归档缓存离线重建、uImage/fwtool/分区检查、8 类异常输入拒绝和实际 MIPS 用户态
程序执行通过。具体证据、未覆盖范围及交换机串流风险见 [AUDIT.md](AUDIT.md)。

[v0.1.0](https://github.com/Renwang-Huang/cudy-personal-openwrt/releases/tag/tr1200-v0.1.0-candidate)
保留原官方定义和旧镜像证据，供历史复现；当前首次迁移评估使用 v0.1.1。
旧版已完成[云端离线镜像复现](https://github.com/Renwang-Huang/cudy-personal-openwrt/actions/runs/41398059150)，
不能把旧版的验证记录当作新版的云端结果。

## 构建与复现

在 Linux x86_64 上以普通用户运行，准备官方 ImageBuilder 依赖，另需 `zstd`、
`squashfs-tools`、`device-tree-compiler`（提供 fdtput）和 `patch`。
从仓库根目录运行：

```sh
python3 devices/tr1200/scripts/prepare.py
bash devices/tr1200/scripts/build.sh
python3 devices/tr1200/scripts/verify-image.py
```

输出为 `output/tr1200-v0.1.1/`，构建目录为 `work/tr1200-v0.1.1-imagebuilder/`。
准备脚本从校验后的官方压缩包创建独立工作区，应用固定的两项设备修正。
先验证原始 uImage 重封装逐字节一致，再修正 DTB，保留时间戳、头信息和机器码。

精确复现发布候选：

```sh
python3 devices/tr1200/scripts/reproduce-release.py
```

脚本验证 ImageBuilder 与归档 APK 缓存，禁止 APK 联网，重建后比较发布哈希。
v0.1.1 复用 v0.1.0 Release 中不可变的工具与软件包缓存，锁文件引用精确 URL 和 SHA-256。
普通构建仍会获取官方源的当前包；修改 `config.json` 或叠加文件后应走普通构建流程。
SBOM 的生成时间和 UUID 不承诺逐字节复现。

离线强化检查：

```sh
# 另需 qemu-user 或 qemu-user-static；不需要 root，也不连接路由器。
python3 devices/tr1200/scripts/audit-candidate.py
python3 devices/tr1200/scripts/prepare-recovery.py
```

这里是使用官方预编译组件组装镜像，不声称所有组件均已独立从源码编译。
源码、feed 和厂商参考的来源锁文件保存在 `reference/`；具体包版本以 manifest 和归档 APK 为准。
25.12 使用 APK，旧 IPK/opkg 包不能直接复用；内核模块必须匹配完整版本和 ABI。

## 首次迁移与恢复

先阅读 [RUNBOOK.md](RUNBOOK.md)，完成原厂验收、恢复文件准备、设备清单和关键数据备份。
`collect-readonly.sh` 只采集目标 OpenWrt 的型号、版本和分区元数据；`check-device.py`
校验已采集的信息，不连接或刷写设备，也不自动批准刷写。

候选 sysupgrade 不是 Cudy 原厂签名固件。只有确认的新机进入匹配 OpenWrt 中间系统、
分区/备份与镜像核对通过，且实际 `sysupgrade -T` 成功后，才有条件评审实际迁移。
TR1200 官方恢复使用 **WAN 口**、电脑 **192.168.1.88**、匹配原厂 **recovery.bin**。
TFTP 请求不等同于已验证完整恢复；bootloader/Flash 损坏仍可能需要维修。

TR1200 是单系统 NOR/JFFS2 布局，无 TR3600 双槽机制。交换机启动期 LAN/WAN 串流仍是
待实机确认的问题，本版不套用有争议的端口关闭方案。无线、网口、USB、按键、真实启动
及恢复均未完成硬件验证。Cudy 对第三方固件的保修声明见操作单引用的官方页面。

## 参考与许可

- [Cudy 产品页面](https://www.cudy.com/en-us/products/tr1200-1-0)
- [Cudy 下载中心](https://www.cudy.com/en-us/pages/download-center/tr1200-1-0)
- [Cudy 官方恢复教程](https://www.cudy.com/zh-cn/blogs/faq/how-to-recovery-the-cudy-router-from-openwrt-firmware-to-cudy-official-firmware)
- [OpenWrt Wiki](https://openwrt.org/toh/cudy/tr1200)
- [官方 ImageBuilder 和固件](https://downloads.openwrt.org/releases/25.12.5/targets/ramips/mt76x8/)
- [上游首次迁移问题 #22640](https://github.com/openwrt/openwrt/issues/22640)
- [启动期交换机串流 #25123](https://github.com/openwrt/openwrt/pull/25123)
- [MT76x8 / ujail 问题 #22428](https://github.com/openwrt/openwrt/issues/22428)

`reference/tr1200/` 保存原厂、中间固件、厂商 DTS 与上游补丁证据。厂商 GPL 历史包
超过 GitHub 单文件限制，保存在 v0.1.0 Release 并由锁文件引用，不参与本候选构建。
原创脚本和文档遵循 MIT，上游及厂商资料遵循各自许可证。
