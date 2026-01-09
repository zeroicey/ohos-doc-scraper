#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML 转 Markdown 转换模块
使用 html2text 库进行专业的转换
"""

import json
import html2text
from typing import Dict, List, Optional


def html_to_markdown(html_content: str) -> str:
    """
    将 HTML 内容转换为 Markdown
    使用 html2text 库进行转换
    
    Args:
        html_content: HTML 字符串
    
    Returns:
        Markdown 字符串
    """
    if not html_content:
        return ""
    
    try:
        # 创建转换器实例
        h = html2text.HTML2Text()
        
        # 配置转换选项
        h.ignore_links = False  # 保留链接
        h.ignore_images = False  # 保留图片
        h.ignore_emphasis = False  # 保留强调（粗体、斜体）
        h.body_width = 0  # 不自动换行
        h.unicode_snob = True  # 使用 Unicode 字符
        h.skip_internal_links = True  # 跳过内部锚点链接
        h.ignore_anchors = True  # 忽略 <a name> 标签
        h.protect_links = True  # 保护链接不被转义
        h.wrap_links = False  # 不换行链接
        
        # 转换
        markdown = h.handle(html_content)
        
        # 清理多余的空行（超过 2 个连续空行合并为 2 个）
        import re
        markdown = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown)
        
        return markdown.strip()
        
    except Exception as e:
        print(f"[警告] HTML 转换失败: {str(e)}")
        return html_content


def process_documents_to_markdown(
    documents_file: str = "documents.json",
    output_file: str = "documents_markdown.json"
) -> Dict[str, any]:
    """
    将 documents.json 中的 HTML 内容转换为 Markdown
    
    Args:
        documents_file: 输入的 documents.json 文件路径
        output_file: 输出的 Markdown 格式文件路径
    
    Returns:
        转换结果统计
    """
    print("=" * 80)
    print("文档 HTML 转 Markdown 处理")
    print("=" * 80)
    print()
    
    # 读取文档
    try:
        with open(documents_file, "r", encoding="utf-8") as f:
            documents = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到 {documents_file} 文件")
        return {"success": False, "error": "File not found"}
    except json.JSONDecodeError:
        print(f"错误：{documents_file} 文件格式不正确")
        return {"success": False, "error": "Invalid JSON"}
    
    print(f"[读取] 读取 {len(documents)} 个文档")
    print()
    
    # 转换文档
    converted_documents = []
    for i, doc in enumerate(documents, 1):
        print(f"[{i}/{len(documents)}] 转换: {doc.get('nodeName', 'Unknown')}")
        
        # 转换 content 中的 HTML
        if doc.get("content") and doc["content"].get("content"):
            html_content = doc["content"]["content"]
            markdown_content = html_to_markdown(html_content)
            
            doc["content"]["markdown"] = markdown_content
        
        converted_documents.append(doc)
    
    print()
    print(f"[完成] 转换完成")
    print()
    
    # 保存转换后的文档
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(converted_documents, f, ensure_ascii=False, indent=2)
    
    print(f"[保存] 结果已保存到 {output_file}")
    
    return {
        "success": True,
        "total": len(documents),
        "converted": len(converted_documents),
        "output_file": output_file
    }


def create_markdown_files(
    documents_file: str = "documents.json",
    output_dir: str = "markdown_docs"
) -> Dict[str, any]:
    """
    为每个文档创建独立的 Markdown 文件
    
    Args:
        documents_file: 输入的 documents.json 文件路径
        output_dir: 输出目录
    
    Returns:
        创建结果统计
    """
    import os
    
    print("=" * 80)
    print("生成独立 Markdown 文件")
    print("=" * 80)
    print()
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取文档
    try:
        with open(documents_file, "r", encoding="utf-8") as f:
            documents = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到 {documents_file} 文件")
        return {"success": False, "error": "File not found"}
    except json.JSONDecodeError:
        print(f"错误：{documents_file} 文件格式不正确")
        return {"success": False, "error": "Invalid JSON"}
    
    print(f"[读取] 读取 {len(documents)} 个文档")
    print()
    
    # 检查是否有 markdown 字段，没有则转换
    need_convert = any(
        not doc.get("content", {}).get("markdown") 
        for doc in documents
    )
    
    if need_convert:
        print("[转换] 文档尚未转换，正在进行 HTML 转 Markdown...")
        for doc in documents:
            if doc.get("content") and doc["content"].get("content"):
                if not doc["content"].get("markdown"):
                    html_content = doc["content"]["content"]
                    markdown_content = html_to_markdown(html_content)
                    doc["content"]["markdown"] = markdown_content
        print()
    
    # 生成 Markdown 文件
    created_count = 0
    for i, doc in enumerate(documents, 1):
        file_name = doc.get("fileName", f"doc_{i}")
        file_path = os.path.join(output_dir, f"{file_name}.md")
        
        # 构建 Markdown 内容
        markdown_content = f"""# {doc.get('title', 'Untitled')}

**来源**: {doc.get('nodeName', 'Unknown')}

"""
        
        # 添加锚点列表
        if doc.get("anchorList"):
            markdown_content += "## 目录\n\n"
            for anchor in doc["anchorList"]:
                markdown_content += f"- {anchor.get('title', 'Unknown')}\n"
            markdown_content += "\n"
        
        # 添加内容
        if doc.get("content") and doc["content"].get("markdown"):
            markdown_content += "## 内容\n\n"
            markdown_content += doc["content"]["markdown"]
        
        # 写入文件
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            print(f"[{i}/{len(documents)}] 生成: {file_name}.md")
            created_count += 1
        except Exception as e:
            print(f"[错误] 生成失败 {file_name}: {str(e)}")
    
    print()
    print(f"[完成] 成功生成 {created_count}/{len(documents)} 个 Markdown 文件")
    print(f"[位置] 输出目录: {os.path.abspath(output_dir)}")
    
    return {
        "success": True,
        "total": len(documents),
        "created": created_count,
        "output_dir": output_dir
    }


if __name__ == "__main__":
    # 转换为 Markdown 并保存到 JSON
    result1 = process_documents_to_markdown(
        documents_file="documents.json",
        output_file="documents_markdown.json"
    )
    print()
    print()
    
    # 生成独立的 Markdown 文件
    result2 = create_markdown_files(
        documents_file="documents.json",
        output_dir="markdown_docs"
    )
