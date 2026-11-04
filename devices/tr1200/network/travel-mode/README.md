# TR1200 · 酒店网络准备

基于 OpenWrt 原生网络、dnsmasq、firewall4 和固定版 Travelmate 2.4.9-r6，
为“酒店 Wi-Fi 为主，有网线时也使用”的场景做运行配置增强。
保留 [2.4 GHz 直连、5 GHz 经 PassWall 分流](../band-policy/README.md)，不重新刷写固件。

## 已部署内容

| 项目 | 配置与目的 |
| --- | --- |
| 上游 Wi-Fi 管理 | Travelmate 管理已保存的 radio0 / 2.4 GHz 上游，提供扫描、添加站点、连接状态及认证入口识别 |
| 酒店 DNS | 2.4 GHz 的独立 dnsmasq 跟随 DHCP 解析器；PassWall 的直连 DNS 使用自动模式，适应不同酒店 |
| 认证探测 | HTTP 探测直达上游，避免代理尚未联网时遮蔽酒店认证入口；当前使用实测可达的 204 探测地址 |
| 测速与切换 | 既有自动测速组合间隔从 10 秒改为 3 分钟，容差设为 150 ms，降低小设备的测速开销和频繁切换 |
| 网线接入 | WAN metric 10，无线中继 metric 20；两者均在线时优先有线 |
| 上游变化同步 | 沿用 PassWall 原有 ifup 处理，补充 DHCP DNS 变化及 WAN 断开后的代理配置重建，复用同一事件锁 |
| TCP 大包问题 | 启用 `tcp_mtu_probing=1`，配合原有 WAN MSS 调整，应对部分路径 MTU 黑洞；不固定降低所有连接的 MTU |

Travelmate 不主动加入未知开放 Wi-Fi，不随机轮换 MAC，不因单次互联网探测失败而断开上游，
也不周期性重启路由器。酒店认证通常与设备 MAC 绑定，已完成的认证应尽量保留。
有线优先依赖链路和 DHCP 可用；不等同于跨两路上游的互联网健康选路。

新增防火墙规则只匹配**路由器本机发出的 TCP 80 请求**，这些 HTTP 请求直接访问上游，
不改动客户端的双频分流。实测路由器本机 HTTP 为直连出口，5 GHz 客户端 HTTP 仍使用代理出口。
HTTPS 认证页仍执行正常证书校验，不能通过关闭证书检查解决认证问题。

## 到酒店后怎么用

1. 手机连接 `Cudy-TR1200-5G`，进入 `https://192.168.20.1`。
   在 **服务 → Travelmate → 无线站点**，使用 **在 radio0 上扫描**，添加酒店 2.4 GHz Wi-Fi，填写密码并应用。
   当前网络接口和防火墙已设置完成，无须重新运行“接口向导”。
2. 需要房号、短信或勾选条款时，手机切到 `Cudy-TR1200-2.4G`，再打开普通 HTTP 网页，
   例如 `http://neverssl.com`，按酒店页面完成认证。2.4 GHz 后台入口为 `192.168.24.1`。
   使用自定义加密 DNS 的浏览器可能无法打开酒店内部认证域名，可在认证期间改用系统 DNS。
3. 认证后回到 5 GHz 使用原 PassWall 规则；Travelmate 概览应显示 `connected, net ok`，
   然后在 PassWall 检查实际代理站点。只有酒店放行上游后，代理节点才可能正常连接。
4. 有酒店网线时，接入路由器 **WAN 口**。有线 DHCP 成功后优先使用网线；拔线后系统使用仍在线的无线中继。

已部署的上游管理限定 2.4 GHz，以保留独立的 5 GHz 下游。只有 5 GHz Wi-Fi 的酒店需要另外调整射频分配，
当前没有把扫描到的 radio1 网络自动纳入管理。WPA Enterprise、短信认证、设备数限制、酒店特定认证脚本
均需按现场网络处理，没有预设通用自动登录。

## 来源与应用

- [Travelmate 固定源码及本地包](../../../../reference/travelmate/README.md)
- [OpenWrt DHCP / DNS](https://openwrt.org/docs/guide-user/base-system/dhcp)
- [OpenWrt firewall4 nftables 片段](https://openwrt.org/docs/guide-user/firewall/firewall_configuration)
- [Linux TCP 路径 MTU 探测](https://www.kernel.org/doc/html/latest/networking/ip-sysctl.html)

`apply-base.sh` 先检查既有双频配置并备份，再应用基础设置。
`enable-travelmate.sh` 在固定版本本地包已安装后，导入现有上游、安装适配文件并启用服务。
脚本是本仓库现场系统的部署配方，不是通用 OpenWrt 一键安装器，也不会下载滚动版本或开启软件源。

Travelmate 的适配仅包括：为两个 DNS 实例添加实际识别出的认证域名例外、补充有限的上游变化事件、
路由器本机 HTTP 的直连标记。没有修改代理协议实现或自动提交酒店登录凭据。
检测出的认证域名按 Travelmate 原有机制写入白名单；不全局关闭 DNS 重绑定保护。

固定本地包共五个，没有升级原有包。设备现有密钥及获取的上游密钥环未通过这批包的签名验证；
本次仅对这批官方 HTTPS 下载的本地包放行，并核对传输内容及关键后端文件与固定源码完全一致。
设备持久密钥、软件源和未来包安装策略保持原样；这一核对不替代有效的发行签名。

## 恢复与验证

修改前的私人配置和恢复脚本位于 `/root/network-backups/travel-quality-before/`，
包含节点、无线密码等敏感数据，不进入仓库。需要回到本次增强前状态时运行：

```sh
sh /root/network-backups/travel-quality-before/rollback.sh
```

恢复会停用 Travelmate，恢复原有网络和代理配置，移除本次事件钩子、HTTP 标记及 TCP 探测设置。
五个新增工具包保留安装但不启用。恢复脚本未在实机执行，原始文件及备份内容已核对。

本地事件分支验证不连接路由器：

```sh
python3 devices/tr1200/network/travel-mode/validate-uplink-events.py
```

实机结果及未验证范围见 [VALIDATION.md](VALIDATION.md)。
