# Reddit App 创建教程

## 步骤

### 1. 登录 Reddit
打开 https://www.reddit.com 并登录你的账号

### 2. 进入 App 创建页面
访问：https://www.reddit.com/prefs/apps

点击 **「Are you a developer? Create an app...」** 蓝色按钮

### 3. 填写 App 信息

| 字段 | 填写内容 |
|------|----------|
| **name** | `github-to-human-bot`（或任意名字） |
| **App type** | 选择 `script` |
| **Description** | `Bot for promoting github-to-human project` |
| **About URL** | `https://github.com/nonlinearHuman/github-to-human` |
| **Redirect URI** | `http://localhost:8080` |

点击 **「Create app」**

### 4. 获取凭证

创建成功后，你会看到类似这样的页面：

```
# 你的凭证：
client_id:    abcdefghijklmnopqrst   ← 18位字符串，在图标下方
client_secret: xxxxxxx             ← 另一个密码（不要泄露）
```

### 5. 把凭证告诉我

把以下信息发给我：
- `client_id`（18位字符串）
- `client_secret`
- 你的 Reddit **用户名**
- 你的 Reddit **密码**

我来配置自动发帖。

---

## 示意图

```
┌─────────────────────────────────────────────────┐
│  APP NAME                                       │
│  github-to-human-bot                            │
│                                                 │
│  TYPE                                           │
│  ○ personal use   ○ web app  ● script           │
│                                                 │
│  REDIRECT URI                                   │
│  http://localhost:8080                          │
│                                                 │
│  CLIENT ID      CLIENT SECRET                   │
│  abcdef........   ••••••••••                   │
│  ↑ 看这里！                                      │
└─────────────────────────────────────────────────┘
```

---

## 注意

- `client_id` 不是密码，可以告诉我
- `client_secret` 是密码，请确认只发给我一个人
- Reddit 账号建议开启双因素认证（可选，但建议）

---

配置好后，我就可以全自动帮你发帖推广了。