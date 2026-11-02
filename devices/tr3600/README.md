# Cudy TR3600 v1 个性化系统

本设备对应 Cudy 的 **BE3600 2.5G Wi-Fi 7 Travel Router / TR3600 1.0**。
它使用 MT7987B、MT7990AN、512 MiB DDR4、256 MiB NAND、双 2.5G 网口和 PWM 风扇。

本配方从官方 OpenWrt 25.12.5 对应提交构建，并增加尚未合入的 TR3600 设备支持及硬件修正。
因此它是基于官方稳定版源码的实验适配，不是 OpenWrt 官方支持的发布镜像。
首版包含中文 LuCI、HTTPS 和基础联网功能，默认管理地址 `10.0.0.1/24`，
主机名 `TR3600-Personal`。不预装代理插件，不嵌入密码、密钥或订阅。

候选产物：[tr3600-v0.1.0-candidate](https://github.com/Renwang-Huang/cudy-personal-openwrt/releases/tag/tr3600-v0.1.0-candidate)。
sysupgrade 为 10,987,804 字节，SHA-256 为
`71911f83ebf60dfd70e72916c02306961b36d5b399dd4056aeb7964da65c8dbe`。
本地连续两次完整构建的系统与 initramfs 镜像分别一致；完整证据见 `evidence/`。
已通过 [GitHub 独立环境的发布镜像静态检查](https://github.com/Renwang-Huang/cudy-personal-openwrt/actions/runs/41394843131)，
并核对全部 13 个公开附件的 GitHub SHA-256 与本地一致。云端检查下载已发布的镜像，
检查设备树、软件包、个性化文件和槽位 stub 逻辑；它没有执行完整源码重建。
独立主机源码重建、实际设备启动和刷写均未验证。

## 源码与补丁

`build.lock.json` 锁定基础源码、工具链、PR、硬件修正及官方开发包；
`config/feeds.conf` 锁定五个官方 feed 的提交。

1. `001`：OpenWrt PR #24596 的 TR3600 v1 设备支持。
2. `002`：社区的红白 LED、PWM0、Wi-Fi MAC 和温控修正。
3. `003`：Cudy 官方开发包中的 UBI rootfs 选择与 `boot_param` 内核补丁。
4. `004`：本工程的双槽升级集成、UBI 环境卷定位，以及本基础源码的 PWM 参数单元修正。
5. `005`：移植已合入上游的 PR #24005，在 APK 打包时固定文件时间戳，避免重复构建时
   包校验标识变化。只调整原补丁的上下文，保留其单行行为。

构建脚本还通过上游提供的 `package/system/ca-certificates/clean` 目标重新准备证书包，
防止 Debian 的证书转换脚本在增量构建时把已有证书再次生成为 `_2.crt`，导致信任库重复。
此步骤只处理本工程的证书包构建目录，不触及主机或路由器的证书。

`source-overlay/package/kernel/cudy-bootcount/` 来自 Cudy GPL 包中的 MediaTek
BSD-3-Clause 启动计数复位模块，仅将旧 `file_operations` 接口改为 Linux 6.12 的
`proc_ops`。原文件保存在 `reference/tr3600/`。成功启动后，仅当厂商启动参数要求
复位计数时，启动服务才触发该接口。

## 双槽行为与边界

厂商在一个 UBI 分区中保留 `u-boot-env`、`kernel`、`kernel2`、`rootfs`、`rootfs2`
和共享的 `rootfs_data`。本工程读取 bootloader 传入的当前槽与目标槽，检查卷名、
环境卷和运行槽一致性。只允许写另一槽；写入并读回校验内核、根文件系统后，才切换
启动槽。`BL2`、`Factory`、`bdinfo`、`FIP` 不在升级写入范围。

**共享 `rootfs_data` 不提供独立的 A/B 配置回退。** 上游 NAND 升级流程会重建共享
可写数据卷，所以保留另一槽镜像不等于保留另一套配置。刷写前必须另存设备配置和
关键分区。缺少或不一致的槽位参数会拒绝升级，不能通过强制选项证明可用。

本机 stub 检查覆盖槽位方向、异常拒绝、写入及校验失败后不切槽；这不能替代真实
闪存掉电测试。风扇转速、温控、WAN/LAN、无线、Wi-Fi 7/MLO、原厂迁移和恢复方式
都必须在目标 TR3600 v1 上另行验证。不要刷入 TR3000 或 WR3600。

## 构建

Linux x86_64 主机需要 OpenWrt 构建依赖，另需 `clang`/LLVM（提供 BPF 编译器）、
`zstd` 和 `squashfs-tools`。以普通用户运行：

```sh
python3 devices/tr3600/scripts/prepare.py
python3 devices/tr3600/scripts/restore-downloads.py
JOBS=6 bash devices/tr3600/scripts/build.sh
python3 devices/tr3600/scripts/verify-image.py
```

产物在 `work/tr3600-source/bin/targets/mediatek/filogic/`；包括 sysupgrade、
initramfs、软件包清单和校验文件。准备脚本只获取并校验源码、应用补丁和配置，
构建脚本没有连接路由器或刷写动作。临时构建目录及私人备份均不进入 Git。

采用官方预编译工具链的完整源码构建。上游禁止在 external-toolchain 配置下导出
ImageBuilder，因此本配方保留完整源码、补丁、工具链和下载缓存，不承诺可直接使用
TR3000 的 ImageBuilder 来重建。普通用户态插件使用官方 25.12.5 软件源；内核模块
必须与本配方的完整 kernel 版本匹配，不能强制安装官方或其他固件的 kmod。

## 参考

`restore-downloads.py` 从本候选 Release 获取并校验源码下载缓存，减少上游站点变化对
复现的影响。没有缓存时也可跳过此步，由 OpenWrt 按包配方的版本和校验值下载。

- https://www.cudy.com/en-us/products/tr3600-1-0
- https://www.cudy.com/zh-cn/pages/download-center/tr3600-1-0
- https://github.com/openwrt/openwrt/pull/24596
- https://github.com/openwrt/openwrt/pull/24596#issuecomment-5226298465
- https://github.com/hyqhyq3/openwrt-cudy-tr3600
- https://github.com/openwrt/openwrt/pull/24005
