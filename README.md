# epubTranslatorWithLLM

这是一个使用OpenAI的LLM（大语言模型）进行epub电子书内容总结和翻译，并重新构建epub电子书的项目。项目主要功能包括提取epub电子书的内容，使用LLM对文本内容进行总结和翻译，最后将翻译后的内容重新构建成新的epub电子书。

## 项目功能

### 1. 提取epub内容
- 从指定的epub文件中提取各种类型的内容，包括文本、其他文档格式以及其他项目。

### 2. 内容总结和翻译
- 使用OpenAI的LLM对提取的文本内容进行总结，按照特定的格式输出人物、时间、地点、主要动作、提出的概念以及其他重要细节。
- 将提取的文本内容从源语言翻译为目标语言，同时遵循特定的翻译要求，如语义忠实、格式一致等。

### 3. 重新构建epub电子书
- 根据翻译后的内容，重新构建一个新的epub电子书，包含翻译后的文本内容、设置好的样式和目录结构。

## 环境配置

### 1. 安装依赖
确保你已经安装了以下Python库：
```bash
pip install ebooklib bs4 openai jinja2
```

### 2. 设置API密钥
在运行项目之前，你需要设置OpenAI的API密钥。本项目使用了阿里云和DeepSeek的兼容API，你需要将对应的API密钥设置为环境变量：
```bash
export ALIYUN_API_KEY=your_aliyun_api_key
export DEEPSEEK_API_KEY=your_deepseek_api_key
```

## 项目结构
```
epubTranslatorWithLLM/
├── epubTemplates/
│   ├── 00.html
│   └── Style.css
├── testBook/
│   └── yourbook.epub
├── main.py
└── README.md
```

### 主要文件说明
- `main.py`：主程序文件，包含主要的函数和程序入口。
- `epubTemplates/`：存放epub电子书构建所需的模板文件和样式文件。
- `testBook/`：存放待处理的epub电子书文件。

## 使用方法

### 1. 准备工作
将需要处理的epub电子书文件放入 `testBook/` 目录下。

修改main.py文件中的以下变量：
```python
# 待处理的epub文件名
book = epub.read_epub('testBook/yourbook.epub')
model = "your preferred model"
sourceLang = ""
targetLang = ""
```

### 2. 运行项目
在项目根目录下，运行以下命令：
```bash
python main.py
```

### 3. 查看结果
处理完成后，翻译后的epub电子书将保存在 `epubOutput/` 目录下，文件名为 `output.epub`。

## 注意事项
- 项目运行过程中会生成一个 `progress.json` 文件，用于记录处理进度，方便程序中断后继续处理。处理完成后，可以使用 `cleanUp()` 函数删除该文件。
- 项目中使用的LLM模型为 `qwen-max`，如果需要更换模型，请修改 `model` 变量的值。
- 默认使用并行模式处理，如果需要更改为串行模式，请修改 `parallel` 变量的值。
- 并行模式下不会保存进度，请保证网络稳定
- 一本书也就不到50w token吧 不贵

## 许可证
本项目使用 [MIT许可证](https://opensource.org/licenses/MIT)，你可以自由使用、修改和分发本项目。