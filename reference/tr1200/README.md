# TR1200 1.0 参考资料

本目录保存原始公开资料用于复核。原厂固件和中间固件是厂商二进制，未修改、未执行，
也未刷入设备。下载完整性由 `archives.lock.json` 与 `SHA256SUMS` 记录，首次迁移
仍需核对目标设备当前版本和恢复能力。

- `mt7628an_cudy_tr1200-v1.dts`：OpenWrt 构建提交
  `f5dae5ece4805730c5e2850f8aa84765af2f6b32` 的官方设备树；核心源码快照已保存在
  `../sources/`，由 `../archives.lock.json` 锁定。
- `vendor-R46.dts`：从 Cudy 下载中心链接的 MT7628/MT7621 GPL 包中提取。
- `upstream-support-commit.json`：官方设备支持提交及当时安装说明，属于历史资料。
- `TR1200-V1-intermediate.zip`：Cudy OpenWrt 中间固件目录中的 `TR1200 V1.zip`。
  https://drive.google.com/file/d/1vqg9GMi3LVF6viG7gSDZf6XwlsD88kX_/view
- `TR1200-R46-2.5.41-stock.zip`：Cudy 下载中心 2026-10-26 发布的原厂固件包。
  https://www.cudy.com/cdn/shop/files/TR1200-R46-2.5.41-20261016-130008-flash.zip?v=3071922756898488208

厂商 GPL 原文件名为 `GPL_cudy_openwrt_MT7628_MT7621_20250724.gz`，134,358,230 字节，
超过 GitHub Git 单文件限制，作为 Release 附件 `tr1200-vendor-gpl.tar.gz` 备份。
它是厂商 17.01 系列历史源码，仅供参考，不是本工程官方 25.12.5 的构建输入。
https://drive.google.com/file/d/1sDSWjrw51HYsv-NPoADaDgPwrUE7EtgL/view

注意官方设备树的 `backup` 分区 `reg` 偏移与厂商版本相差一位十六进制零，详见
`devices/tr1200/README.md` 和对应静态检查报告。v0.1.0 保留官方设备树，v0.1.1
采用固定的上游 PR #23812 修正该偏移，保持内核机器码原样。实机核查前不能仅凭
分区名称认定备份范围正确。`openwrt-pr-*.patch` / `.json` 保存本次核对的上游提案，
#22648、#23812 采用其中的 TR1200 部分，#25123 仅归档研究，不应用交换机修改。
