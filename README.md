<p align="center">
  <img src=".github/assets/readme-banner.svg" alt="Cudy Personal OpenWrt — 面向多款 Cudy 路由器的个性化固件" width="100%">
</p>

<p align="center">
  面向多款 Cudy 路由器的轻量定制系统。<br>
  源码参考与构建输入留档，插件按需添加。
</p>

<p align="center">
  <a href="https://downloads.openwrt.org/releases/25.12.5/"><img src="https://img.shields.io/badge/OpenWrt-25.12.5-0ea5e9?style=flat-square" alt="基于 OpenWrt 25.12.5"></a>
  <a href="#设备与固件"><img src="https://img.shields.io/badge/Cudy-3%20devices-14b8a6?style=flat-square" alt="3 款 Cudy 设备"></a>
  <a href="https://github.com/Renwang-Huang/cudy-personal-openwrt/releases"><img src="https://img.shields.io/badge/Status-Candidate-f59e0b?style=flat-square" alt="候选版本"></a>
</p>

<p align="center">
  <a href="#设备与固件">选择设备</a> ·
  <a href="#验证进度">验证进度</a> ·
  <a href="#构建与定制">构建与定制</a> ·
  <a href="reference/README.md">源码备份</a>
</p>

> [!IMPORTANT]
> 当前固件均为个人定制候选版，尚未完成实机启动与迁移验证。
> 下载前请核对完整型号和硬件版本，并阅读对应设备的迁移说明。

## 设备与固件

<a name="tr3000-256mb-使用说明"></a>

| 设备 | 构建基础 | 入口 |
| :--- | :--- | :---: |
| **TR1200 v1**<br>AC1200 | 官方 ImageBuilder + 两项设备修正<br>`ramips/mt76x8` | [说明](devices/tr1200/README.md)<br>[v0.1.1](https://github.com/Renwang-Huang/cudy-personal-openwrt/releases/tag/tr1200-v0.1.1-candidate) |
| **TR3000 256MB v1**<br>AX3000 | 官方 ImageBuilder<br>`mediatek/filogic` | [说明](devices/tr3000/README.md)<br>[v0.1.1](https://github.com/Renwang-Huang/cudy-personal-openwrt/releases/tag/v0.1.1-candidate) |
| **TR3600 v1**<br>BE3600 | 官方源码 + 实验适配补丁<br>`mediatek/filogic` | [说明](devices/tr3600/README.md)<br>[v0.1.0](https://github.com/Renwang-Huang/cudy-personal-openwrt/releases/tag/tr3600-v0.1.0-candidate) |

每个型号都有独立的镜像、配置和构建流程。TR3600 的设备支持补丁尚未合入上游；
各型号的镜像不能混刷。精确版本、软件包清单与 SHA-256 见各自 Release。

## 默认体验

- **中文管理** — 中文 LuCI、HTTPS 管理界面、基础路由与防火墙。
- **轻量起步** — 先保留基础联网组件，代理、VPN、存储共享等插件后续按需添加。
- **配置自主** — 默认管理地址 `10.0.0.1/24`，主机名为对应的 `TRxxxx-Personal`；首次启动自行设置密码与无线。
- **输入留档** — 固定源码参考与构建输入，归档工具及缓存，不嵌入密码、私钥或订阅。

## 验证进度

| 设备 | 已完成的验证 | 云端记录 |
| :--- | :--- | :---: |
| **TR1200** | v0.1.1 云端离线重建逐字节一致，MIPS 用户态与异常检查通过 | [重建](https://github.com/Renwang-Huang/cudy-personal-openwrt/actions/runs/41443725093) |
| **TR3000** | 本地离线重建与云端镜像逐字节一致 | [重建](https://github.com/Renwang-Huang/cudy-personal-openwrt/actions/runs/41333664663) |
| **TR3600** | 本地两次源码构建一致；云端发布镜像静态检查通过 | [检查](https://github.com/Renwang-Huang/cudy-personal-openwrt/actions/runs/41394843131) |

TR1200 / TR3000 的云端验证使用官方 ImageBuilder 与归档 APK 重建镜像。
TR3600 尚未完成独立主机的源码重建。上述结果不代表无线、网口、USB 或恢复流程已通过实机验证。

## 构建与定制

在 Linux x86_64 主机上，以普通用户运行。先克隆仓库，再按设备文档准备构建依赖：

```sh
git clone https://github.com/Renwang-Huang/cudy-personal-openwrt.git
cd cudy-personal-openwrt
```

<details>
<summary><strong>TR1200</strong> · 精确复现已发布候选镜像</summary>

```sh
python3 devices/tr1200/scripts/reproduce-release.py
```

校验归档 ImageBuilder 与软件包缓存，禁用 APK 联网，重建后比较首版 SHA-256。
修改软件包或默认配置时，使用[设备文档中的常规构建流程](devices/tr1200/README.md#构建与复现)。

</details>

<details>
<summary><strong>TR3000</strong> · 精确复现已发布候选镜像</summary>

```sh
python3 scripts/reproduce-release.py
```

校验归档输入，禁用 APK 联网，重建后比较首版 SHA-256。
配置与脚本位于仓库根目录，详见 [TR3000 构建说明](devices/tr3000/README.md#构建输入)。

</details>

<details>
<summary><strong>TR3600</strong> · 使用固定源码与工具链构建</summary>

```sh
python3 devices/tr3600/scripts/prepare.py
python3 devices/tr3600/scripts/restore-downloads.py
JOBS=6 bash devices/tr3600/scripts/build.sh
python3 devices/tr3600/scripts/verify-image.py
```

完整主机依赖、补丁来源与双槽行为见 [TR3600 设备说明](devices/tr3600/README.md)。

</details>

所有构建命令均从仓库根目录执行。添加插件、修改默认网络或界面语言，请使用对应设备的
配置和叠加文件；精确复现脚本用于核对归档版本，修改配置后应走常规构建流程。

<details>
<summary>项目目录与资料位置</summary>

```text
config.json / files/ / scripts/   TR3000 配置与构建脚本
devices/
├── tr1200/                      TR1200 配方、脚本与证据
├── tr3000/                      TR3000 使用说明
└── tr3600/                      TR3600 源码配方、补丁与证据
reference/                       上游源码、厂商资料与来源校验
evidence/                        TR3000 验证记录与仓库变更证据
```

临时构建目录、下载缓存和私人备份不进入 Git。Release 保存候选镜像与归档构建输入，
源码参考的备份范围与复现边界见[参考资料说明](reference/README.md)。

</details>

## 上游与许可

本项目基于 [OpenWrt](https://github.com/openwrt/openwrt)，结合 [Cudy 官方资料](https://www.cudy.com/)
与设备社区的适配工作。具体来源和固定提交记录在各设备的锁文件与参考目录中。

原创脚本和文档遵循 [MIT License](LICENSE)；固件组件、上游源码与厂商资料遵循各自许可证。
