#!/usr/bin/env bash

# 方案 1：仅修改文字
# 适合国家课题申报图、技术路线图、中文较多的页面。
python run_text_only_pipeline_cli.py demo/技术路线4.png \
  --output-dir demo/技术路线4_0332/技术路线4 \
  --font-name Arial \
  --font-size 14


# 方案 2：同时修改文字与图标，完整流程
# 包含：
# 1. 提取视觉元素和文字
# 2. 背景修复
# 3. 导出 PPT
python run_pipeline_cli.py demo/demo_banana.png \
  --output-dir demo/demo_banana \
  --remove-bg \
  --restore-background


# 方案 3：同时修改文字与图标，但不依赖背景修复，默认白色
# 适合背景简单、准备后续人工处理背景的情况。
python run_pipeline_cli.py demo/demo_banana.png \
  --output-dir demo/demo_banana \
  --background white


# 方案 4：如果元素已经提取好了，只重新导出 PPT（适用于自己更新了restored_background.png的情况）
# 这里不会重新跑 RMBG，而是优先复用 prepared_visuals/ 里的结果。
python export_ppt_cli.py demo/demo_banana/demo_banana/manifest.json \
  --output demo/demo_banana/demo_banana/new.pptx \
  --disable-rmbg


# 方案 5：完全分步执行，便于排查问题

# 5.1 提取元素
python extract_elements_cli.py demo/demo_banana.png \
  --output-dir demo/demo_banana \
  --remove-bg

# 5.2 修复背景
python restore_background_cli.py demo/demo_banana/demo_banana

# 5.3 导出 PPT
python export_ppt_cli.py demo/demo_banana/demo_banana/manifest.json \
  --output demo/demo_banana/demo_banana/edit.pptx \
  --disable-rmbg
