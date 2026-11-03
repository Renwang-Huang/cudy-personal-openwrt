# TR1200 · 白色正常、红色异常

本方案使用设备现有的 `white:status` 与 `red:power`，配合 OpenWrt `procd` 管理的轻量观察服务。
灯色固定、不闪烁，不安装新软件包，不重启网络或代理服务。

| 状态 | 白灯 | 红灯 |
| --- | --- | --- |
| 检查正常 | 常亮 | 熄灭 |
| 连续检查异常 | 熄灭 | 常亮 |
| 系统启动、等待初始检查 | 常亮 | 熄灭 |

## 检测范围

每轮检查以下条件，HTTPS 使用两个独立探测站点，任意一个成功即可：

- 网络管理、DNS、网页管理、RPC、SSH 服务均有运行实例。
- 存在 IPv4 默认路由，本地 DNS 能解析 `example.com`。
- 当 PassWall 主开关启用时，核心进程及 TCP/UDP 透明代理规则存在。
- 按当前路由和代理策略进行 HTTPS 请求，完成证书验证并收到成功或重定向响应。
- 可用内存至少 4 MiB，可写系统分区至少剩余 256 KiB。

探测器只显示状态，不自动重启设备、不修复网络、不修改节点。它不是全部硬件故障的检测器；
设备完全死机或断电时，软件无法保证更新灯色。

## 防止误报

- 默认每轮检查后等待 30 秒；请求本身有独立超时。
- 连续 3 轮异常才亮红灯，短暂抖动保留原颜色。
- 连续 2 轮正常恢复白灯。
- 首次启动最多留 300 秒宽限，容纳无线连接和 PassWall 初始化；确认正常后不再重复享受宽限。

通常约一至数分钟确认异常，具体取决于失败点及请求耗时。早期引导、恢复和刷写阶段仍由设备原流程控制。
5 分钟宽限内的白灯表示“正在等待检测”，尚不等于所有外网检查均已通过。

## 查看状态

```sh
# 查看后台观察结果和原因。
/usr/libexec/cudy-health-led --status

# 立即进行一次只读健康检查，不改变灯色。
/usr/libexec/cudy-health-led --check

# 查看服务是否启用及运行。
/etc/init.d/cudy-health-led enabled
/etc/init.d/cudy-health-led status
```

运行状态仅写在 `/var/run/cudy-health-led/status`，颜色变化时写系统日志，不持续写闪存。
设置位于 `/etc/config/cudy-health-led`；调整后只需重启 `cudy-health-led` 服务。
两路 LED 使用 `none` 触发器，观察器每轮维持当前颜色，原有流量闪烁灯语已替换。

## 安装与回退

将本目录整体复制到匹配的 TR1200，先检查，再应用：

```sh
sh apply.sh --check
sh apply.sh --apply
```

安装器先备份并执行实际健康检查，再替换旧的两项灯语配置。若已安装或已有备份会拒绝覆盖。
现有网络、Wi-Fi、DNS、防火墙、PassWall 和界面配置不会被安装器修改。

设备上的旧配置和回退脚本保存在 `/root/led-backups/health-before/`。
需要恢复此前灯语时：

```sh
sh /root/led-backups/health-before/rollback.sh
```

回退仅移除本健康灯服务并恢复被替换的 LED 配置段，保留其他系统设置。
配置、服务、观察脚本和私有回退目录已加入设备的升级备份列表。

## 后续镜像

将 `files/` 叠加进镜像，保留脚本的可执行权限。首次启动脚本注册两路常亮 LED，并启用观察服务。
PassWall 个性化配方已声明这层叠加；历史基础候选镜像没有改写。
首次启动前的引导灯色由引导程序和原系统控制，本方案不修改引导程序。

## 参考与验证

采用 OpenWrt 的 LED 配置、`procd` 进程管理，以及多次失败后才改变状态的常见探测方式：

- [OpenWrt LED 配置](https://openwrt.org/docs/guide-user/base-system/led_configuration)
- [OpenWrt LED 初始化脚本](https://github.com/openwrt/openwrt/blob/openwrt-25.12/package/base-files/files/etc/init.d/led)
- [OpenWrt Watchcat 的 procd 与周期探测结构](https://github.com/openwrt/packages/blob/openwrt-25.12/utils/watchcat/files/watchcat.init)

实机已检查正常白灯、连续模拟探测失败转红、实际网络仍可用、恢复探测后转白、标准 LED 服务重载和配置边界。
具体观察结果见 [validation.json](validation.json)。本次没有为灯语单独重启整台路由器。
