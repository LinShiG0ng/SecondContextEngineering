# Windows 系统配置说明

> 💡 本文档专门为 Windows 用户提供详细的配置指南

## 📋 配置方式（三选一）

### ✅ 方式 1：使用 .env 文件（推荐，最简单）

这是 **最简单** 的配置方式，适合 Windows 用户！

**步骤：**

1. **复制配置模板**
   ```bash
   # 在项目根目录（SecondContextEngineering文件夹）中
   # 找到 .env.example 文件
   # 右键复制 → 粘贴 → 重命名为 .env
   ```

2. **编辑 .env 文件**
   - 用**记事本**或 **VS Code** 打开 `.env` 文件
   - 找到这几行：
   ```env
   OPENAI_API_KEY=sk-your-openai-api-key-here
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-3.5-turbo
   ```

3. **填入你的 API Key**
   ```env
   # 替换成你的真实 API Key
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-3.5-turbo
   ```

4. **保存文件**
   - Ctrl+S 保存
   - **不要改变文件名**（必须是 `.env`）

5. **重启服务器**
   ```bash
   python -m context_engineering_demo.app
   ```

---

### ✅ 方式 2：使用 config.yaml 文件

**步骤：**

1. **复制配置模板**
   - 找到 `config.example.yaml` 文件
   - 复制并重命名为 `config.yaml`

2. **编辑 config.yaml**
   ```yaml
   llm:
     provider: openai
     model: gpt-3.5-turbo
     api_key: sk-proj-xxxxxxxxxxxxx  # 👈 填入你的 API Key
   ```

3. **保存并重启**
   ```bash
   python -m context_engineering_demo.app
   ```

---

### ✅ 方式 3：使用 Windows 环境变量

**步骤：**

1. **打开环境变量设置**
   - 右键 **此电脑** → **属性**
   - 点击 **高级系统设置**
   - 点击 **环境变量**

2. **添加用户变量**
   - 在"用户变量"区域点击 **新建**
   - 添加以下变量：

   | 变量名 | 变量值 |
   |-------|--------|
   | `OPENAI_API_KEY` | `sk-proj-xxxxxxxxxxxxx` |
   | `LLM_PROVIDER` | `openai` |
   | `LLM_MODEL` | `gpt-3.5-turbo` |

3. **重启命令提示符**
   - 关闭并重新打开 CMD 或 PowerShell
   - 运行程序

---

## 🔑 获取 API Key

### OpenAI（推荐，最常用）

1. 访问：https://platform.openai.com/api-keys
2. 登录或注册账号
3. 点击 **Create new secret key**
4. 复制生成的 API Key（格式：`sk-proj-xxxxx`）
5. **重要**：立即保存到安全的地方（只显示一次）

**费用参考：**
- GPT-3.5-turbo：约 $0.50 / 100万 tokens（很便宜）
- GPT-4-turbo：约 $10 / 100万 tokens

### Anthropic Claude（质量高）

1. 访问：https://console.anthropic.com/settings/keys
2. 注册并登录
3. 创建 API Key（格式：`sk-ant-xxxxx`）

**配置：**
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
```

### Ollama（完全免费，本地运行）

1. 下载：https://ollama.com/download/windows
2. 安装后打开命令提示符
3. 下载模型：
   ```bash
   ollama pull qwen2.5:7b
   ```
4. 配置：
   ```env
   LLM_PROVIDER=ollama
   LLM_MODEL=qwen2.5:7b
   LLM_BASE_URL=http://localhost:11434
   ```

**优点：** 完全免费，无限使用
**缺点：** 需要较好的电脑配置（8GB+ 内存）

---

## ✅ 验证配置

启动服务器后，你应该看到以下输出之一：

### ✅ 配置成功
```
✅ 已加载 .env 配置文件
✅ LLM客户端已初始化: openai - gpt-3.5-turbo
✨ 使用LLM驱动模式（智能分析）
```

### ❌ 未配置
```
⚠️  未配置LLM API，将使用规则匹配Fallback模式
⚠️  使用规则匹配模式（Fallback）
```

---

## 🎯 完整配置示例

### 示例 1：OpenAI GPT-3.5（推荐新手）

**.env 文件：**
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
MAX_TOKENS=8000
```

### 示例 2：OpenAI GPT-4（高质量）

**.env 文件：**
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo
MAX_TOKENS=8000
```

### 示例 3：Claude 3.5 Sonnet（最佳质量）

**.env 文件：**
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
MAX_TOKENS=8000
```

### 示例 4：Ollama 本地（免费）

**.env 文件：**
```env
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b
LLM_BASE_URL=http://localhost:11434
MAX_TOKENS=8000
```

---

## 🐛 常见问题

### ❓ Q1: 找不到 .env 文件怎么办？

**A:** Windows 默认隐藏了文件扩展名，解决方法：

1. 打开**文件资源管理器**
2. 点击顶部 **查看** 选项卡
3. 勾选 **文件扩展名**
4. 现在你可以看到 `.env.example` 了

### ❓ Q2: API Key 无效？

**A:** 检查：
- ✅ API Key 格式正确（OpenAI: `sk-proj-xxx`, Anthropic: `sk-ant-xxx`）
- ✅ 没有多余的空格或换行
- ✅ API Key 未过期
- ✅ 账号有余额（OpenAI需要充值）

### ❓ Q3: 显示 "未配置LLM API"？

**A:** 可能原因：
1. `.env` 文件名错误（应该是 `.env` 不是 `.env.txt`）
2. `.env` 文件不在项目根目录
3. API Key 前面有 `#` 注释符号（需要删除）
4. 配置后没有重启服务器

### ❓ Q4: 压缩功能不工作？

**A:** 检查启动时的输出：
- 如果看到 `✨ LLM驱动模式` → 配置成功
- 如果看到 `⚠️ 规则匹配模式` → 配置未生效

### ❓ Q5: 使用国内网络，OpenAI API 连接不上？

**A:** 使用国内镜像：
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
LLM_BASE_URL=https://api.openai-proxy.com/v1  # 示例镜像
```

或者使用 Ollama 本地模型（无需网络）。

---

## 📞 需要帮助？

1. 检查终端输出的错误信息
2. 查看 `config.example.yaml` 中的配置说明
3. 确保 API Key 正确且有余额
4. 重启服务器试试

---

## 🎉 配置成功后

启动服务器：
```bash
python -m context_engineering_demo.app
```

访问：http://localhost:8000

你现在可以：
1. ✅ 导入对话历史
2. ✅ 使用 **LLM智能压缩**（高质量摘要）
3. ✅ 导出压缩结果
4. ✅ 查看压缩统计

**压缩质量对比：**
- 规则匹配：信息保留率 ~70%，简单文本拼接
- LLM驱动：信息保留率 ~90%，连贯专业摘要 ⭐

祝使用愉快！🚀
