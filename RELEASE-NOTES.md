# v0.1.1-candidate

首个基于官方 OpenWrt 25.12.5 的 Cudy TR3000 256MB 最小个性化镜像。

- 设备 profile：`cudy_tr3000-256mb-v1`，平台：`mediatek/filogic`。
- 官方内核、驱动与设备分区定义；中文 LuCI、HTTPS 管理界面。
- 默认地址 `10.0.0.1/24`，主机名 `TR3000-Personal`。
- 不预装 Passwall 或 iStore，不嵌入管理密码、Wi-Fi 密码、订阅或私人配置。
- 完整软件包版本见 `.manifest`，软件物料清单见 `.bom.cdx.json`。

镜像为 9,574,687 字节。
本版统一构建 umask、个性化目录权限和语言环境，修复 v0.1.0 本机与 GitHub
环境之间因目录权限造成的根文件系统内容差异。内核及所用软件包保持一致。

## 验证范围

已检查固件元数据、内核设备树、UBI 起点与长度、个性化文件、中文及 HTTPS 软件包，
并确认未嵌入 root 密码。重复构建和使用归档 APK 缓存的离线重建生成的镜像逐字节一致。
已通过[独立 GitHub Actions 环境复现](https://github.com/Renwang-Huang/cudy-personal-openwrt/actions/runs/41333664663)，
云端产物下载后与本机镜像逐字节比较一致。
未刷入路由器，未验证实机运行、Wi-Fi、WAN 或从现有 Kwrt 的迁移。

## 刷写前尚待解决

现有 Kwrt 板型为 `cudy,tr3000-v2-mod`，候选固件板型为
`cudy,tr3000-256mb-v1`。现有 UBI 长度 226.5 MiB，官方为 230 MiB。
候选固件未加入旧 Kwrt 标识来绕过设备检查。这是供评审的预发布候选，
不是已经验证可直接强制刷写的固件。

## 备份与复现

- 仓库 `reference/` 保存固定提交的完整源码仓库快照及来源记录。
- 本版附件保存候选镜像和校验报告；相同的官方原始 ImageBuilder 与 APK 缓存
  保存在 v0.1.0-candidate Release，由本版锁定文件按固定来源引用并自动检查完整性。
- 下载仓库后运行 `python3 scripts/reproduce-release.py`，可校验输入、使用缓存重建，
  并比对镜像内容。脚本没有刷写动作。
- 源码备份包含主工程与包配方、补丁；每个软件包的上游原始源码另由其配方按固定版本下载并校验。
- 各上游源码与固件组件保留原有许可证；本仓库 MIT 许可证仅覆盖原创脚本和文档。
