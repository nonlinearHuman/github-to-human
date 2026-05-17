---
name: github-to-human
description: 将 GitHub 项目翻译成普通人能看懂的内容。当用户想了解某个 GitHub 项目是做什么的、有什么用、值不值得关注时触发。也用于获取 GitHub Trending 上最热门的项目并进行通俗化翻译。触发词包括：github翻译、翻译github、github说人话、说人话、github通俗版、github通俗解释、trending翻译、今日热门翻译。
---

# GitHub 说人话 (github-to-human)

把 GitHub 项目翻译成**普通人能直接上手的操作指南**。

---

## 用户配置

使用前配置你的 AI API key（支持多种选择，用哪个都行）：

```bash
# 方式1：用 GLM（默认，免费额度）
export GLM_API_KEY=***

# 方式2：用 OpenAI
export GITHUB_TO_HUMAN_PROVIDER=openai
export OPENAI_API_KEY=***

# 方式3：用 DeepSeek（性价比高）
export GITHUB_TO_HUMAN_PROVIDER=deepseek
export DEEPSEEK_API_KEY=***

# 方式4：用 MiniMax
export GITHUB_TO_HUMAN_PROVIDER=minimax
export MINIMAX_API_KEY=***
```

**支持的 Provider**：

| Provider | 环境变量 | 模型 |
|----------|----------|------|
| GLM（默认）| GLM_API_KEY | glm-4-flash |
| OpenAI | OPENAI_API_KEY | gpt-4o-mini |
| DeepSeek | DEEPSEEK_API_KEY | deepseek-chat |

---

## 核心功能

### 功能一：翻译单个 GitHub 项目

```bash
# 设置 key 后执行
python3 ~/.openclaw/workspace/skills/github-to-human/scripts/translate_repo.py mattpocock/skills

# 支持完整 URL
python3 ~/.openclaw/workspace/skills/github-to-human/scripts/translate_repo.py https://github.com/facebook/react
```

### 功能二：翻译 Trending Top 3

```bash
python3 ~/.openclaw/workspace/skills/github-to-human/scripts/translate_trending.py
```

---

## 输出格式示例

```
📦 facebook/react
⭐ 245k+ stars
🔧 JavaScript
────────────────────────────────────────

💡 快速构建互动UI

📖 构建用户界面的JavaScript库

🎯 简化UI开发过程

⚡ 怎么用？
   1️⃣ 具体操作步骤1
   2️⃣ 具体操作步骤2
   3️⃣ 具体操作步骤3

✨ 亮点：为什么比传统方案好

🔗 还有这些类似选择：
   • owner/project ⭐10k+
     AI生成的一句话介绍（对比/场景）...
   • owner/project ⭐8k+
     AI生成的一句话介绍...

────────────────────────────────────────
🔗 https://github.com/facebook/react
💬 安装前建议先看项目 README，实际步骤可能有差异
```

**新增特性**：
- 🔗 **相似项目推荐**：自动查找 2-3 个类似项目，**每个配 AI 生成的一句话介绍**
- 📊 **信息更完整**：stars 数量、语言类型一目了然
- 💡 **结构更清晰**：tagline（营销金句）+ what_it_does（功能描述）双层输出
- 🤖 **模型自选**：支持 GLM/OpenAI/DeepSeek/MiniMax，用自己的 key

---

## 设计原则

1. **说操作，不说概念**：每个步骤要让普通人知道"打开什么、输入什么、点击什么"
2. **说结果，不说过程**：先告诉用户能得到什么，再说怎么操作
3. **说对比**：用"以前XXX现在YYY"或"相当于XXX"制造认知反差
4. **禁止套话**：不许用"这是一个..."开头