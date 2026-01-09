#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
import time
from typing import List, Dict, Optional
from pathlib import Path

# API 配置
API_URL = "https://svc-drcn.developer.huawei.com/community/servlet/consumer/cn/documentPortal/getDocumentById"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 请求延迟（秒）
REQUEST_DELAY = 0.5


def extract_doc_ids(data: List[Dict]) -> List[Dict]:
    """
    从 category.json 递归提取所有文档信息
    返回包含 nodeName, relateDocument, relateDocId 的列表
    """
    docs = []
    
    def traverse(nodes):
        for node in nodes:
            if node.get("nodeName") and node.get("relateDocId"):
                docs.append({
                    "nodeName": node.get("nodeName"),
                    "relateDocument": node.get("relateDocument", ""),
                    "relateDocId": node.get("relateDocId"),
                    "nodeId": node.get("nodeId", "")
                })
            
            children = node.get("children", [])
            if children:
                traverse(children)
    
    traverse(data)
    return docs


def fetch_document(object_id: str, catalog_name: str = "harmonyos-guides") -> Optional[Dict]:
    """
    获取单个文档的详细信息
    
    Args:
        object_id: 对象 ID（来自 relateDocument）
        catalog_name: 目录名称，默认为 "harmonyos-guides"
    """
    try:
        payload = {
            "objectId": object_id,
            "version": "",
            "catalogName": catalog_name,
            "language": "cn"
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
        print(f"[错误] JSON 解析失败 {doc_id}")
        return None


def main():
    print("=" * 80)
    print("OpenHarmony 文档爬虫")
    print("=" * 80)
    print()
    
    # 读取 category.json
    try:
        with open("category.json", "r", encoding="utf-8") as f:
            category_data = json.load(f)
    except FileNotFoundError:
        print("错误：找不到 category.json 文件")
        return
    except json.JSONDecodeError:
        print("错误：category.json 文件格式不正确")
        return
    
    # 提取文档 ID
    docs = extract_doc_ids(category_data)
    print(f"[提取] 找到 {len(docs)} 个文档")
    print()
    
    # 爬取文档
    documents = []
    for i, doc in enumerate(docs, 1):
        object_id = doc["relateDocument"]
        node_name = doc["nodeName"]
        
        print(f"[{i}/{len(docs)}] 爬取: {node_name} ({object_id})")
        
        doc_info = fetch_document(object_id)
        if doc_info:
            # 添加原始信息
            doc_info.update({
                "nodeName": node_name,
                "relateDocument": doc["relateDocument"],
                "nodeId": doc["nodeId"]
            })
            documents.append(doc_info)
        
        # 延迟请求
        time.sleep(REQUEST_DELAY)
    
    print()
    print(f"[完成] 成功爬取 {len(documents)}/{len(docs)} 个文档")
    print()
    
    # 保存结果
    output_file = "documents.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"[保存] 结果已保存到 {output_file}")
    
    # 生成摘要
    summary_file = "documents_summary.json"
    summary = []
    for doc in documents:
        summary.append({
            "nodeName": doc.get("nodeName"),
            "title": doc.get("title"),
            "fileName": doc.get("fileName"),
            "anchorCount": len(doc.get("anchorList", [])),
            "anchors": [a.get("title") for a in doc.get("anchorList", [])]
        })
    
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"[保存] 摘要已保存到 {summary_file}")


if __name__ == "__main__":
    main()
