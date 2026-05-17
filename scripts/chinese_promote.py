#!/usr/bin/env python3
"""
chinese_promote.py - 推广到国内技术社区

支持平台：掘金、V2EX、开源中国、CSDN

用法：
    python3 chinese_promote.py --platform all --dry-run  # 测试模式
    python3 chinese_promote.py --platform all             # 实际发布
"""

import requests
import time
import json
import os
import argparse
from datetime import datetime

TOOL_NAME = "github-to-human"
TOOL_URL = "https://github.com/nonlinearHuman/github-to-human"

CONTENT_TEMPLATE = """# GitHub 说人话 — 把技术文档翻译成人话 🤖

## 它是什么？

一个 Python 脚本，把任意 GitHub 项目的 README 翻译成**普通人能看懂的操作指南**。

## 输出示例

输入 `facebook/react`，输出：

```
📦 facebook/react
⭐ 245k+ stars

💡 快速构建互动UI

📖 构建用户界面的JavaScript库

⚡ 怎么用？
   1️⃣ 访问 React 官网，了解基本概念
   2️⃣ 选择「快速开始」或「创建新项目」
   3️⃣ 按教程逐步学习

✨ 亮点：以前开发界面复杂且耗时，现在用 React 轻松实现

🔗 还有这些类似选择：
   • trekhleb/javascript-algorithms ⭐195k+
     做算法题的最佳刷题伴侣
```

## 核心功能

- ✅ 输入任意 GitHub 链接 → 输出通俗版介绍
- ✅ 3 步具体操作，照着做就能用
- ✅ 相似项目推荐，有对比有选择
- ✅ AI 生成的一句话说名

## 支持的 AI

GLM / OpenAI / DeepSeek / MiniMax，用自己的 key，自己掌控。

## 开源地址

🔗 {url}

---

*作者：Alex，打造 7x24 小时全自动运转的数字公司*
"""

# ============ 平台配置 ============
PLATFORMS = {
    "juejin": {
        "name": "掘金",
        "url": "https://api.juejin.cn/content/v1/article",
        "requires_auth": True,
        "note": "需配置 JUEJIN_COOKIE 环境变量"
    },
    "v2ex": {
        "name": "V2EX",
        "url": "https://www.v2ex.com/new",
        "requires_auth": False,
        "note": "无需 API，但发帖需要 cookie"
    },
    "oschina": {
        "name": "开源中国",
        "url": "https://www.oschina.net/blog",
        "requires_auth": False,
        "note": "无需 API，但发帖需要登录"
    },
}


def post_juejin(title, content, cookie=None):
    """发布到掘金"""
    if not cookie:
        return False, "未配置 JUEJIN_COOKIE"
    
    try:
        headers = {
            "Cookie": cookie,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        data = {
            "title": title,
            "content": content,
            "type": "article",
            "tag": "Python"
        }
        resp = requests.post(
            "https://api.juejin.cn/content/v1/article",
            headers=headers,
            json=data,
            timeout=15
        )
        if resp.status_code == 200:
            result = resp.json()
            if result.get("err_no") == 0:
                return True, f"https://juejin.cn/post/{result['data']['article_id']}"
            return False, result.get("err_msg", "未知错误")
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)


def generate_content(platform="通用"):
    """生成各平台适配的内容"""
    base = CONTENT_TEMPLATE.format(url=TOOL_URL)
    
    if platform == "juejin":
        return {
            "title": "开源 | GitHub 说人话 — 让技术文档变成3步上手指南",
            "content": base + "\n\n---\n\n## 为什么做这个？\n\n我经常遇到这种情况：看到一个 GitHub 项目，想知道适不适合自己，但 README 全是技术术语，看半天看不懂。\n\n所以做了这个工具，让 AI 把 README 翻译成：\n- 一句话说明能做什么\n- 3 步具体操作\n- 和同类项目的对比\n\n全程用自己的 API key，不依赖任何第三方服务。"
        }
    elif platform == "v2ex":
        return {
            "title": f"做了一个工具：{TOOL_NAME}，把 GitHub 项目翻译成人话",
            "content": base + f"\n\n[项目地址]({TOOL_URL})"
        }
    elif platform == "oschina":
        return {
            "title": f"[开源] {TOOL_NAME} - GitHub 项目说人话工具",
            "content": base
        }
    else:
        return {
            "title": f"开源项目：{TOOL_NAME} - GitHub 说人话",
            "content": base
        }


def main():
    parser = argparse.ArgumentParser(description="推广到国内平台")
    parser.add_argument("--platform", default="all", help="平台: all/juejin/v2ex/oschina")
    parser.add_argument("--dry-run", action="store_true", help="测试模式，不实际发布")
    args = parser.parse_args()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始国内推广...")
    
    platforms = PLATFORMS.keys() if args.platform == "all" else [args.platform]
    
    results = []
    for p in platforms:
        print(f"\n处理 {PLATFORMS[p]['name']}...")
        
        content_data = generate_content(p)
        
        if args.dry_run:
            print(f"  [dry-run] 标题: {content_data['title']}")
            print(f"  [dry-run] 内容长度: {len(content_data['content'])} 字符")
            results.append({"platform": p, "status": "dry-run", "title": content_data['title']})
            continue
        
        # 发布
        if p == "juejin":
            cookie = os.getenv("JUEJIN_COOKIE", "")
            success, msg = post_juejin(content_data['title'], content_data['content'], cookie)
            results.append({"platform": p, "status": "success" if success else "failed", "message": msg})
            print(f"  {'✓' if success else '✗'} {msg}")
        
        time.sleep(1)
    
    # 生成报告
    report = [f"**🌏 国内平台推广报告 — {datetime.now().strftime('%m/%d %H:%M')}**\n"]
    for r in results:
        status_icon = "✅" if r.get("status") == "success" else ("🔄" if r.get("status") == "dry-run" else "❌")
        report.append(f"{status_icon} {r['platform']}: {r.get('message', r.get('title', 'N/A'))}")
    
    result_text = "\n".join(report)
    print(f"\n{result_text}")
    
    return result_text


if __name__ == "__main__":
    main()