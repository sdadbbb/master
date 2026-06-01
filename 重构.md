# .doc 文件支持说明

## 功能概述

需求文档上传功能现已支持 `.doc` 格式（Microsoft Word 97-2003 文档）。

**支持的格式：**
- ✅ `.txt` - 纯文本文件
- ✅ `.md` - Markdown 文件
- ✅ `.docx` - Microsoft Word 2007+ 文档
- ✅ `.doc` - Microsoft Word 97-2003 文档（新增）
- ✅ `.json` - JSON 文件
- ✅ `.yaml/.yml` - YAML 文件

## 安装依赖

### Windows 系统（推荐方案）

使用 pywin32 调用 Word COM 接口读取 `.doc` 文件：

```bash
pip install pywin32>=306
```

**注意：** 
- 需要系统中已安装 Microsoft Word
- 仅适用于 Windows 系统

### Linux/macOS 系统或跨平台方案

使用 textract 库（需要额外系统依赖）：

```bash
# 安装系统依赖（Ubuntu/Debian）
sudo apt-get install antiword unrtf poppler-utils pdftotext tesseract-ocr

# 安装 Python 库
pip install textract>=1.6.5
```

**注意：**
- `antiword` 用于读取 `.doc` 文件
- 在 openKylin 上可能需要从源码编译或使用其他工具

## 工作原理

代码会自动尝试以下方案读取 `.doc` 文件：

1. **优先使用 pywin32**（Windows + Word）
   - 通过 Word COM 接口打开文件
   - 提取文本内容
   - 自动关闭 Word 进程

2. **备选使用 textract**（跨平台）
   - 如果 pywin32 不可用，尝试使用 textract
   - 适用于 Linux/macOS 系统

## 常见问题

### Q1: 上传 .doc 文件时报错 "读取 doc 文件失败"

**解决方案：**
- Windows: 安装 `pywin32` 并确保已安装 Microsoft Word
  ```bash
  pip install pywin32
  ```

- Linux/openKylin: 安装 `textract` 和系统依赖
  ```bash
  sudo yum install antiword  # CentOS/openKylin
  pip install textract
  ```

### Q2: Windows 下是否需要安装 textract？

**不需要**。如果有 Microsoft Word，使用 pywin32 即可，效果更好。

### Q3: Linux 下如何读取 .doc 文件？

推荐使用 `textract` + `antiword`：
```bash
# openKylin/CentOS
sudo yum install antiword
pip install textract

# Ubuntu/Debian
sudo apt-get install antiword
pip install textract
```

### Q4: 能否将 .doc 转换为 .docx？

可以，但不是必需的。建议：
- 如果有 Microsoft Word，直接另存为 `.docx` 格式
- 或者使用在线转换工具
- 我们的代码已经支持直接读取 `.doc` 文件

## 技术实现

相关代码位置：
- 文件上传验证：`web_ui/llm.py` (ALLOWED_EXTENSIONS)
- 文档读取逻辑：`page/llmCaseGenerator.py` (read_document 方法)
- 前端配置：`web_ui/templates/llm.html`

## 更新日志

- 2026-05-29: 新增 `.doc` 文件格式支持
- 支持双系统（Windows/Linux）读取 `.doc` 文件
