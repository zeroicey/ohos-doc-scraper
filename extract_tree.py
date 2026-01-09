#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys

def extract_tree(nodes, indent=0):
    """
    递归提取 nodeName 和 relateDocument，并按树形结构展示
    """
    if not nodes:
        return
    
    for node in nodes:
        prefix = "  " * indent + "├─ " if indent > 0 else ""
        
        node_name = node.get("nodeName", "N/A")
        relate_doc = node.get("relateDocument", "")
        
        # 格式化输出：nodeName (relateDocument)
        if relate_doc:
            print(f"{prefix}{node_name} ({relate_doc})")
        else:
            print(f"{prefix}{node_name}")
        
        # 递归处理子节点
        children = node.get("children", [])
        if children:
            extract_tree(children, indent + 1)

def main():
    # 读取 category.json 文件
    try:
        with open("category.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("错误：找不到 category.json 文件")
        sys.exit(1)
    except json.JSONDecodeError:
        print("错误：JSON 文件格式不正确")
        sys.exit(1)
    
    print("OpenHarmony 文档结构树")
    print("=" * 80)
    print()
    
    extract_tree(data)

if __name__ == "__main__":
    main()
