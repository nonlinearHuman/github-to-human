#!/usr/bin/env python3
"""
translate_repo.py - 翻译单个 GitHub 仓库为普通人能看懂的内容

支持多 Provider：GLM / OpenAI / DeepSeek
用户通过 GITHUB_TO_HUMAN_PROVIDER 环境变量选择，默认 glm

Usage:
    python3 translate_repo.py owner/repo
    python3 translate_repo.py https://github.com/owner/repo
"""

import sys
import json
import os
import base64
import requests

# ============ Provider 配置 ============
PROVIDER = os.getenv("GITHUB_TO_HUMAN_PROVIDER", "glm")

PROVIDER_CONFIG = {
    "glm": {
        "env_key": "GLM_API_KEY",
        "model": "glm-4-flash",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_format": "openai",
    },
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1/chat/completions",
        "api_format": "openai",
    },
    "deepseek": {
        "env_key": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1/chat/completions",
        "api_format": "openai",
    },
    "minimax": {
        "env_key": "MINIMAX_API_KEY",
        "model": "MiniMax-M2.5",
        "base_url": "https://api.minimaxi.com/v1/messages",
        "api_format": "anthropic",
    },
}

def get_api_config():
    """获取当前 Provider 的 API 配置"""
    config = PROVIDER_CONFIG.get(PROVIDER, PROVIDER_CONFIG["glm"])
    api_key = os.getenv(config["env_key"])
    if not api_key:
        raise ValueError(f"未设置 {config['env_key']}，请先配置 API key")
    return config, api_key

# ============ 工具函数 ============
def parse_input(text):
    """解析输入，支持 owner/repo 和完整 URL 两种格式"""
    text = text.strip().strip("/")
    if text.startswith("https://github.com/"):
        path = text.replace("https://github.com/", "")
        parts = path.split("/")
        return parts[0], parts[1].replace(".git", "")
    elif "/" in text:
        parts = text.split("/")
        return parts[0], parts[1].replace(".git", "")
    return None, None

def get_repo_info(owner, repo):
    """获取 GitHub 仓库基础信息"""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    req = requests.get(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "github-to-human-skill"
    }, timeout=15)
    if req.status_code == 404:
        return None, f"仓库 {owner}/{repo} 不存在或无法访问，请检查名称是否正确"
    data = req.json()
    return {
        "name": data.get("full_name", ""),
        "description": data.get("description", ""),
        "stars": data.get("stargazers_count", 0),
        "language": data.get("language", ""),
        "url": data.get("html_url", ""),
    }, None

def get_readme(owner, repo):
    """获取 README 内容"""
    branches = ["main", "master"]
    for branch in branches:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md?ref={branch}"
        req = requests.get(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "github-to-human-skill"
        }, timeout=15)
        if req.status_code == 200:
            data = req.json()
            if "content" in data:
                content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                return content[:6000]
    return ""


def get_similar_projects(owner, repo, language, topic=""):
    """获取相似项目推荐（最多3个）"""
    similar = []
    
    # 方式1：GitHub Related API
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        req = requests.get(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "github-to-human-skill"
        }, timeout=10)
        if req.status_code == 200:
            data = req.json()
            related_urls = data.get("related_repos", [])
            for r in related_urls[:3]:
                similar.append({
                    "name": r.get("full_name", ""),
                    "desc": r.get("description", "") or "无描述",
                    "stars": r.get("stargazers_count", 0),
                    "url": r.get("html_url", "")
                })
    except:
        pass
    
    # 方式2：按语言搜索同类型热门项目
    if not similar and language:
        try:
            search_url = f"https://api.github.com/search/repositories"
            params = {
                "q": f"language:{language} stars:>1000",
                "sort": "stars",
                "order": "desc",
                "per_page": 5
            }
            req = requests.get(search_url, headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "github-to-human-skill"
            }, params=params, timeout=10)
            if req.status_code == 200:
                items = req.json().get("items", [])
                for item in items:
                    if item["full_name"] != f"{owner}/{repo}":
                        similar.append({
                            "name": item.get("full_name", ""),
                            "desc": item.get("description", "") or "无描述",
                            "stars": item.get("stargazers_count", 0),
                            "url": item.get("html_url", "")
                        })
                    if len(similar) >= 3:
                        break
        except:
            pass
    
    return similar[:3]


def enrich_similar_projects(similar, main_project_desc):
    """用 AI 为相似项目生成一句话介绍"""
    if not similar:
        return similar
    
    # 准备项目信息
    projects_text = "\n".join([
        f"{i+1}. {p['name']} - {p['desc'][:80]}"
        for i, p in enumerate(similar)
    ])
    
    prompt = f"""你是一个推荐系统。基于以下主项目：
{main_project_desc}

为这些相似项目各写一句「普通人能看懂」的一句话介绍（15-25字）：
{projects_text}

要求：
- 用对比或场景说明，不只是重复描述
- 说人话，不说技术术语
- 输出格式：每行一个，序号+介绍，例：「1. 做算法题的最佳刷题伴侣」

直接输出，不要其他内容。"""
    
    try:
        config, api_key = get_api_config()
        
        if config.get("api_format") == "anthropic":
            data = {
                "model": config["model"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200
            }
        else:
            data = {
                "model": config["model"],
                "messages": [{"role": "user", "content": prompt}]
            }
        
        resp = requests.post(
            config["base_url"],
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=data,
            timeout=60
        )
        
        if resp.status_code == 200:
            result = resp.json()
            if config.get("api_format") == "anthropic":
                lines = result["content"][0]["text"].strip().split("\n")
            else:
                lines = result["choices"][0]["message"]["content"].strip().split("\n")
            
            for i, line in enumerate(lines):
                if i < len(similar):
                    # 去掉序号和前导空格
                    desc = line.strip()
                    if desc and desc[0].isdigit():
                        desc = desc.split(".", 1)[-1].strip()
                    similar[i]["ai_desc"] = desc
    except:
        pass
    
    return similar

# ============ AI 调用 ============
def call_ai(prompt: str) -> str:
    """调用 AI API（支持 GLM/OpenAI/DeepSeek/MiniMax）"""
    config, api_key = get_api_config()
    
    url = config["base_url"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    if config.get("api_format") == "anthropic":
        # MiniMax anthropic format
        data = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512
        }
    else:
        # OpenAI-compatible format
        data = {
            "model": config["model"],
            "messages": [{"role": "user", "content": prompt}]
        }
    
    resp = requests.post(url, headers=headers, json=data, timeout=90)
    resp.raise_for_status()
    result = resp.json()
    
    if config.get("api_format") == "anthropic":
        return result["content"][0]["text"]
    else:
        return result["choices"][0]["message"]["content"]

# ============ 翻译 Prompt ============
TRANSLATION_PROMPT = """你是一个科普作家，负责把 GitHub 上的技术项目翻译成普通人能直接上手的操作指南。

【项目】
- 仓库：{owner}/{repo}
- stars：{stars}
- 官方描述：{description}
- README：{readme}

【翻译要求】严格按以下格式输出 JSON，不要输出任何其他内容：

{{
    "tagline": "一句话说明这东西能让你做什么，20字以内，直接说结果，不出现项目名，不说'这是一个'",
    "what_it_does": "用一句话描述这个项目到底是做什么的，30字以内，普通人能理解",
    "steps": ["步骤1（具体操作，普通人能照做，打开什么输入什么都要说清楚）", "步骤2", "步骤3"],
    "highlight": "1句话说明为什么比传统方案好，用'以前XXX现在YYY'或'相当于XXX'句式",
    "why_matters": "一句话说明解决了什么痛点，20字以内",
    "stars": {stars},
    "url": "{url}"
}}

【关键要求】
- tagline：说结果，不说概念，不能以'这是一个'开头
- steps：必须是具体操作，不能模糊，每个步骤要让普通人知道'打开什么、输入什么、点击什么'
- 如果需要技术基础，尽量简化到普通人在10分钟内能搞定
- what_it_does 和 tagline 的区别：tagline 是营销金句，what_it_does 是功能描述
"""

def translate_content(repo_info, readme_content):
    """翻译内容"""
    owner, repo = repo_info["name"].split("/")
    
    prompt = TRANSLATION_PROMPT.format(
        owner=owner,
        repo=repo,
        stars=repo_info.get("stars", 0),
        description=repo_info.get("description", ""),
        readme=readme_content[:4000] if readme_content else "（无 README）",
        url=repo_info.get("url", "")
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
def format_output(owner, repo, repo_info, translation, similar_projects):
    """格式化输出"""
    if "error" in translation:
        return f"❌ 错误：{translation['error']}"
    
    tagline = translation.get("tagline", "")
    what_it_does = translation.get("what_it_does", "")
    steps = translation.get("steps", [])
    highlight = translation.get("highlight", "")
    why_matters = translation.get("why_matters", "")
    stars = translation.get("stars", repo_info.get("stars", 0))
    url = translation.get("url", f"https://github.com/{owner}/{repo}")
    
    # 数字缩写
    stars_str = f"{stars//1000}k+" if stars >= 1000 else str(stars)
    
    lines = []
    
    # 头部信息栏
    lines.append(f"📦 {owner}/{repo}")
    lines.append(f"⭐ {stars_str} stars")
    if repo_info.get("language"):
        lines.append(f"🔧 {repo_info['language']}")
    lines.append("─" * 40)
    
    # 核心价值（金句）
    lines.append(f"\n💡 {tagline}")
    lines.append(f"\n📖 {what_it_does}")
    
    # 为什么重要（痛点）
    if why_matters:
        lines.append(f"\n🎯 {why_matters}")
    
    # 操作步骤
    lines.append(f"\n⚡ 怎么用？")
    step_icons = ["1️⃣", "2️⃣", "3️⃣"]
    for i, step in enumerate(steps[:3]):
        lines.append(f"   {step_icons[i]} {step}")
    
    # 亮点
    if highlight:
        lines.append(f"\n✨ {highlight}")
    
    # 相似项目推荐
    if similar_projects:
        lines.append(f"\n🔗 还有这些类似选择：")
        for p in similar_projects:
            p_stars = f"{p['stars']//1000}k+" if p['stars'] >= 1000 else str(p['stars'])
            lines.append(f"   • {p['name']} ⭐{p_stars}")
            # AI 生成的一句话说名，fallback 到 GitHub 原始描述
            desc = p.get("ai_desc") or p.get("desc", "")
            desc = desc[:50] + "..." if len(desc) > 50 else desc
            lines.append(f"     {desc}")
    
    # 底部链接和警告
    lines.append("\n" + "─" * 40)
    lines.append(f"🔗 {url}")
    lines.append("💬 安装前建议先看项目 README，实际步骤可能有差异")
    
    return "\n".join(lines)

# ============ 主程序 ============
def main():
    if len(sys.argv) < 2:
        print("用法: python3 translate_repo.py <owner/repo>")
        print("      GITHUB_TO_HUMAN_PROVIDER=openai python3 translate_repo.py owner/repo")
        print(f"\n当前 Provider: {PROVIDER}")
        print("支持: glm / openai / deepseek")
        sys.exit(1)
    
    owner, repo = parse_input(sys.argv[1])
    if not owner or not repo:
        print("错误：请输入格式为 owner/repo 或 https://github.com/owner/repo")
        sys.exit(1)
    
    print(f"[{PROVIDER}] 正在获取 {owner}/{repo}...", file=sys.stderr)
    
    repo_info, error = get_repo_info(owner, repo)
    if error:
        print(json.dumps({"error": error}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    
    print(f"Stars: {repo_info['stars']}, Language: {repo_info['language']}", file=sys.stderr)
    
    # 并行获取 README 和相似项目
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_readme = executor.submit(get_readme, owner, repo)
        f_similar = executor.submit(get_similar_projects, owner, repo, repo_info.get("language", ""))
        
        readme = f_readme.result()
        print(f"README 获取成功 ({len(readme)} 字符)" if readme else "警告：无法获取 README", file=sys.stderr)
        
        similar = f_similar.result()
        if similar:
            print(f"找到 {len(similar)} 个相似项目，正在生成 AI 介绍...", file=sys.stderr)
            similar = enrich_similar_projects(similar, repo_info.get("description", ""))
    
    translation = translate_content(repo_info, readme)
    formatted = format_output(owner, repo, repo_info, translation, similar)
    print(formatted)

if __name__ == "__main__":
    main()