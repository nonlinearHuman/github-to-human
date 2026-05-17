# GitHub 说人话 🤖

> 把 GitHub 项目翻译成**普通人能直接上手的操作指南**

看不懂技术文档？不知道一个项目适不适合你？

`github-to-human` 用 AI 把冰冷的 README 和 technical specs 变成：
- ✅ 一句话说明**这东西能让你做什么**
- ✅ 3 步具体操作，**照着做就能用**
- ✅ 亮点对比，**知道为什么比别的强**
- ✅ 相似项目推荐，**有对比才有选择**

---

## 输出示例

```
📦 facebook/react
⭐ 245k+ stars
🔧 JavaScript
────────────────────────────────────────

💡 快速构建互动UI

📖 构建用户界面的JavaScript库

🎯 简化UI开发过程

⚡ 怎么用？
   1️⃣ 访问 React 官网，了解基本概念和安装方法
   2️⃣ 选择「快速开始」或「创建新项目」
   3️⃣ 按官网教程逐步学习，构建你的第一个界面

✨ 以前开发界面复杂且耗时，现在用 React 轻松实现

🔗 还有这些类似选择：
   • trekhleb/javascript-algorithms ⭐195k+
     做算法题的最佳刷题伴侣，用JavaScript轻松掌握数据结构
   • Snailclimb/JavaGuide ⭐155k+
     面试通关秘籍，Java面试题全覆盖，轻松应对后端挑战

────────────────────────────────────────
🔗 https://github.com/facebook/react
💬 安装前建议先看项目 README，实际步骤可能有差异
```

---

## 快速上手

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置你的 AI API Key

支持 4 种 Provider，用哪个都行：

```bash
# 方式1：GLM（默认，免费额度）
export GLM_API_KEY=your_key_here

# 方式2：OpenAI
export GITHUB_TO_HUMAN_PROVIDER=openai
export OPENAI_API_KEY=your_key_here

# 方式3：DeepSeek（性价比高）
export GITHUB_TO_HUMAN_PROVIDER=deepseek
export DEEPSEEK_API_KEY=your_key_here

# 方式4：MiniMax
export GITHUB_TO_HUMAN_PROVIDER=minimax
export MINIMAX_API_KEY=your_key_here
```

### 3. 运行

**翻译单个项目：**
```bash
# 方式1：owner/repo 格式
python3 scripts/translate_repo.py facebook/react

# 方式2：完整 URL
python3 scripts/translate_repo.py https://github.com/facebook/react
```

**翻译今日 Trending 热门 Top 3：**
```bash
python3 scripts/translate_trending.py
```

---

## 功能

| 功能 | 说明 |
|------|------|
| 单项目翻译 | 输入任意 GitHub 链接，输出通俗版介绍 |
| Trending 翻译 | 一键获取 GitHub 今日热门 Top 3 |
| 相似项目推荐 | 每个项目推荐 2-3 个同类选择 |
| AI 生成简介 | 相似项目也有 AI 生成的一句话说名 |
| 模型自选 | 支持 GLM / OpenAI / DeepSeek / MiniMax |

---

## 设计原则

1. **说操作，不说概念** — 每个步骤要让普通人知道"打开什么、输入什么、点击什么"
2. **说结果，不说过程** — 先告诉用户能得到什么，再说怎么操作
3. **说对比** — 用"以前XXX现在YYY"或"相当于XXX"制造认知反差
4. **禁止套话** — 不许用"这是一个..."开头

---

## 项目结构

```
github-to-human/
├── SKILL.md                      # 技能说明文档
├── README.md                     # 你正在看的这个
├── scripts/
│   ├── translate_repo.py         # 单项目翻译
│   └── translate_trending.py     # Trending 翻译
└── references/
```

---

## 适用场景

- 🔍 想快速了解一个 GitHub 项目是做什么的
- 🤔 在几个类似项目之间犹豫，想知道哪个更适合你
- 📰 想追 GitHub Trending 但不想看英文技术文档
- 🤝 想向非技术朋友介绍某个项目

---

**开源协议**：MIT  
**作者**：Alex（打造 7x24 小时全自动运转的数字公司）