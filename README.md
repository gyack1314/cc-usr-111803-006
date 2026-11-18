# 地方猪病通报与交易批次影响范围采集

现有项目保存地方通报与范围图的冻结来源响应。transport 核对请求和原文字节，domain 提取来源声明的资料身份，ledger 原子保存版本，view 展示已收资料及待核状态。collection 将来源目录、待收范围与接收进度持久保存，archive 保留已发布视图所引用的资料状态；双来源初版资料已可按当前字段核对并判断发布；后续更正、撤回与范围变化尚待接续。合成样例不访问外部站点。来源字段见 docs/source-contract.md。

在项目根目录运行：

    python -m unittest discover -s tests -v
    python -m compileall -q capture_service tests
    python -m capture_service.cli inspect data/normal.json

容器运行：docker build -t pork-collection-006 .；docker run --rm pork-collection-006。

县级演练资料 district-initial.json 可接入同一采集入口；districts.restrictions 按公告引用的整组范围页判定批次归属，页码齐备才算完整，缺页时未见乡镇保持待核而不判范围外；dispatch.refresh 形成独立持久交易审核清单，collect 每次接续后同步刷新，恢复后的建议不领先于已核实依据，旧放行建议随资料变化撤回。解除通知正文核实后按生效日解除同公告的子范围，不追溯、不及其余乡镇；正文未取得的解除文书只在依据中标记为待核。district-pending/complete/moved/release(-pending).json 依次演练公告修订、缺页补齐、同原文转址与解除通知的接续。所有数据均为本地合成资料。
