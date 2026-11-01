# Cudy TR3000 256MB 个性化镜像

公开仓库：https://github.com/Renwang-Huang/cudy-tr3000-personal-openwrt

基于官方 OpenWrt 25.12.5、`mediatek/filogic` 的 ImageBuilder 工程。
首版保留官方硬件定义，加入中文 LuCI 和 HTTPS 管理界面，默认地址为
`10.0.0.1/24`，主机名为 `TR3000-Personal`。不嵌入管理密码、Wi-Fi 密码、
代理订阅或其他私人凭据。Wi-Fi 和管理密码按官方首次启动流程设置。

## 构建输入

- `config.json`：设备 profile 和附加软件包。
- `files/`：写入镜像的个性化文件。
- `scripts/build.sh`：使用官方 ImageBuilder 生成镜像；不包含刷写动作。
- `scripts/prepare.py`：下载并校验锁定的官方 ImageBuilder。
- `scripts/verify-image.py`：检查候选镜像的设备树、分区、软件包和个性化文件。
- `scripts/reproduce-release.py`：使用 Release 保存的软件包缓存离线重建首版。
- `evidence/`：下载校验值、官方 profile 和设备树参考。
- `reference/`：固定提交的 OpenWrt、软件包 feeds、旧 Kwrt 源码备份及校验清单。
- `.github/workflows/build.yml`：可手动运行的 GitHub Actions 构建流程。

官方 ImageBuilder：
`openwrt-imagebuilder-25.12.5-mediatek-filogic.Linux-x86_64.tar.zst`

SHA-256：
`7fb6cf626582ebcbfb46974da48c1eae577213f38879eaf6b1d982041e843461`

下载源：
https://downloads.openwrt.org/releases/25.12.5/targets/mediatek/filogic/

在已安装 ImageBuilder 主机依赖和 `squashfs-tools` 的 Linux x86_64 机器运行：

```sh
python3 scripts/prepare.py
bash scripts/build.sh
python3 scripts/verify-image.py
```

构建输出位于 `output/`。构建成功只证明镜像生成成功，不能证明实机运行或迁移成功。

## 当前 Kwrt 与候选镜像的迁移差异

当前设备标识为 `cudy,tr3000-v2-mod`，官方目标为
`cudy,tr3000-256mb-v1`，官方 `supported_devices` 尚不包含当前标识。
当前 UBI 分区起点是 `0x5c0000`、长度是 `0xe280000`（226.5 MiB）；
官方分区起点相同，长度为 `0xe600000`（230 MiB）。

本工程保留这两项差异，未通过修改镜像元数据绕过设备检查。
输出仅作为待评审的候选镜像。刷写前需完成配置、软件清单、关键分区备份，
并解决 UBI 分区扩大、卷布局、配置迁移和恢复方式的核查。

日后添加插件，修改 `config.json` 中的 `packages`；修改主机名、管理地址或
默认界面语言，编辑 `files/etc/uci-defaults/99-personalize`。修改后使用
`build.sh` 生成新的候选版本；`reproduce-release.py` 专门验证归档首版，
个性化输入变化后其原始 SHA-256 检查会按预期失败。

OpenWrt 25.12 使用 apk 软件包；不能直接复用旧 Kwrt 的 opkg/IPK 软件源和包。

## 版本与复现边界

`build.lock.json` 锁定官方 ImageBuilder 的 SHA-256 和源码参考提交；
`reference/archives.lock.json` 锁定备份源码的具体内容。
官方软件包服务器仍可能更新包版本，实际构建的软件包版本以输出 `.manifest` 为准。
如需复现同一次构建，应同时保存构建所用的 ImageBuilder、软件包缓存及构建输出。
本仓库的 Release 会保存首版使用的构建输入和候选镜像，源码快照直接保存在仓库。

复现已经发布的首版候选镜像，运行：

```sh
python3 scripts/reproduce-release.py
```

脚本验证 Release 附件的 SHA-256，在安装镜像软件包时使用归档缓存并禁止网络，
然后检查输出镜像 SHA-256 是否与首版相同。普通 `build.sh` 可从官方源获取更新后的包；
这两种用途应区分。

首版镜像为 9,574,687 字节（约 9.13 MiB），含 161 个基础包及依赖。
SHA-256：`1b24d3bfcc0379e90cfa52151d5b920e6e2b222556bbf6286383720b1786677b`。
它仍是未完成实机迁移验证的候选版本，不应仅凭构建成功而刷写。

MIT 许可证仅适用于本工程原创脚本和文档；上游源码和固件组件遵循各自许可证。

## 参考

- https://openwrt.org/toh/cudy/tr3000
- https://openwrt.org/docs/guide-user/additional-software/imagebuilder
- https://github.com/openwrt/openwrt/blob/openwrt-25.12/target/linux/mediatek/dts/mt7981b-cudy-tr3000-256mb-v1.dts
