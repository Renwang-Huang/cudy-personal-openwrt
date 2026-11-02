# TR3600 v0.1.0 实验候选

面向 **Cudy TR3600 1.0 / BE3600 2.5G Wi-Fi 7 Travel Router**，不能用于 TR3000 或 WR3600。

基于官方 OpenWrt 25.12.5 对应源码与固定 GCC 14.3.0 工具链，加入未合入的设备适配、
社区硬件修正、Cudy 双槽参数补丁，以及厂商启动计数模块的 Linux 6.12 移植。
包含中文 LuCI、HTTPS、基础联网功能，默认地址 `10.0.0.1/24`，主机名 `TR3600-Personal`。
没有预装代理插件，没有嵌入密码、私钥或订阅。

## 产物与验证

- `*-squashfs-sysupgrade.bin`：候选系统镜像。
- `*-initramfs-kernel.bin`：候选内存启动镜像；不是可直接上传原厂后台的签名固件。
- `.manifest`、`profiles.json`、`tr3600-verification.json`：实际软件包和静态检查结果。
- `tr3600-v0.1.0-source-cache.tar.zst`：按 OpenWrt 配方下载的固定版本源码缓存，含 Linux 和无线固件包。
- `openwrt-toolchain-*.tar.zst`：实际使用且已校验的官方工具链。
- 设备源码、补丁、官方开发包、GPL 包和校验值在仓库 `devices/tr3600/`、`reference/`。

已完成本地源码编译、设备树及镜像静态检查、槽位状态与写入失败路径的 stub 检查。
产物大小和构建重复性结果以附件及仓库 evidence 为准。

已通过 [GitHub 独立环境的发布镜像静态检查](https://github.com/Renwang-Huang/cudy-personal-openwrt/actions/runs/41394843131)：
重新下载公开附件，检查设备树、软件包、个性化文件及槽位 stub 逻辑，并核对发布镜像内容。
全部 13 个附件均已通过完整性检查。此检查没有执行完整源码重建。

最终 sysupgrade：10,987,804 字节（约 10.48 MiB）。
连续两次本地完整构建的 sysupgrade 和 initramfs 分别逐字节一致。
回移了已合入上游的 APK 时间戳修复，并通过标准包清理目标避免增量构建重复生成
CA 证书；最终信任库含 121 个不重复的证书。独立主机源码重建未验证。

## 实机边界

**没有刷入 TR3600，没有完成实机启动、无线、MLO、双 2.5G、风扇、掉电或回退测试。**
这不是 OpenWrt 官方发布的 TR3600 稳定版，也不是已经验证可直接强制刷写的固件。
首次刷入需要按当前原厂/中间固件状态、UBI 卷及启动槽另行核对。

槽位升级实现会在校验目标槽写入内容后才改变启动槽；`rootfs_data` 仍为两个槽共享，
因此另一槽系统镜像不能代表独立的配置回退。刷写前必须保存设备配置和关键分区。
不提供自动刷写命令，也未修改真实路由器。

## 复现

参照 `devices/tr3600/README.md`，依次运行 `prepare.py`、`restore-downloads.py`、
`build.sh`、`verify-image.py`。缓存恢复脚本先检查附件完整性，再恢复 `dl/`。
固定 feed、源码与补丁，使用附带工具链。内核模块必须与本次完整 kernel 版本匹配。
本配方不导出或复用 TR3000 的 ImageBuilder；完整源码构建的独立主机复现尚未验证。
