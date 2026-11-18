# 来源变化

解除通知在完整范围图发布后到达；同时，地图修订版只有一页；旧交易日的影响判断和当前状态不同。

event-pending.json 表示来源目录已发现资料但正文尚未取得，event-complete.json 表示补取的原文字节已进入接收链。来源字段与既有资料的关系需根据业务事实核对。

县级演练中，district-pending.json 的修订公告改指两页组成的 r2 范围图但第二页未齐，district-complete.json 补齐第二页，district-moved.json 以转址后的新地址提供同一页原文，district-release-pending.json 只把解除通知列入目录，district-release.json 取得解除通知正文。审核清单随每次接续刷新：缺页时未见乡镇待核，旧放行建议撤回；解除按 released_on 当日起适用于同公告的子范围。
