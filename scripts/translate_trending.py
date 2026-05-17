#!/usr/bin/env python3
"""
translate_trending.py - 获取 GitHub Trending Top 3 并翻译

支持多 Provider：GLM / OpenAI / DeepSeek
用户通过 GITHUB_TO_HUMAN_PROVIDER 环境变量选择，默认 glm

Usage:
    GITHUB_TO_HUMAN_PROVIDER=openai python3 translate_trending.py
"""

import json
import requests
import sys
import re
import os

# ============ Provider 配置 ============
PROVIDER = os.getenv("GITHUB_TO_HUMAN_PROVIDER", "glm")

PROVIDER_CONFIG = {
    "glm": {
        "env_key": "GLM_API_KEY",
        "model": "glm-4-flash",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    },
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1/chat/completions",
    },
    "deepseek": {
        "env_key": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1/chat/completions",
    },
}

def get_api_config():
    config = PROVIDER_CONFIG.get(PROVIDER, PROVIDER_CONFIG["glm"])
    api_key = os.getenv(config["env_key"])
    if not api_key:
        raise ValueError(f"未设置 {config['env_key']}，请先配置 API key")
    return config, api_key

def call_ai(prompt: str) -> str:
    config, api_key = get_api_config()
    
    url = config["base_url"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": config["model"],
        "messages": [{"role": "user", "content": prompt}]
    }
    
    resp = requests.post(url, headers=headers, json=data, timeout=90)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

# ============ GitHub Trending 获取 ============
def get_trending_repos():
    """解析 GitHub Trending HTML 页面获取今日热门"""
    url = "https://github.com/trending"
    req = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }, timeout=15)
    html = req.text
    
    repos = []
    # 直接匹配仓库链接
    pattern = r'<h2[^>]*>.*?<a[^>]+href="/([a-zA-Z0-9-_]+)/([a-zA-Z0-9-._]+)"'
    
    seen = set()
    for match in re.finditer(pattern, html, re.DOTALL):
        owner, repo = match.group(1), match.group(2)
        # 过滤非仓库链接
        if owner in seen or owner in ["apps", "sponsors", "trending", "collections"]:
            continue
        if ".." in repo or "/" in repo:
            continue
        repos.append({"owner": owner, "repo": repo})
        seen.add(owner)
        if len(repos) >= 10:
            break
    
    return repos

def get_repo_stars(owner, repo):
    """获取仓库的 stars 数量"""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    req = requests.get(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-to-human-skill"
    }, timeout=10)
    if req.status_code == 200:
        data = req.json()
        return data.get("stargazers_count", 0), data.get("description", "")
    return 0, ""

# ============ 翻译 Prompt ============
TRANSLATION_PROMPT = """你是一个科普作家，负责把 GitHub 上的技术项目翻译成普通人能直接上手的操作指南。

【项目】
- 仓库：{owner}/{repo}
- stars：{stars}
- 官方描述：{description}

【翻译要求】严格按以下格式输出 JSON，不要输出任何其他内容：

{{
    "hook": "一句话说明这东西能让你做什么，15-25字，直接说结果，不要出现项目名，不要说'这是一个'",
    "steps": ["步骤1（具体操作，普通人能照做，打开什么输入什么都要说清楚）", "步骤2", "步骤3"],
    "highlight": "1句话说明为什么比传统方案好，用'以前XXX现在YYY'或'相当于XXX'句式",
    "stars": {stars},
    "url": "https://github.com/{owner}/{repo}"
}}

【关键要求】
- steps 必须是具体操作，不能是'选择工具'或'配置环境'这种模糊描述
- 每个步骤要让普通人知道'打开什么、输入什么、点击什么'
- 如果需要技术基础，尽量简化到普通人在10分钟内能搞定
"""

def translate_single_repo(owner, repo, stars, description=""):
    """翻译单个仓库"""
    prompt = TRANSLATION_PROMPT.format(
        owner=owner,
        repo=repo,
        stars=stars,
        description=description
    )
    
    result = call_ai(prompt)
    
    try:
        output = result.strip()
        start = output.find('{')
        end = output.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(output[start:end])
    except:
        pass
    return {"error": f"JSON 解析失败: {result[:200]}"}

# ============ 输出格式化 ============
def format_output(owner, repo, repo_info, translation):
    """格式化输出"""
    if "error" in translation:
        return f"错误：{translation['error']}"
    
    hook = translation.get("hook", "")
    steps = translation.get("steps", [])
    highlight = translation.get("highlight", "")
    stars = translation.get("stars", repo_info.get("stars", 0))
    url = translation.get("url", f"https://github.com/{owner}/{repo}")
    
    stars_str = f"{stars//1000}k" if stars >= 1000 else str(stars)
    
    lines = [
        f"━━━ {owner} / {repo} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        hook,
        "",
        "怎么上手？（3步）",
    ]
    
    step_icons = ["1️⃣", "2️⃣", "3️⃣"]
    for i, step in enumerate(steps[:3]):
        lines.append(f"  {step_icons[i]} {step}")
    
    lines.extend(["", f"✨ 亮点：{highlight}", ""])
    lines.append(f"⭐ {stars_str} stars")
    lines.append(f"→ {url}")
    lines.append("")
    lines.append("⚠️ 安装前建议先看项目 README，实际步骤可能有差异")
    
    return "\n".join(lines)

# ============ 主程序 ============
def main():
    print(f"[{PROVIDER}] 正在获取 GitHub Trending...", file=sys.stderr)
    
    repos = get_trending_repos()
    
    if not repos:
        print("无法获取 Trending，使用备用方案", file=sys.stderr)
        repos = [
            {"owner": "mattpocock", "repo": "skills"},
            {"owner": "tinyhumansai", "repo": "openhuman"},
            {"owner": "anthropics", "repo": "skills"},
        ]
    
    print(f"找到 {len(repos)} 个仓库，准备翻译...", file=sys.stderr)
    
    results = []
    for i, r in enumerate(repos[:3]):
        print(f"[{i+1}/3] 正在翻译 {r['owner']}/{r['repo']}...", file=sys.stderr)
        stars, description = get_repo_stars(r["owner"], r["repo"])
        translation = translate_single_repo(r["owner"], r["repo"], stars, description)
        
        formatted = format_output(r["owner"], r["repo"], {"stars": stars}, translation)
        print(formatted)
        if i < 2:
            print("\n" + "─" * 50 + "\n")
        
        results.append({
            "owner": r["owner"],
            "repo": r["repo"],
            "stars": stars,
            "translation": translation
        })
    
    return results

if __name__ == "__main__":
    main()