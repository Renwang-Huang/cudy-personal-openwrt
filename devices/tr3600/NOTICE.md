# 来源和许可证

- 基础源码：OpenWrt，提交 `f5dae5ece4805730c5e2850f8aa84765af2f6b32`，保留其原许可证。
- 设备补丁：soapmancn 的 OpenWrt PR #24596，提交 `046aec0dccd90f5a156cb8e9725c121c81955dd3`。
- 硬件修正：hyqhyq3/openwrt-cudy-tr3600，提交 `a9aa917c3a3fe3a2fb88572b77aea4f48a635549`。
- APK 时间戳修正：OpenWrt PR #24005（已合入），按本基础源码的上下文回移。
- 双槽内核参数、启动协议参考：Cudy 官方 TR3600 开发包和 GPL 包；原文件保存在仓库参考目录。
- 启动计数模块：MediaTek Inc. / Weijie Gao，BSD-3-Clause；本工程将 proc 接口移植到 Linux 6.12。
- 本工程的 `files/lib/upgrade/cudy-tr3600.sh` 按 GPL-2.0-only 提供，并调用上游 OpenWrt NAND 升级实现。
- 其余本工程原创构建与验证脚本、文档使用仓库 MIT 许可证。根目录 MIT 不替代上述上游许可证。

无线芯片固件等组件沿用 linux-firmware/mt76 中相应文件的分发许可证。
本工程不会因为归档 GPL 源码而声称全部芯片固件均可从源码重新编译。
