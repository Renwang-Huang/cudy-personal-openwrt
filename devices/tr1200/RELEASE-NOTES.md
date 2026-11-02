# TR1200 v0.1.1 刷写前复核候选

适用 **Cudy TR1200 1.0 / AC1200 旅行路由器**。基于官方 OpenWrt 25.12.5
ImageBuilder，移植两项固定的上游提案：

- PR #22648：补回 `cudy,tr1200` 历史兼容名称，保留 `cudy,tr1200-v1`，移除原厂 `R46` 直接 sysupgrade 身份。
- PR #23812：backup 偏移由 `0xfe000` 修正为 `0xfe0000`。只应用 TR1200 相关修改。

两个 PR 尚未合入。内核机器码、内核模块和整个根文件系统与 v0.1.0 逐字节一致；
DTB 只改两个字节，uImage 重新计算 CRC。每次准备时先验证原始封装能逐字节重现。

中文 LuCI、HTTPS、默认 `10.0.0.1/24`，主机名 `TR1200-Personal`，151 个包及依赖，
无内置密码、私钥、订阅或代理插件。sysupgrade 为 **6,619,419 字节**，SHA-256：

```text
7dec3ae143b5d1f41c6d969e176ff5f6e74b0abf6c9cc69a16e5ce256595a37a
```

## 验证与附件

本地归档 APK、禁用 APK 联网后的重建镜像与首版逐字节一致。
已通过 fwtool / uImage / 分区检查、8 类损坏或不兼容输入拒绝、实际 MIPS 24KEc
用户态 BusyBox / UCI / dnsmasq 检查；个性化脚本的提交、重复执行和 WAN/VLAN 保留通过。
镜像没有已知可触发 SMALL_FLASH 服务问题的 ujail。
原厂恢复文件通过 ZIP、归档 SHA-256 和厂商 MD5；没有启动恢复服务或刷写设备。

附件包含镜像、manifest、SBOM、profiles、静态检查、离线审计和关键修正报告。
工具与 APK 缓存继续复用 v0.1.0 的已锁定附件，`release-assets.lock.json` 精确引用，
不复制改变原始输入。候选复现：

```sh
python3 devices/tr1200/scripts/reproduce-release.py
python3 devices/tr1200/scripts/audit-candidate.py
```

## 明确未通过的实机条件

**没有实际启动、刷写或恢复测试。** 原厂 GUI 不能直接上传此 sysupgrade；先按当前
设备状态核对 Cudy 签名中间固件、真实分区、校准备份及实际 `sysupgrade -T` 结果。
不提供强制刷写方案。

上游 #25123 报告启动期间 LAN/WAN 可能短暂互通，其修复尚有争议，本版保持官方交换机
驱动与端口禁用值，首次启动用隔离电脑接 LAN、WAN 断开。该规程不代表串流问题已修复。
TR1200 为 NOR 单系统，不具备双槽自动回退。

官方恢复为 **WAN + 192.168.1.88 + 匹配原厂 recovery.bin**，依赖 bootloader 和硬件完好；
不能保证任何故障都可恢复。明天到货检查与故障策略见仓库：

- [完整复核与范围](https://github.com/Renwang-Huang/cudy-personal-openwrt/blob/main/devices/tr1200/AUDIT.md)
- [到货与恢复操作单](https://github.com/Renwang-Huang/cudy-personal-openwrt/blob/main/devices/tr1200/RUNBOOK.md)
