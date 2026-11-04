# TR1200 · 双频 Wi-Fi 分流

此配方使用 OpenWrt 的独立网络、dnsmasq 多实例和 PassWall 原生访问控制，将两路下游无线分别处理。
不更换固件、不新增软件包，不改变无线中继上游、节点、SSID 或无线密码。

| 下游网络 | 地址与管理入口 | 数据与 DNS 策略 |
| --- | --- | --- |
| 2.4 GHz · `Cudy-TR1200-2.4G` | `192.168.24.0/24`，网关 `192.168.24.1` | 绕过本机 PassWall；独立 DNS 直连解析 |
| 5 GHz · `Cudy-TR1200-5G` | `192.168.20.0/24`，网关 `192.168.20.1` | 使用现有 PassWall 全局节点和分流规则 |
| 原有有线 LAN | 保留 `192.168.20.0/24` | 保留与 5 GHz 相同的策略 |

5 GHz 使用现有分流规则：命中代理的目标经代理连接，国内及局域网等直连目标仍按规则直连。
2.4 GHz 的“直连”指绕过这台 TR1200 的 PassWall；上游网络的策略仍由上游设备决定。
两个下游网络保留同一可信防火墙区域，允许管理及相互访问，不提供访客隔离。

## 实现

- 仅将 `wireless.default_radio0` 下游 AP 移到新建的 `direct24` 网络，桥为 `br-direct24`。
  radio0 上的上游 STA 和 radio1 上的 5 GHz AP 保持原样。
- 为 `direct24` 创建独立 dnsmasq 实例、地址池和租约文件，直连 DNS 为 `223.5.5.5`。
  原有 LAN DHCP 显式关联其实际 UCI 实例名，避免双实例环境中遗漏地址池或跨网段发放地址。
- PassWall 的 `wifi24_direct` 规则匹配 `direct24`，TCP/UDP 全端口绕过，DNS 使用该网络自己的 53 端口。
  `wifi5_proxy` 匹配原 `lan`，复用既有全局代理配置；无须复制或公开节点信息。
- 2.4 GHz 不分配 IPv6 前缀，不提供 RA/DHCPv6。现有 5 GHz/LAN IPv6 配置不变。

参考：[OpenWrt 无线网络配置](https://openwrt.org/docs/guide-user/network/wifi/basic)、
[dnsmasq 多实例](https://openwrt.org/docs/guide-user/base-system/dhcp#multiple_dhcpdns_serverforwarder_instances)、
[PassWall 固定版本源码](https://github.com/Openwrt-Passwall/openwrt-passwall/tree/26.10.29-1)。
实现沿用这些项目提供的功能，没有另建透明代理服务。

## 应用与恢复

适用于本仓库已经部署 PassWall 的 TR1200 v1 现场系统，管理网段为 `192.168.20.0/24`，
两个下游 AP 原本都连接 `lan`。脚本会检查前置条件，并拒绝重复执行或覆盖已有备份。
它是部署后的配置配方，不是历史基础镜像的默认配置。

将本目录的两个脚本一起复制到路由器。在保留 5 GHz 或有线管理连接的条件下，先检查再应用：

```sh
sh apply.sh --check
sh apply.sh --apply
```

配置重载会短暂中断无线和代理服务。2.4 GHz 客户端应断开后重新连接，取得 `192.168.24.x` 地址；
5 GHz 继续使用原管理地址。原有无线及管理密码保持不变。

脚本把修改前的五份配置和恢复脚本保存在设备私有目录
`/root/network-backups/band-policy-before/`。恢复命令：

```sh
sh /root/network-backups/band-policy-before/rollback.sh
```

备份包含无线密码和节点凭据，只能留在私有存储中。应用脚本会把该备份目录加入
`/etc/sysupgrade.conf` 的保留列表；不要上传配置备份或租约文件到公开仓库。

现场验证见 [VALIDATION.md](VALIDATION.md)。测试范围是单台设备当前环境，不代表所有上游和节点都已覆盖。
