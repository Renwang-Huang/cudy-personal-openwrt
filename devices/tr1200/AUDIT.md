# TR1200 1.0 刷写前复核

本次复核结论：**v0.1.1 通过离线检查；实机首次迁移仍需完成到货核查。**
不能凭镜像编译成功、云端产物一致或用户态模拟执行，认定新机一定能启动或恢复。
本次没有连接、重启或刷写真实路由器。

新版 [GitHub 独立环境验证](https://github.com/Renwang-Huang/cudy-personal-openwrt/actions/runs/41443725093)
已通过离线镜像重建、MIPS 用户态与异常输入检查、原厂恢复文件核验。下载云端镜像后
与本地逐字节一致，静态报告和离线审计报告也一致。11 个公开发布附件均已通过完整性核验；完整记录见 `evidence/v0.1.1-github-actions.json` 和发布附件核验记录。

## 已修正

| 项目 | 原候选 v0.1.0 | 当前候选 v0.1.1 | 依据 |
| --- | --- | --- | --- |
| 旧设备名称兼容 | 仅接受 `cudy,tr1200-v1` / `R46` | 接受 `cudy,tr1200-v1` / `cudy,tr1200`，移除原厂 `R46` 直接 sysupgrade 身份 | [上游 PR #22648](https://github.com/openwrt/openwrt/pull/22648) 与仅修改命名的历史提交 |
| backup 分区 | `reg=0xfe000`，与 firmware 重叠 | `reg=0xfe0000`，位于 debug 与 bdinfo 之间 | [上游 PR #23812](https://github.com/openwrt/openwrt/pull/23812) 与厂商 GPL R46 DTS |
| 镜像检查 | 检查镜像头、设备树和组件 | 增加 fwtool 校验、分区连续性、启动服务、ujail 排除与损坏输入拒绝 | 仓库校验脚本与离线审计 |

两个上游 PR 尚未合入，本项目锁定补丁内容和提交，不将其描述为官方发布修复。
PR #23812 仅采用 TR1200 的 hunk，不修改 M1200。

内核来自已锁定的官方 ImageBuilder。先用官方 LZMA、mkimage 工具重封装原始内容，
确认与官方 uImage 逐字节一致，再用 libfdt 的 `fdtput` 修正唯一的 backup `reg` 属性。
原始 DTB 为 9,988 字节，修改后长度不变，只有偏移 3277、3278 两个字节不同。
DTB 前的全部内核内容为 6,994,304 字节，内容保持不变。
根文件系统也与 v0.1.0 逐字节一致，不替换内核模块或无线驱动。
这项修正没有刷写 U-Boot、factory 或 bdinfo 的动作。

## 离线覆盖范围

- 重新检查官方 ImageBuilder、归档 APK 和发布镜像的完整性。
- 用归档缓存、APK `--no-network` 重建 v0.1.1，比较首版与重建镜像的完整内容。
- 校验 fwtool 元数据、uImage 头/数据 CRC、MIPS 架构、LZMA、根文件系统及精确 DTB。
- 核对 16 MiB 闪存的静态分区连续且不重叠，固件范围为 `[0x50000, 0xfd0000)`。
- 检查中文 LuCI、HTTPS、2.4/5 GHz 固件和驱动、USB、交换机及启动服务。
- 检查实际根文件系统的包清单与 manifest 一致，核心程序为 MIPSEL / MIPS32r2 / soft float，内核模块 vermagic 匹配。
- 解包归档的 Cudy 中间固件，确认实际版本为 OpenWrt 23.05.3、旧兼容名 `cudy,tr1200`；
  在 MIPS 用户态运行该中间固件自带的 fwtool，成功提取新版候选元数据。
- 在 QEMU 用户态的 MIPS `24KEc` CPU 上运行镜像自身的 BusyBox、UCI 和 dnsmasq。
  对代表性的首次启动配置执行实际个性化脚本，验证提交、重复执行、LAN 地址、WAN DHCP 和 VLAN 设置。
- 拒绝 8 类故障输入：uImage 头损坏、内核损坏、错误设备元数据、缺失 SquashFS、缺失中文组件、引入 ujail、超出分区容量和关闭 Python 检查。
- 检查设备清单工具拒绝 TR3000、TR3600、原厂 R46 直接 sysupgrade、未知型号、错误或缺失的固件分区范围。
- 原厂恢复包同时通过归档完整性校验、ZIP CRC 和厂商 MD5，生成原样的 `recovery.bin`；不启动 TFTP。

原候选与 v0.1.1 的根文件系统逐字节一致。

## 未覆盖及保留风险

**启动期间 LAN/WAN 串流：** [PR #25123](https://github.com/openwrt/openwrt/pull/25123)
报告 TR1200 在交换机初始化至 VLAN 配置期间可能短暂互通。该 PR 的端口关闭与重新
启用方案存在 failsafe、启动顺序和网口可用性方面的争议，评论提出了驱动层替代方案。
本版不引入未经本机实测的交换机修改；`portdisable` 保持官方 `0x3c`。
初次启动与重启测试只连接隔离电脑的 LAN 口，WAN 保持断开，待 VLAN 与 DHCP 验证后
再连接测试上游。该操作规程不能宣称修复了以后每次重启的串流问题。

**服务崩溃报告：** [issue #22428](https://github.com/openwrt/openwrt/issues/22428)
涉及无 namespaces/cgroups 的 SMALL_FLASH 内核与 ujail。已检查实际文件和包清单：
本镜像没有 `procd-ujail`、`uxc` 或 `/sbin/ujail`；保留官方 `procd-seccomp`，两者不能混淆。
这排除了报告中的已知触发条件，不代表 dnsmasq 的真实启动和 DHCP 已通过硬件测试。
后续安装插件仍需检查是否引入不受内核支持的 jail。

**仍需实机：** 完整型号与硬件版本、Flash 型号、bootloader 签名行为、原厂至中间
固件迁移、在设备上执行 sysupgrade 检查、校准/MAC 数据读取、以太网实际端口映射、
无线射频、USB 负载、温度、断电与恢复。QEMU 用户态没有模拟 MT7628 的整机或闪存。

## 明天刷写前的条件

按 [RUNBOOK.md](RUNBOOK.md) 核查：物理身份、原厂验收、恢复材料、只读清单、关键备份、
镜像完整性、实际设备上的 `sysupgrade -T` 及隔离网线/稳定供电。
任何身份、分区或设备检查异常，先停止迁移并分析，不使用强制选项绕过。
