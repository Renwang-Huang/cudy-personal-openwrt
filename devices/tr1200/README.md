# Cudy TR1200 1.0 最小定制系统

对应官方页面中的橙色 **TR1200 1.0 / AC1200 Wi-Fi Travel Router**。
使用官方 OpenWrt 25.12.5 的 `ramips/mt76x8`、`cudy_tr1200-v1` profile；
不修改内核、设备树、分区布局或镜像支持的设备名称。
这是个人定制候选镜像，尚未完成目标设备的启动和迁移验证。

| 项目 | 配置 |
| --- | --- |
| CPU | MediaTek MT7628AN，580 MHz 单核 MIPS |
| 内存 / 闪存 | 128 MiB RAM / 16 MiB SPI NOR |
| 有线 | 一个百兆 WAN、一个百兆 LAN |
| 无线 | 2.4 GHz MT7628、5 GHz MT7613BEN，Wi-Fi 5 |
| USB | USB 2.0 数据口；USB-C 供电 |
| 系统 | 中文 LuCI、HTTPS、基础路由、防火墙、IPv6、无线和 USB 驱动 |
| 默认管理配置 | `10.0.0.1/24`，主机名 `TR1200-Personal` |

沿用官方首次启动流程设置管理密码与无线。不内置密码、私钥、代理订阅或额外代理插件。
连接初始设置时使用 LAN 网线，并避免与现有同为 `10.0.0.1` 的路由器接入同一网络。
USB 文件共享、VPN、代理及其他插件后续按空间和性能需求添加；保留拨动开关输入，
不预设原厂模式切换或 VPN 切换动作。Wi-Fi 的 DFS、无线中继与实际吞吐需另行验证。

候选发布：[tr1200-v0.1.0-candidate](https://github.com/Renwang-Huang/cudy-tr3000-personal-openwrt/releases/tag/tr1200-v0.1.0-candidate)。
构建产物、精确包版本、校验值与验证状态见发布附件和 `evidence/`。
首版镜像 6,619,411 字节（约 6.31 MiB），共 151 个包及依赖。
本地使用归档 APK 并禁止其联网后重建，镜像与首版逐字节一致。
SHA-256：`61b98e0139bfc6c850821036c4b8733cb73fff9634d6965f31951fd47ceff74f`。
已通过 [GitHub 独立环境的镜像重建](https://github.com/Renwang-Huang/cudy-tr3000-personal-openwrt/actions/runs/41398059150)，
使用归档 ImageBuilder 与 APK 缓存并禁用 APK 联网后，得到相同 SHA-256。
全部 10 个发布附件的 GitHub SHA-256 均与本地一致，匿名下载已核验。
证据见 `evidence/github-actions-reproduction.json` 和 `evidence/github-release-assets.json`。

## 构建与复现

复用已校验的官方 ImageBuilder，不需要自行移植 TR3000 或 TR3600 的硬件支持。
以普通用户在 Linux x86_64 上安装官方 ImageBuilder 主机依赖，另需 `zstd` 和
`squashfs-tools`。从仓库根目录运行：

```sh
python3 devices/tr1200/scripts/prepare.py
bash devices/tr1200/scripts/build.sh
python3 devices/tr1200/scripts/verify-image.py
```

输出在 `output/tr1200/`，TR1200 的配置、叠加文件、构建目录和输出均独立保存。
构建脚本没有连接或刷写设备的动作。修改 `config.json` 增加用户态插件，编辑
`files/etc/uci-defaults/99-personalize` 调整首次启动配置，再重新构建。

要精确复现已发布的首版，运行：

```sh
python3 devices/tr1200/scripts/reproduce-release.py
```

它校验归档的 ImageBuilder 和 APK 缓存，以 `--no-network` 禁止 APK 包管理器联网，
重新生成镜像并比较首版 SHA-256。普通构建命令仍会使用官方软件源的当前包版本；
复现脚本专用于归档首版，修改配置后其原始镜像哈希检查会按预期失败。
SBOM 含生成时间和随机 UUID，不承诺 SBOM 文件本身逐字节可复现。

这是用官方预编译组件重建镜像；不等同于从所有组件的源码完成独立编译。
仓库已归档对应 OpenWrt 核心源码及 feed 参考，具体软件包版本以本版 `.manifest`
和归档 APK 为准，不能仅凭 feed 快照声称逐包源码构建已验证。
OpenWrt 25.12 使用 APK；旧系统的 IPK/opkg 插件与软件源不能直接复用。
内核模块需严格匹配本版 kernel 的版本和 ABI。

## 首次迁移与已知限制

**候选 sysupgrade 不能直接当作 Cudy 原厂签名固件上传。** 官方 Wiki 描述了 Cudy
签名中间固件路径，也描述了 UART/TFTP 路径，但还需按实机当前系统和 bootloader
状态核查。发布本镜像不代表对任何版本的原厂固件迁移成功。

首次迁移前必须备份配置、完整闪存及设备校准数据，核对型号、`board_name`、
真实分区范围与恢复路径。保留官方校验，不添加 `cudy,tr1200` 旧名称来绕过检查。
上游 issue #22640 记录了中间固件使用旧名称 `cudy,tr1200`、新版仅接受
`cudy,tr1200-v1` / `R46` 的差异；不能把强制升级当作已验证的解决方案。

**上游设备树还存在一处需要实机核对的地址差异：** `partition@fe0000` 的 `backup`
分区 `reg` 写为 `0xfe000`，而厂商 GPL 的 R46 设备树写为 `0xfe0000`。
本版保留官方二进制并在检查报告中显式记录这一差异；不能按 OpenWrt 中的
`backup` 分区名称推断已正确备份了闪存末尾的真实 backup 区域。
固件可写分区仍为 `[0x50000, 0xfd0000)`；其余静态分区在官方设备树中标记只读。
这不替代实机验证或独立的完整闪存备份。

TR1200 是 NOR/JFFS2 单系统布局，没有 TR3600 的 UBI 双槽机制。
仅计算镜像大小和剩余分区容量不能保证运行时 RAM、可写空间或代理性能。
Wi-Fi、LAN/WAN、USB、LED、按键、掉电恢复及实机升级均需在目标 TR1200 上验证。

## 参考与备份

- [Cudy 产品页面](https://www.cudy.com/en-us/products/tr1200-1-0)
- [Cudy 下载中心](https://www.cudy.com/en-us/pages/download-center/tr1200-1-0)
- [OpenWrt Wiki 与首次安装说明](https://openwrt.org/toh/cudy/tr1200)
- [OpenWrt 官方固件和 ImageBuilder](https://downloads.openwrt.org/releases/25.12.5/targets/ramips/mt76x8/)
- [官方首次设备支持提交](https://github.com/openwrt/openwrt/commit/f1091ef7ac3596f1e401b918a36273672acbe389)
- [中间固件名称不兼容问题 #22640](https://github.com/openwrt/openwrt/issues/22640)

`reference/tr1200/` 保存官方与厂商设备树、原厂包、中间固件和来源校验清单。
超过 GitHub 单文件限制的厂商 17.01 GPL 包保存在本设备 Release 中，来源和 SHA-256
由 `reference/tr1200/archives.lock.json` 锁定；它只作历史参考，不参与本版构建。
项目原创脚本和文档遵循仓库 MIT 许可证，上游组件及厂商包遵循各自许可证。
