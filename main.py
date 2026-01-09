#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenHarmony 文档爬虫完整流程
集成：爬取 -> HTML转Markdown -> 按树形结构保存到本地
"""

import json
import requests
import time
import sys
import os
import re
from typing import List, Dict, Optional
from html_to_markdown import html_to_markdown

# API 配置
API_URL = "https://svc-drcn.developer.huawei.com/community/servlet/consumer/cn/documentPortal/getDocumentById"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 请求延迟（秒）
REQUEST_DELAY = 0.5

# 输出目录
DOCS_DIR = "docs"


def fetch_document(object_id: str, catalog_name: str = "harmonyos-guides", language: str = "cn") -> Optional[Dict]:
    """
    获取单个文档的详细信息
    
    Args:
        object_id: 对象 ID（来自 relateDocument）
        catalog_name: 目录名称，默认为 "harmonyos-guides"
        language: 语言，默认为 "cn"
    
    Returns:
        包含文档信息的字典，如果请求失败返回 None
    """
    try:
        payload = {
            "objectId": object_id,
            "version": "",
            "catalogName": catalog_name,
            "language": language
        }
        response = requests.post(
            API_URL,
            json=payload,
            headers=HEADERS,
            timeout=10
        )
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
            print(f"[错误] 文档 {object_id}: {result.get('message', '未知错误')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"[错误] 请求失败 {object_id}: {str(e)}")
        return None
    except json.JSONDecodeError:
        print(f"[错误] JSON 解析失败 {object_id}")
        return None


def fetch_and_save_documents(
    category_file: str = "category.json",
    catalog_name: str = "harmonyos-guides",
    output_file: str = "documents.json",
    summary_file: str = "documents_summary.json",
    save_markdown: bool = True,
    skip_existing: bool = True
) -> Dict[str, any]:
    """
    从 category.json 爬取所有文档并实时保存
    
    Args:
        category_file: category.json 文件路径
        catalog_name: 目录名称，传递给 fetch_document
        output_file: 完整文档输出文件
        summary_file: 摘要输出文件
        save_markdown: 是否实时保存 Markdown 文件到 docs 目录
        skip_existing: 是否跳过已下载的文档
    
    Returns:
        包含爬取结果的字典
    """
    print("=" * 80)
    print("OpenHarmony 文档爬虫")
    print("=" * 80)
    print()
    
    # 读取 category.json
    try:
        with open(category_file, "r", encoding="utf-8") as f:
            category_data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到 {category_file} 文件")
        return {"success": False, "error": "File not found"}
    except json.JSONDecodeError:
        print(f"错误：{category_file} 文件格式不正确")
        return {"success": False, "error": "Invalid JSON"}
    
    # 提取文档 ID
    docs = _extract_doc_ids_with_path(category_data)
    print(f"[提取] 找到 {len(docs)} 个文档")
    
    # 创建 docs 目录
    if save_markdown:
        os.makedirs(DOCS_DIR, exist_ok=True)
        print(f"[创建] 输出目录: {os.path.abspath(DOCS_DIR)}")
    
    # 检查已下载的文档
    existing_files = set()
    skipped_count = 0
    if skip_existing and save_markdown and os.path.exists(DOCS_DIR):
        print(f"[检查] 扫描已下载的文档...")
        for doc in docs:
            file_path = os.path.join(DOCS_DIR, doc["path"] + ".md")
            if os.path.exists(file_path):
                existing_files.add(doc["path"])
        skipped_count = len(existing_files)
        if skipped_count > 0:
            print(f"[跳过] 发现 {skipped_count} 个已下载的文档，将跳过")
        else:
            print(f"[跳过] 未发现已下载的文档")
    
    print()
    
    # 爬取文档
    documents = []
    failed_count = 0
    saved_count = 0
    
    for i, doc in enumerate(docs, 1):
        object_id = doc["relateDocument"]
        node_name = doc["nodeName"]
        doc_path = doc["path"]
        
        # 检查是否已下载
        if skip_existing and doc_path in existing_files:
            print(f"[{i}/{len(docs)}] 跳过: {node_name} (已存在)")
            continue
        
        print(f"[{i}/{len(docs)}] 爬取: {node_name} ({object_id})", end=" ... ")
        
        doc_info = fetch_document(object_id, catalog_name=catalog_name)
        if doc_info:
            # 添加原始信息
            doc_info.update({
                "nodeName": node_name,
                "relateDocument": doc["relateDocument"],
                "nodeId": doc["nodeId"],
                "path": doc["path"],
                "isLeaf": doc["isLeaf"]
            })
            documents.append(doc_info)
            print("✓", end="")
            
            # 实时保存 Markdown 文件
            if save_markdown:
                try:
                    file_path = os.path.join(DOCS_DIR, doc["path"] + ".md")
                    
                    # 创建目录
                    dir_path = os.path.dirname(file_path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    
                    # 构建 Markdown 内容
                    markdown_content = f"""# {doc_info.get('title', 'Untitled')}

**来源**: {node_name}  
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
                    
                    # 写入文件
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    saved_count += 1
                    print(" [已保存]")
                except Exception as e:
                    print(f" [保存失败: {str(e)}]")
            else:
                print()
        else:
            failed_count += 1
            print("✗")
        
        # 延迟请求
        time.sleep(REQUEST_DELAY)
    
    print()
    print(f"[完成] 成功爬取 {len(documents)}/{len(docs)} 个文档")
    if save_markdown:
        print(f"[完成] 成功保存 {saved_count} 个 Markdown 文件")
    if skipped_count > 0:
        print(f"[跳过] {skipped_count} 个文档已存在")
    if failed_count > 0:
        print(f"[失败] {failed_count} 个文档爬取失败")
    print()
    
    # 保存完整文档
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    print(f"[保存] 完整数据已保存到 {output_file}")
    
    # 生成摘要
    summary = []
    for doc in documents:
        summary.append({
            "nodeName": doc.get("nodeName"),
            "title": doc.get("title"),
            "fileName": doc.get("fileName"),
            "path": doc.get("path"),
            "anchorCount": len(doc.get("anchorList", [])),
            "anchors": [a.get("title") for a in doc.get("anchorList", [])]
        })
    
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"[保存] 摘要已保存到 {summary_file}")
    
    return {
        "success": True,
        "total": len(docs),
        "successful": len(documents),
        "failed": failed_count,
        "saved": saved_count,
        "skipped": skipped_count,
        "documents": documents
    }


def _extract_doc_ids_with_path(data: List[Dict], path: str = "") -> List[Dict]:
    """
    从 category.json 递归提取所有文档信息，包含路径信息
    返回包含 nodeName, relateDocument, path 的列表
    """
    docs = []
    
    def traverse(nodes, current_path):
        for node in nodes:
            node_name = node.get("nodeName", "")
            relate_doc = node.get("relateDocument", "")
            
            # 构建路径
            if current_path:
                node_path = f"{current_path}/{_sanitize_filename(node_name)}"
            else:
                node_path = _sanitize_filename(node_name)
            
            # 添加文档信息
            if node_name and relate_doc:
                docs.append({
                    "nodeName": node_name,
                    "relateDocument": relate_doc,
                    "relateDocId": node.get("relateDocId", ""),
                    "nodeId": node.get("nodeId", ""),
                    "path": node_path,
                    "isLeaf": node.get("isLeaf", True)
                })
            
            # 递归处理子节点
            children = node.get("children", [])
            if children:
                traverse(children, node_path if node_name else current_path)
    
    traverse(data, path)
    return docs


def _sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除特殊字符
    """
    # 移除特殊字符，保留中文、英文、数字、下划线、连字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename.strip()


if __name__ == "__main__":
    # 完整流程：边爬取边保存，支持断点续传
    print("\n" + "=" * 80)
    print("OpenHarmony 文档爬虫 - 边爬取边保存（支持断点续传）")
    print("=" * 80)
    print()
    
    result = fetch_and_save_documents(
        category_file="category.json",
        catalog_name="harmonyos-guides",
        output_file="documents.json",
        summary_file="documents_summary.json",
        save_markdown=True,  # 实时保存 Markdown
        skip_existing=True   # 跳过已下载的文档
    )
    
    if not result.get("success"):
        print("\n[错误] 文档爬取失败")
        sys.exit(1)
    
    print()
    print("=" * 80)
    print("全部完成！")
    print("=" * 80)
    print(f"✓ 爬取文档: {result['successful']}/{result['total']}")
    print(f"✓ 保存文件: {result['saved']} 个 Markdown 文件")
    if result.get('skipped', 0) > 0:
        print(f"⊘ 跳过: {result['skipped']} 个文档（已存在）")
    if result.get('failed', 0) > 0:
        print(f"⚠ 失败: {result['failed']} 个文档")
    print(f"✓ 输出目录: {os.path.abspath(DOCS_DIR)}")
