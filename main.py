import os

import ebooklib
from ebooklib import epub
import bs4
from openai import OpenAI
import json

sourceLang = "日语"
targetLang = "中文"

book = epub.read_epub('testBook/yourbook.epub')

client1 = OpenAI(
    api_key=os.environ.get("ALIYUN_API_KEY","your-api-key"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
client2 = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY","your-api-key"),
    base_url="https://api.deepseek.com/v1"
)
model = "qwen-max"

SummaryPersona = f'''
请根据以下要求，参照以下格式以{targetLang}总结小说章节内容：
你应该完全依照给出的内容进行总结，不应附加你所知道的任意其他知识。


1. **人物**：列出本章中出现的主要人物及其身份或关系。
2. **时间**：指出本章发生的时间背景（如具体年份、季节、时间段等）。
3. **地点**：描述本章故事发生的主要地点或场景。
4. **主要动作**：概括本章中发生的关键事件或情节发展。
5. **提出的概念**：总结本章中提到的核心概念、主题或思想。
6. **其他重要细节**：补充任何对理解本章内容有帮助的细节或伏笔。

请根据以上要素，用简洁的语言总结本章内容，确保逻辑清晰、重点突出。
以下部分可能含有书籍最近章节的内容，请参考这些内容进行总结。
'''
TranslatorPersona = f'''
以上是该书籍的背景信息，请严格参考这些信息进行翻译。人名、地名等信息需要完全参考背景信息。
请将以下书籍内容从{sourceLang}翻译为{targetLang}。翻译时需确保语义准确、表达流畅，并尽量保持原文的格式、风格和语气。具体要求如下：
语义忠实：翻译应准确传达原文的意思，避免添加或遗漏重要信息。
格式一致：保留原文的段落结构、标题、列表、引用等格式。
风格贴近：根据原文的风格（如正式、幽默、学术等）调整翻译语言。
文化适配：若原文涉及文化特定内容，需适当调整以符合目标语言读者的理解。
术语统一：确保专业术语的翻译一致，必要时可提供术语表。
避免重复：当一个字在句中连续出现五次以上时，你应该考虑是否陷入了循环翻译，并且主动结束这一句，开始翻译下一句。

翻译时的格式要求：
所有引号使用「」进行翻译
所有换行之间不使用空行
段落之间的分隔符使用三个横线（---）进行分隔


注意事项：
翻译完成后，请检查语法、拼写和标点符号。
若遇到不确定的内容，可标注并说明。
提交时仅输出翻译版本及必要的注释。你不应该输出原文或其他无关内容。你不应该输出提供给你的背景信息。
'''
ComparePersona = ""

bookBackground = f"这本书的标题是《{book.get_metadata('DC', 'title')[0][0]}》，作者是{book.get_metadata('DC', 'creator')[0][0]}。\n"
contextBackground = ""


def extractBookItems(book):
    book_content = []
    for item in book.get_items():
        # print(item.get_type())
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = bs4.BeautifulSoup(item.get_body_content())
            text = soup.get_text().strip("\n")
            # print(text)
            if text:
                book_content.append({"type": "text", "content": text, "format": soup})
            else:
                book_content.append({"type": "other", "content": "", "format": soup})
        else:
            book_content.append({"type": "item", "content": "", "format": item})
    return book_content





def LLMTranslator(book_content, book_summary, book_translation, start_idx=0):
    count = 0
    for content in book_content:
        if content["type"] == "text":
            count += 1
            if count < start_idx:
                continue
            print(f"Processing {count}th content...")
            try:
                # summary
                stream = client1.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": bookBackground + SummaryPersona + "\n".join(
                            book_summary if len(book_summary) <= 3 else book_summary[-3:])},
                        {"role": "user", "content": content["content"]}
                    ],
                    stream=True,
                    timeout=200,
                    presence_penalty=0.4
                )
                response = ""
                for chunk in stream:
                    if chunk.choices:
                        response += chunk.choices[0].delta.content
                        print(chunk.choices[0].delta.content, end="")
                book_summary.append(response)
                # translation
                print(f"Translating {count}th content...")
                contextBackground = bookBackground + "\n".join(
                    book_summary if len(book_summary) <= 3 else book_summary[-3:])
                stream = client1.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": contextBackground + TranslatorPersona},
                        {"role": "user", "content": "以下是需要翻译的内容,注意：你必须只输出以下内容的翻译版本：\n" + content[
                            "content"] + f"请将这一章的内容翻译成{targetLang}。"}
                    ],
                    stream=True,
                    timeout=200,
                    presence_penalty=2.0,
                    top_p=0.9,

                )
                response = ""
                for chunk in stream:
                    if chunk.choices:
                        response += chunk.choices[0].delta.content
                        print(chunk.choices[0].delta.content, end="")
                book_translation.append(response)
                # save
                with open("progress.json", "w") as f:
                    json.dump({"book_summary": book_summary, "book_translation": book_translation}, f, ensure_ascii=False)
            except Exception as e:
                print(f"Found error: {e}")
                exit(1)

# rebuild epub
def epubRebuilder(book, book_content, book_translation,output_path="epubOutput/output.epub"):
    newBook = epub.EpubBook()
    newBook.set_identifier(book.get_metadata('DC', 'identifier')[0][0])
    newBook.set_title(book.get_metadata('DC', 'title')[0][0])
    newBook.add_author(book.get_metadata('DC', 'creator')[0][0])
    # 设置css样式
    css = epub.EpubItem(uid="style_css", file_name="style/style.css", media_type="text/css")
    css.content = open("epubTemplates/Style.css").read()
    newBook.add_item(css)

    from jinja2 import Environment, FileSystemLoader

    count = 0
    html_count = 0
    template = Environment(loader=FileSystemLoader("epubTemplates")).get_template("00.html")
    for idx, content in enumerate(book_content):
        if content["type"] == "text":
            item = epub.EpubItem(file_name=f'Text/{html_count}.xhtml')
            TranslatedContent = book_translation[count].replace("\n\n", "\n").split("\n")
            context = {
                "title": book.get_metadata('DC', 'title')[0][0],
                "contents": TranslatedContent,
            }
            item.content = template.render(context)
            newBook.add_item(item)
            newBook.toc.append(item)
            newBook.spine.append(item)
            count += 1
            html_count += 1
        elif content["type"] == "other":
            item = epub.EpubHtml(title="", file_name=f'Text/{html_count}.xhtml', lang=None)
            item.content = str(content["format"].contents[0])
            newBook.add_item(item)
            newBook.toc.append(item)
            newBook.spine.append(item)
            html_count += 1
        elif content["type"] == "item":
            newBook.add_item(content["format"])
            newBook.toc.append(content["format"])

    newBook.add_item(epub.EpubNcx())
    newBook.add_item(epub.EpubNav())

    epub.write_epub(output_path, newBook, {})


def cleanUp():
    os.remove("progress.json")

def main():
    book_content = extractBookItems(book)
    book_summary = []
    book_translation = []
    start_idx = 0
    # resume from progress.json
    try:
        with open("progress.json", "r") as f:
            progress = json.load(f)
            book_summary = progress["book_summary"]
            book_translation = progress["book_translation"]
            if len(book_summary) != len(book_translation):
                book_summary = book_summary[:min(len(book_summary), len(book_translation))]
                book_translation = book_translation[:min(len(book_summary), len(book_translation))]
            start_idx = len(book_summary)
            print(f"Resuming from index {start_idx}")
    except:
        pass
    LLMTranslator(book_content, book_summary, book_translation, start_idx)
    epubRebuilder(book, book_content, book_translation,output_path="epubOutput/"+book.get_metadata('DC', 'title')[0][0]+".epub")
    cleanUp()


if __name__ == "__main__":
    main()