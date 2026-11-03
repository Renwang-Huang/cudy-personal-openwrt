# TR1200 · 系统状态灯

当前使用 [白色正常、红色异常](health/README.md) 的状态灯方案：系统运行正常时白灯常亮，
连续检测异常时白灯熄灭、红灯常亮；恢复正常后自动转白。

检测覆盖上游路由、DNS、管理服务、启用中的 PassWall、HTTPS 访问及基础资源余量。
开机有 5 分钟宽限，连续多轮失败才转红，避免启动等待和短暂抖动造成误报。
服务只观察并控制灯色，不重启设备或修改网络。

| 内容 | 入口 |
| --- | --- |
| 当前行为、检测范围与调整 | [健康灯说明](health/README.md) |
| 安装及回退脚本 | [apply.sh](health/apply.sh) · [rollback.sh](health/rollback.sh) |
| 镜像叠加配置及源脚本 | [files/](health/files/) |
| 当前实机检查 | [健康灯验证](health/validation.json) |

旧的星舰巡航灯语源文件 `apply.sh`、`starship-calm.uci` 及 `validation.json` 保留作历史参考，
当前设备已替换，不再使用白灯定时闪烁和红灯流量闪烁。旧验证报告中的“无新增后台进程”仅描述旧方案。
