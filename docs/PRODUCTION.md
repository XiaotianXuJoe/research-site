# 生产环境边界

- 项目：个股深度研究站
- 端口：3002
- 目录：/var/www/research；监控 /home/ubuntu/monitor/monitor.py
- 进程：nginx + cron

## 推荐检查

`python3 build.py（先在测试目录验证输出）`

## 不上传、不覆盖

alerts.json、monitor/state.json 和监控日志。这些内容只应通过独立的生产备份机制保存，不属于 Git 源码。

本仓库公开可见。任何真实凭据都不应写入代码、Issue、Actions 日志或 Git 历史。
