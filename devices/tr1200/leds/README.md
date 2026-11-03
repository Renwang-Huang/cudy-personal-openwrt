# TR1200 · 星舰巡航灯语

利用 OpenWrt 自带的 LED 配置和内核 `timer` / `netdev` 触发器，
让红白两路状态灯显示舒缓的运行节奏与 LAN 数据活动。
没有新增软件包、常驻脚本、定时任务或后台服务。

| 灯 | 最终效果 | 含义 |
| --- | --- | --- |
| 白色 | 每 5 秒亮约 0.35 秒，随后熄灭约 4.65 秒 | 舒缓的巡航节奏 |
| 红色 | LAN 收发数据时闪动，触发间隔为 400 ms；空闲时熄灭 | 数据活动提示 |

灯只支持开关，无法实现 RGB 变色或连续调光。红灯重新用于流量提示，
白灯按固定节奏运行；这套灯语不检测互联网连通性或代理节点状态。
启动、恢复和早期故障阶段仍由设备原有流程控制，正常系统启动后由 `S96led` 应用本预设。

## 已完成的实机检查

- 在一台 Cudy TR1200 v1、OpenWrt 25.12.5 上配置并读取内核控制参数核对。
- 观察灯亮度状态采样，确认白灯周期亮灭、红灯响应真实 LAN HTTP 流量。
- 标准 LED 服务重载后仍使用相同触发器与时序，服务已设为开机启用。
- 系统配置只增加本预设的两项 LED 配置，既有系统和网络设置保持原样。
- 安装前状态与系统配置已保存在设备和电脑；未为此执行设备重启。

结构化结果见 [validation.json](validation.json)。

## 查看和调整

在管理页进入 **系统 → LED 配置**，可以调整两路灯的触发器和时序。
配置位于 `/etc/config/system` 的 `cudy_starship_white` 和 `cudy_starship_red`。

例如把白灯改为每 8 秒亮 0.3 秒：

```sh
uci set system.cudy_starship_white.delayon='300'
uci set system.cudy_starship_white.delayoff='7700'
uci commit system
/etc/init.d/led reload
```

## 在匹配的设备首次应用

将 `apply.sh` 和 `starship-calm.uci` 放到路由器上的同一个目录。先检查，再应用：

```sh
sh apply.sh --check
sh apply.sh --apply
```

脚本只适用于这里固定的设备和 LED 名称，不应直接套用到其他 Cudy 型号。
已配置过本预设的设备会拒绝重复安装，避免覆盖原备份；后续通过管理页或 UCI 调整。

当前实机的原配置、亮度和触发器以及专用回退脚本保存在本机部署记录对应的
`/root/led-backups/` 子目录。回退脚本只移除本预设并恢复原 LED 状态，保留后续其他系统设置。
完整配置备份仅存本机，未提交到仓库。

## 参考

- [OpenWrt LED 配置](https://openwrt.org/docs/guide-user/base-system/led_configuration)
- [Linux timer 触发器](https://github.com/torvalds/linux/blob/v6.12/drivers/leds/trigger/ledtrig-timer.c)
- [Linux netdev 触发器](https://github.com/torvalds/linux/blob/v6.12/drivers/leds/trigger/ledtrig-netdev.c)
