#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本 - 只爬取前 3 个文档
"""

import json
import requests
import time
import os
import re
from html_to_markdown import html_to_markdown

# API 配置
API_URL = "https://svc-drcn.developer.huawei.com/community/servlet/consumer/cn/documentPortal/getDocumentById"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

DOCS_DIR = "docs"

def fetch_document(object_id, catalog_name="harmonyos-guides", language="cn"):
    """获取单个文档"""
    try:
        payload = {
            "objectId": object_id,
            "version": "",
            "catalogName": catalog_name,
            "language": language
        }
        response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("code") == 0 and result.get("value"):
            value = result["value"]
            return {
                "docId": value.get("docId"),
                "title": value.get("title"),
                "fileName": value.get("fileName"),
                "anchorList": value.get("anchorList", []),
                "content": value.get("content", {})
            }
        else:
            print(f"[错误] {object_id}: {result.get('message', '未知错误')}")
            return None
    except Exception as e:
        print(f"[错误] 请求失败 {object_id}: {str(e)}")
        return None

def sanitize_filename(filename):
    """清理文件名"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename.strip()

def main():
    print("测试：爬取前 3 个文档并保存")
    print("=" * 80)
    
    # 测试数据
    test_docs = [
        {"nodeName": "应用开发导读", "relateDocument": "application-dev-guide", "path": "基础入门/应用开发导读"},
        {"nodeName": "开发准备", "relateDocument": "start-overview", "path": "基础入门/快速入门/开发准备"},
        {"nodeName": "快速入门", "relateDocument": "quick-start", "path": "基础入门/快速入门"},
    ]
    
    # 创建 docs 目录
    os.makedirs(DOCS_DIR, exist_ok=True)
    print(f"✓ 创建目录: {os.path.abspath(DOCS_DIR)}\n")
    
    for i, doc in enumerate(test_docs, 1):
        print(f"[{i}/3] 爬取: {doc['nodeName']} ({doc['relateDocument']})")
        
        # 爬取文档
        doc_info = fetch_document(doc["relateDocument"])
        
        if doc_info:
            # 构建文件路径
            file_path = os.path.join(DOCS_DIR, sanitize_filename(doc["path"]) + ".md")
            
            # 创建目录
            dir_path = os.path.dirname(file_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # 构建 Markdown 内容
            markdown_content = f"""# {doc_info.get('title', 'Untitled')}

**来源**: {doc['nodeName']}  
**文件名**: {doc_info.get('fileName', 'N/A')}

"""
            
            # 添加锚点列表
            if doc_info.get("anchorList"):
                markdown_content += "## 目录\n\n"
                for anchor in doc_info["anchorList"]:
                    markdown_content += f"- {anchor.get('title', 'Unknown')}\n"
                markdown_content += "\n"
            
            # 转换 HTML 到 Markdown
            if doc_info.get("content") and doc_info["content"].get("content"):
                html_content = doc_info["content"]["content"]
                markdown_body = html_to_markdown(html_content)
                markdown_content += "## 内容\n\n"
                markdown_content += markdown_body
            
            # 保存文件
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                print(f"  ✓ 保存成功: {file_path}")
            except Exception as e:
                print(f"  ✗ 保存失败: {str(e)}")
        else:
            print(f"  ✗ 爬取失败")
        
        time.sleep(0.5)
        print()
    
    print("=" * 80)
    print("测试完成！请检查 docs 目录")
    print("=" * 80)

if __name__ == "__main__":
    main()
