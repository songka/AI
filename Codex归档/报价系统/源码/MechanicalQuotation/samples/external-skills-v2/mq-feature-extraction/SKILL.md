---
name: mq-feature-extraction
description: Extract manufacturing features from drawing evidence for downstream planning and pricing. Use for the FEATURE_EXTRACTION step in MechanicalQuotation V2.
---

# 制造特征提取

只执行 `FEATURE_EXTRACTION`。从图纸证据提取外形尺寸、孔、螺纹、槽、型腔、框架、焊缝、折弯、表面处理、公差和粗糙度。

每项特征保留数量、尺寸、单位、来源和置信度；不确定值放入 `unknown_features`，不得用常见值填空。结果写入 `step_results.FEATURE_EXTRACTION`。

返回协议 JSON，复制 `request_id`；固定 `skill_id=sample.feature-extraction`、`skill_version=1.0.0`、`protocol_version=1.0`，不得返回 Markdown。
