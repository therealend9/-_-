# B Module

## 目标

`b_module` 负责把页面级 OCR 结果整理成题目级结构化结果，供后续 AI 批改直接消费。

当前主链路覆盖：

1. 路线判断
2. 自由版式分题
3. 跨页答案合并
4. OCR 复核记录
5. 题目级结果导出

## 目录结构

```text
b_module/
  layout_router/
  question_segmenter/
  cross_page_merger/
  ocr_review/
  result_exporter/
  schemas/
  tests/
```

## 当前约定

- 模块间数据交互统一使用 JSON 兼容字典结构。
- 坐标框统一使用 `[x_min, y_min, x_max, y_max]`。
- `question_no` 一律使用字符串。
- 置信度字段统一使用 `0 ~ 1` 小数。
- 运行时 schema 统一通过 `b_module.schemas.types` 入口消费。

## 当前实现状态

已落地：

- `layout_router.service.decide_layout_route`
- `question_segmenter.free_layout_pipeline.split_free_layout_questions_v2`
- `question_segmenter.free_layout_pipeline_v3.split_free_layout_questions_v3`
- `cross_page_merger.service.merge_cross_page_answers`
- `ocr_review.service.submit_ocr_review`
- `result_exporter.service.export_question_level_results`

待继续增强：

- 统一格式试卷模板路线
- 基于几何特征的更稳健分题
- 更完整的跨页连续性判断
- 真实样本联调与回归测试
