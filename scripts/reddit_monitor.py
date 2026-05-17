#!/usr/bin/env python3
"""
reddit_monitor.py - 监控 Reddit 相关帖子，支持自动回复

依赖：pip install requests
无需 PRAW，用 Reddit 公开 API

用法：
  python3 reddit_monitor.py              # 搜索 + 输出报告
  python3 reddit_monitor.py --auto       # 搜索 + 自动回复（需配置 Reddit 凭证）
  python3 reddit_monitor.py --test       # 测试模式，输出建议但不实际发帖
"""

import requests
import re
import time
import json
import os
import sys
import argparse
from datetime import datetime, timedelta

# ============ 配置 ============
TOOL_URL = "https://github.com/nonlinearHuman/github-to-human"
TOOL_NAME = "github-to-human"

# Reddit App 凭证（可选，不填则只输出报告）
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")
REDDIT_USER_AGENT = "github-to-human promotional bot v1.0"

SEARCH_SUBREDDITS = ["Python", "programming", "learnpython", "sideproject", "BuildInPublic"]

SEARCH_QUERIES_BY_SUB = {
    "Python": [
        "github readme tool",
        "useful github scripts python",
        "github project recommendation",
    ],
    "programming": [
        "github alternatives useful",
        "understand github project fast",
        "best github tools developers",
    ],
    "learnpython": [
        "github projects beginners",
        "useful python tools github",
        "python project ideas github",
    ],
    "sideproject": [
        "github tools useful",
        "open source project finder",
    ],
}

# ============ Reddit API ============
def get_reddit_token():
    """获取 Reddit API token"""
    if not REDDIT_CLIENT_ID:
        return None
    try:
        resp = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            data={"grant_type": "password", "username": REDDIT_USERNAME, "password": REDDIT_PASSWORD},
            headers={"User-Agent": REDDIT_USER_AGENT},
            auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception as e:
        print(f"获取 token 失败: {e}")
    return None


def search_reddit_posts(subreddit, query, token=None, limit=10):
    """搜索 Reddit 帖子"""
    try:
        headers = {
            "User-Agent": REDDIT_USER_AGENT,
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {"q": query, "limit": limit, "sort": "relevance", "t": "month"}
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        posts = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            posts.append({
                "id": d.get("name", ""),  # t3_xxx
                "title": d.get("title", ""),
                "url": f"https://reddit.com{d.get("permalink", "")}",
                "subreddit": d.get("subreddit", ""),
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
                "created_utc": d.get("created_utc", 0),
                "selftext": d.get("selftext", "")[:200],
            })
        return posts
    except Exception as e:
        print(f"搜索 r/{subreddit} 出错: {e}")
        return []


def should_reply(post, seen_ids):
    """判断是否值得回复"""
    if post["id"] in seen_ids:
        return False
    
    title = post["title"].lower() + " " + post["selftext"].lower()
    
    # 排除词
    exclude = ["nsfw", "onlyfans", "giveaway", "spam", "crypto scam"]
    if any(w in title for w in exclude):
        return False
    
    # 匹配词
    positive = any(k in title for k in [
        "github", "readme", "confusing", "understand", "useful", "recommend",
        "tool", "project recommendation", "alternatives", "vs", "comparison",
        "beginner", "open source", "cli", "script", "useful tool"
    ])
    
    # 至少要有一定热度（避免 necro 回复）
    if post["score"] < 2 and post["num_comments"] < 2:
        return False
    
    return positive


def generate_reply(post):
    """生成推广回复"""
    title = post.get("title", "").lower()
    
    # 根据帖子类型选择模板
    if "confusing" in title or "understand" in title or "don" in title:
        template = """This is exactly the problem I ran into — so I built `github-to-human` to solve it.

It uses AI to translate any GitHub repo's README into a plain-language 3-step guide. No more squinting at technical docs.

**Example:** input `facebook/react` → output:
- 💡 快速构建互动UI  
- ⚡ Step 1: Visit React.dev, Step 2: Choose "Start a New Project", Step 3: Follow the tutorial
- 🔗 Compared with 3 similar projects

Supports **GLM / OpenAI / DeepSeek / MiniMax** — your key, your choice.

[github.com/nonlinearHuman/github-to-human]({url})

*Free & open source* 🤖"""
    elif "recommend" in title or "best" in title or "alternatives" in title:
        template = """For understanding what a GitHub project actually does before you dive in — I made `github-to-human`.

It translates any repo into plain language + 3 concrete steps to get started + similar project comparisons.

Supports GLM / OpenAI / DeepSeek / MiniMax (bring your own API key).

[github.com/nonlinearHuman/github-to-human]({url})"""
    elif "beginner" in title or "new to" in title or "start" in title:
        template = """One thing that helped me: `github-to-human` — turns scary GitHub READMEs into friendly 3-step guides.

Great for exploring new projects without the docs wall.

[github.com/nonlinearHuman/github-to-human]({url})"""
    else:
        template = """Not sure if this fits, but I built `github-to-human` — a tool that translates GitHub repos into human-readable step-by-step guides.

Might be useful for digging into this.

[github.com/nonlinearHuman/github-to-human]({url})"""
    
    return template.format(url=TOOL_URL)


def post_reply(post_id, reply_text, token):
    """发帖回复"""
    try:
        resp = requests.post(
            "https://oauth.reddit.com/api/comment",
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": REDDIT_USER_AGENT,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "api_type": "json",
                "thing_id": post_id,
                "text": reply_text,
            },
            timeout=15
        )
        result = resp.json()
        if result.get("json", {}).get("errors"):
            return False, result["json"]["errors"]
        return True, "posted"
    except Exception as e:
        return False, str(e)


# ============ 主程序 ============
def main():
    parser = argparse.ArgumentParser(description="Reddit 推广监控")
    parser.add_argument("--auto", action="store_true", help="自动发帖（需配置 Reddit 凭证）")
    parser.add_argument("--test", action="store_true", help="测试模式：只输出，不发帖")
    args = parser.parse_args()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始监控 Reddit...", flush=True)
    
    # 获取 token
    token = None
    if args.auto and REDDIT_CLIENT_ID:
        token = get_reddit_token()
        if token:
            print("✓ Reddit API 认证成功")
        else:
            print("✗ Reddit API 认证失败，将只输出报告")
    
    # 加载已处理记录
    cache_file = os.path.join(os.path.dirname(__file__), "../data/seen_posts.json")
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    try:
        with open(cache_file) as f:
            seen = set(json.load(f))
    except:
        seen = set()
    
    all_targets = []
    
    # 搜索各 subreddit
    for sub, queries in SEARCH_QUERIES_BY_SUB.items():
        for q in queries:
            posts = search_reddit_posts(sub, q, token)
            for p in posts:
                if should_reply(p, seen):
                    p["query"] = q
                    all_targets.append(p)
                    seen.add(p["id"])
                    print(f"  ✓ 发现目标: r/{sub} - {p['title'][:50]}...")
            time.sleep(0.5)
    
    # 保存已处理记录
    with open(cache_file, "w") as f:
        json.dump(list(seen)[-200:], f)
    
    if not all_targets:
        print("未发现合适的目标帖子")
        return
    
    print(f"\n发现 {len(all_targets)} 条潜在目标\n")
    
    # 生成报告
    report_lines = [f"**🎯 Reddit 推广报告 — {datetime.now().strftime('%m/%d %H:%M')}**\n"]
    report_lines.append(f"发现 {len(all_targets)} 条目标\n")
    
    # 自动模式：发帖 + 报告
    for i, post in enumerate(all_targets[:3], 1):
        reply = generate_reply(post)
        print(f"\n{'='*50}")
        print(f"[{i}] {post['title']}")
        print(f"URL: {post['url']}")
        print(f"Score: {post['score']} | Comments: {post['num_comments']}")
        print(f"\n建议回复：\n{reply}\n")
        
        if args.auto and token and not args.test:
            success, msg = post_reply(post["id"], reply, token)
            if success:
                print(f"✓ 已自动回复!")
                report_lines.append(f"✅ [{i}] 已自动回复: {post['title']}")
            else:
                print(f"✗ 回复失败: {msg}")
                report_lines.append(f"❌ [{i}] 回复失败: {post['title']} - {msg}")
        else:
            report_lines.append(f"📝 [{i}] 建议回复: {post['title']}")
    
    report = "\n".join(report_lines)
    print(f"\n{'='*50}\n{report}")
    
    # 保存报告
    report_file = os.path.join(os.path.dirname(__file__), "../data/last_report.md")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w") as f:
        f.write(report)
    
    return report


if __name__ == "__main__":
    main()