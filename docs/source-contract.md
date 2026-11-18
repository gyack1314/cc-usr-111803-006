# 来源字段

health_notice 与 area_map 的 county 是来源声明的关联线索；字段相等不证明两份原文已经完整或同版。

来源目录中的 expected_revision 表示该链接当前要求核实的来源版次；normal.json 为 v1，revised.json 将第一份来源改指同链接 v2。旧版原文仍可用于历史视图。

县级演练来源以 notice_no 关联公告、范围页和解除文书；map_revision 标识一组范围页，page 从 1 开始，pages_expected 是本组总页数，townships 为该页列出的乡镇。单页上的 pages_received 只说明这份响应含有一页。新公告只采用它引用的 map_revision，其他版次不能填入缺页。release_notice 的 townships 是被解除的子范围，released_on 当日起适用，只解除同一 notice_no。trade_batch 的 ship_on 为计划交易日期，heads 为该批数量。演练日期按当地日历日解释。
