# TR1200 v0.1.0 最小定制候选

面向橙色 **Cudy TR1200 1.0 / AC1200 Wi-Fi Travel Router**，使用官方 OpenWrt
25.12.5 的 `ramips/mt76x8` / `cudy_tr1200-v1` ImageBuilder。内核、设备树及
设备兼容名称保持官方原样。

包含中文 LuCI、HTTPS 和基础联网组件，默认 `10.0.0.1/24`，主机名
`TR1200-Personal`，没有预置密码、私钥、订阅或代理插件。

## 附件

- `*-squashfs-sysupgrade.bin`：个人定制系统候选镜像。
- `.manifest`、`.bom.cdx.json`、`profiles.json`：包版本、许可证及产物信息。
- `tr1200-verification.json`：设备元数据、uImage CRC、官方内核与设备树一致性、
  分区、空间余量、必要驱动及个性化文件的检查结果。
- `openwrt-imagebuilder-*.tar.zst` 和 `openwrt-25.12.5-tr1200-package-cache.tar.zst`：
  精确复现所用的官方 ImageBuilder 和软件包缓存。
- `tr1200-vendor-gpl.tar.gz`：Cudy 下载中心提供的 17.01 GPL 历史源码参考，不参与构建。
- `TR1200-SHA256SUMS.txt`：发布附件校验清单。

源代码参考、配置、复现脚本、来源与校验锁文件保存在仓库 `devices/tr1200/`
和 `reference/`；TR3000 和 TR3600 的配方独立保留。

系统镜像：6,619,411 字节（约 6.31 MiB），包含 151 个包及依赖。
SHA-256：`61b98e0139bfc6c850821036c4b8733cb73fff9634d6965f31951fd47ceff74f`。
本地使用归档 APK 并禁用其联网后，重建镜像与首版逐字节一致。
估算可写区域约 9.19 MiB，尚未扣除 JFFS2 开销。

## 刷写前提与限制

**尚未刷入设备，未验证实机启动、联网、无线、USB 或恢复。** 本镜像不是厂商签名
factory 固件，不能直接作为原厂后台升级文件。Cudy 中间固件和新版 OpenWrt
存在旧、新 board_name 不一致的已知问题（上游 #22640），本版没有绕过该检查。

官方 DTS 的 `backup` 分区节点地址 `@fe0000` 与 `reg=0xfe000` 不一致；厂商 R46
DTS 为 `0xfe0000`。本版保留官方内核，并明确记录该问题。首次迁移前需核对真实
闪存布局、保存完整闪存与校准数据；不能仅依赖名称为 backup 的分区完成备份。
TR1200 是 16 MiB NOR 单系统布局，不提供 TR3600 式双槽回退。

## 复现

```sh
python3 devices/tr1200/scripts/reproduce-release.py
```

脚本校验归档输入，以 APK `--no-network` 重建镜像，运行静态检查并比较原始 SHA-256。
这里只重建官方预编译组件组成的镜像，不声称独立源码编译或实机验证完成。
详细配置和常规构建命令见 `devices/tr1200/README.md`。
