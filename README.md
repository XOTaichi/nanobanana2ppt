# nanobanana2ppt

项目目标：把 nanobanana 生成的科研绘图、技术路线图、流程图页面，转换成“可继续人工编辑”的 PPT。

## 适用场景

主要支持两类场景：

1. 只修改文字
适合国家课题申报图、技术路线图、流程图这类 container 很多、图标位置要求没那么高，但中文文字必须能改的场景。

2. 同时修改文字和图标
适合科研绘图、方法图、系统结构图。文字会尽量转成可编辑文本框，icon、箭头、图块会尽量拆成独立图片，便于后续手动拖动和替换。

## 依赖准备

```bash
git clone https://github.com/XOTaichi/nanobanana2ppt.git
cd nanobanana
```

在 `nanobanana2ppt/` 目录下执行：

```bash
cp .env.example .env
```

填入对应的 API Key：

- `ROBOFLOW_API_KEY`
  用于 SAM3 检测视觉元素
- `BAIDU_API_KEY`
  用于百度 OCR 检测文字
- `IMAGE_API_KEY`
- `IMAGE_API_BASE`
- `IMAGE_MODEL`
  以上三项用于背景修复

API 获取位置：

- Roboflow: `https://app.roboflow.com/`
- Baidu API Key: `https://console.bce.baidu.com/iam/#/iam/apikey/list`

安装依赖：

```bash
pip install -r requirements.txt
```

如果你希望本地跑 BRIA RMBG 去背景，把模型下载到：

```bash
model/
```

模型地址：

```text
https://huggingface.co/briaai/RMBG-2.0/
```

备注：

- 某些网络环境下 OCR / Roboflow / 图像模型接口会失败，实测建议先不要开梯子
- `.gitignore` 已忽略 `model/`、Python 缓存、虚拟环境和 `.env`

## 目录里的主要入口

- `run_text_only_pipeline_cli.py`
  只处理文字
- `run_pipeline_cli.py`
  完整流程：提取元素，可选背景修复，导出 PPT
- `extract_elements_cli.py`
  只做元素提取
- `restore_background_cli.py`
  只做背景修复
- `export_ppt_cli.py`
  从已有 manifest 导出 PPT

## 使用方法 1：仅修改文字

适用场景：

- 国家课题申报图
- 技术路线图
- 中文较多、对 OCR 准确率要求高
- icon 精度要求不高

基本思路：

- 用百度 OCR 检测文字位置
- 在 PPT 里用白色区域盖掉原文字
- 重新叠加可编辑文本框
- 不依赖 SAM3，不处理视觉元素

命令：

```bash
python run_text_only_pipeline_cli.py demo/技术路线4.png \
  --output-dir demo/技术路线4_0332/技术路线4 \
  --font-name Arial \
  --font-size 14
```

常用参数：

- `--output-dir`
  输出目录
- `--font-name`
  文本框默认字体
- `--font-size`
  文本框默认字号
- `--ocr-api-key`
  手动指定百度 OCR key，不走 `.env`

输出结果：

- `text_only_editable.pptx`
- `text_manifest.json`
- `crops/`

## 使用方法 2：同时修改文字与图标

适用场景：

- 科研绘图
- 方法图
- 结构图
- 希望文字和 icon 都能拆出来单独处理

基本思路：

1. 用 SAM3 提取视觉元素
2. 用百度 OCR 提取文字元素
3. 生成 `manifest.json`、mask、overlay、crop
4. 可选做背景修复
5. 导出 PPT

直接跑完整流程：

```bash
python run_pipeline_cli.py demo/demo_banana.png \
  --output-dir demo/demo_banana \
  --remove-bg \
  --restore-background
```

常用参数：

- `--output-dir`
  输出目录
- `--sam-prompts`
  指定 SAM3 提示词，例如 `icon,arrow,diagram,chart`
- `--sam-threshold`
  SAM3 过滤阈值
- `--remove-bg`
  在元素提取阶段就先给 visual crop 去背景
- `--restore-background`
  执行背景修复
- `--background white|restored`
  导出时使用白底或修复后的背景

输出目录里通常包含：

- `manifest.json`
- `overlay.png`
- `mask.png`
- `masked_preview.png`
- `restored_background.png`
- `crops/`
- `prepared_visuals/`
- `overlay_editable.pptx`

## 使用方法 3：同时修改文字与图标，但背景自己处理

有些科研图背景比较简单，或者你不信任当前背景修复效果，这时可以直接导出白底 PPT，再自己在 PPT 里或外部手工处理背景。

命令：

```bash
python run_pipeline_cli.py demo/demo_banana.png \
  --output-dir demo/demo_banana \
  --background white
```

如果你已经自己准备好了背景图，也可以把背景图放到输出目录里，然后单独导出：

```bash
python export_ppt_cli.py demo/demo_banana/demo_banana/manifest.json \
  --output demo/demo_banana/demo_banana/new.pptx \
  --disable-rmbg
```

说明：

- `--disable-rmbg` 表示导出阶段不重新跑一次 RMBG
- 当前导出逻辑会优先复用：
  1. `prepared_visuals/*_tight.png`
  2. `prepared_visuals/rmbg_raw/*_nobg.png`
  3. manifest 中已有的 `nobg_path`
  4. 原始 `crop_path`

所以如果你前面已经生成了 `prepared_visuals/`，导出阶段会优先吃已有结果。

## 分步命令

### 1. 只提取元素

```bash
python extract_elements_cli.py demo/demo_banana.png \
  --output-dir demo/demo_banana \
  --remove-bg
```

### 2. 只修复背景

```bash
python restore_background_cli.py demo/demo_banana/demo_banana
```

### 3. 只导出 PPT

```bash
python export_ppt_cli.py demo/demo_banana/demo_banana/manifest.json \
  --output demo/demo_banana/demo_banana/edit.pptx \
  --disable-rmbg
```

## 注意事项

- 输出 PPT 更接近“半可编辑 PPT”，不是完全结构化还原
- 文本通常可以编辑
- icon、箭头、图形通常仍然是图片对象
- OCR 和 SAM3 的结果会影响最终可编辑程度
- 背景修复仍然有不稳定性，复杂背景建议人工介入

## 致谢

- `https://github.com/ResearAI/AutoFigure-Edit/tree/main#`
- `https://github.com/Anionex/banana-slides#`
