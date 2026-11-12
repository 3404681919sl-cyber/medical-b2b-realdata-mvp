# 可用数据源筛选与采用决策

更新日期：2026-11-12。

## 筛选原则

候选数据必须同时说明来源、字段用途、下载门槛和再分发边界。能下载不等于能放入公开 GitHub；竞赛报名或平台登录也不等于获得公开再分发许可。

## 候选对比

| 数据源 | 可支持的业务问题 | 规模/字段 | 访问与许可判断 | 当前决策 |
|---|---|---|---|---|
| [Mendeley：Retail sales dataset of a pharmacy in Indonesia](https://data.mendeley.com/datasets/2ym7v78wtd/1) | 药店销量分析、需求回测、采购规则演示 | 当前项目已验证 399,738 条交易；商品、数量、成本、售价、日期 | CC BY 4.0；当前项目已记录 DOI、归档哈希和限制 | **继续作为药采智析主数据** |
| [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) | CRM、RFM、客户分层、复购/流失代理指标、取消订单分析 | 541,909 条交易；InvoiceNo、StockCode、Quantity、InvoiceDate、UnitPrice、CustomerID、Country；部分客户为批发商 | CC BY 4.0；页面提供 DOI 与 22.6 MB 文件 | **推荐作为独立 CRM-AI 伴生项目**，不混入药品口径 |
| [天池 O2O 优惠券使用预测](https://tianchi.aliyun.com/competition/entrance/231593/introduction) | 优惠券核销意图、营销触达、用户—商家特征 | 用户、商家、优惠券、折扣、距离、领券与消费日期等竞赛数据 | 需登录/报名下载；公开页面未确认该竞赛数据可被重新发布 | **仅在本人接受条款后本地研究**，原始数据不提交 GitHub |
| [天池移动推荐长期赛](https://tianchi.aliyun.com/competition/entrance/532043/information) | 浏览/收藏/加购/购买意图识别、推荐 | 脱敏 user_id、item_id、behavior_type、category、geohash、小时级时间 | 需登录下载；属于竞赛数据，需逐条核对参赛协议 | **候选**，适合行为意图项目，不作为当前公开数据包 |
| [天池天猫复购预测](https://tianchi.aliyun.com/competition/entrance/532417/information) | 用户—商家复购、线索分层、客户画像 | 用户画像、点击/加购/购买/收藏日志、训练标签 | 需登录/报名；未确认公开再分发许可 | **候选**，适合目标 JD 的 CRM 算法案例，先不下载/发布 |
| [Kaggle Store Sales](https://www.kaggle.com/competitions/store-sales-time-series-forecasting/data) | 门店×品类销量、促销与节假日预测 | 门店、品类、日期、促销、销量及外部信息 | 需登录并接受竞赛规则；不能把竞赛数据直接打包公开 | **仅作本地模型基准**，不优先于 UCI |

天池的[数据集许可指南](https://tianchi.aliyun.com/specials/promotion/license)明确提醒需要检查具体数据集的许可、所有权和覆盖范围；平台列出通用许可类型，不代表每个竞赛数据自动采用开放许可。

## 采用路线

1. 当前药采智析保持单一药店数据口径，不把电商客户行为硬拼成药品字段。
2. 下一独立作品建议采用 UCI Online Retail，构建“CRM 销售分析 Agent”：RFM 客群、取消订单、复购概率、客户流失风险和工具调用评测。
3. 天池数据只有在账号完成报名、本人阅读并接受具体条款后再下载；原文件放在 Git 忽略目录，公开仓库仅保留处理代码、字段说明和不可逆汇总结果（仍需以条款允许为前提）。
4. 如果后续获得中国药店真实脱敏数据，应另建数据版本并重新生成来源、哈希、质量报告和模型评估，不能用它覆盖当前公开数据的证据链。

## 尚未找到的理想数据

本轮没有找到同时满足“中国医药零售交易、含库存/效期/在途/促销、明确开放许可、允许公开再分发”的天池数据。医疗类天池资源主要集中在临床、医学 NLP、知识图谱和影像，不适合冒充药店采购数据。
