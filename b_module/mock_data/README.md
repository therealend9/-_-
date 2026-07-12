# Mock Data

当前目录用于放置 B 模块联调前的模拟输入输出数据。

当前提供：
- `free_layout_case_basic.json`
  单页双题的基础样例
- `free_layout_case_cross_page.json`
  跨页同题合并样例
- `free_layout_case_ocr_heading_error.json`
  OCR 题号识别错误样例
- `free_layout_case_cross_page_boundary_negative.json`
  跨页边界负样例，不应误并
- `free_layout_case_multi_page_complex_a.json`
  三页复杂样例，包含正常切题、跨页续写、跳号风险
- `free_layout_case_multi_page_complex_b.json`
  三页复杂噪声样例，包含重复题号、低置信度题头、OCR 题号错误

建议在 A 模块真实 OCR 输出稳定前，优先用这些样例验证 B 模块自由格式主链路。
