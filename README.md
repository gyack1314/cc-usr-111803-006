# 地方猪病通报与交易批次影响范围采集

现有项目保存地方通报与范围图的冻结来源响应。transport 核对请求和原文字节，domain 提取来源声明的资料身份，ledger 原子保存版本，view 展示已收资料及待核状态。collection 将来源目录、待收范围与接收进度持久保存，archive 保留已发布视图所引用的资料状态；双来源初版资料已可按当前字段核对并判断发布；后续更正、撤回与范围变化尚待接续。合成样例不访问外部站点。来源字段见 docs/source-contract.md。

在项目根目录运行：

    python -m unittest discover -s tests -v
    python -m compileall -q capture_service tests
    python -m capture_service.cli inspect data/normal.json

容器运行：docker build -t pork-collection-006 .；docker run --rm pork-collection-006。

县级演练资料 district-initial.json 可接入同一采集入口；districts.restrictions 展示单图范围下的批次状态，dispatch.refresh 形成独立持久交易审核清单。所有数据均为本地合成资料。
