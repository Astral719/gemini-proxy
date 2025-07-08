# Gemini Proxy

一个用于 Google Gemini Pro API 的反向代理服务，专为解决网络访问限制而设计。**客户端提供自己的 API Key，服务器不存储任何密钥。**

🚀 **已部署到 Vercel，零配置即用！**

## ✨ 特性

- 🚀 **Serverless 部署** - 基于 Vercel 的无服务器架构，零配置部署
- � **客户端 API Key** - 用户使用自己的 Gemini API Key，费用自理
- 🛡️ **零存储策略** - 服务器不存储任何 API Key，更安全
- 🌐 **CORS 支持** - 完整的跨域资源共享支持
- 📝 **Base64 编码** - 自动对响应内容进行 Base64 编码
- ⚡ **高性能** - 使用连接池优化网络请求
- � **多种认证方式** - 支持多种 API Key 传递格式

## 🚀 快速开始

### 1. 获取 Google Gemini API Key

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建新的 API Key
3. 保存你的 API Key（稍后需要用到）

### 2. 部署到 Vercel（零配置）

#### 方法一：一键部署（推荐）

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Astral719/gemini-proxy)

#### 方法二：手动部署

1. **Fork 此仓库**
   ```bash
   # 或者克隆到本地
   git clone https://github.com/Astral719/gemini-proxy.git
   cd gemini-proxy
   ```

2. **连接到 Vercel**
   - 访问 [Vercel Dashboard](https://vercel.com/dashboard)
   - 点击 "New Project"
   - 导入你的 GitHub 仓库

3. **直接部署**
   - ✅ **无需配置任何环境变量！**
   - Vercel 会自动检测项目类型并开始部署
   - 部署完成后，你会获得一个 `.vercel.app` 域名

> 🎉 **新设计的优势**：不需要在服务器配置任何密钥，部署过程更简单！

### 3. 本地开发

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **运行服务**
   ```bash
   python api/index.py
   ```

   服务将在 `http://localhost:8000` 启动

> 💡 **提示**：本地开发也不需要配置环境变量，直接运行即可！

## 📖 API 使用说明

### 端点信息

- **GET /** - 获取 API 信息和使用说明
- **POST /** - 生成内容（主要端点）

### 请求格式

**方式一：使用 X-API-Key 头（推荐）**
```bash
curl -X POST https://your-domain.vercel.app/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 你的_Gemini_API_Key" \
  -d '{
    "text": "你好，请介绍一下人工智能的发展历史"
  }'
```

**方式二：使用 Authorization 头**
```bash
curl -X POST https://your-domain.vercel.app/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 你的_Gemini_API_Key" \
  -d '{
    "text": "你好，请介绍一下人工智能的发展历史"
  }'
```

**方式三：使用 x-goog-api-key 头（官方格式）**
```bash
curl -X POST https://your-domain.vercel.app/ \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: 你的_Gemini_API_Key" \
  -d '{
    "text": "你好，请介绍一下人工智能的发展历史"
  }'
```

### 响应格式

**成功响应：**
```json
{
  "success": true,
  "content": "base64编码的响应内容",
  "original_length": 1234
}
```

**错误响应：**
```json
{
  "error": "错误类型",
  "message": "详细错误信息"
}
```

### 解码响应内容

响应内容使用 Base64 编码，需要解码后使用：

**JavaScript:**
```javascript
const response = await fetch('https://your-domain.vercel.app/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-gemini-api-key'  // 使用你的 Gemini API Key
  },
  body: JSON.stringify({
    text: '你的问题'
  })
});

const data = await response.json();
if (data.success) {
  const decodedContent = atob(data.content);
  console.log(decodedContent);
}
```

**Python:**
```python
import base64
import requests

response = requests.post('https://your-domain.vercel.app/',
  headers={
    'Content-Type': 'application/json',
    'X-API-Key': 'your-gemini-api-key'  # 使用你的 Gemini API Key
  },
  json={
    'text': '你的问题'
  }
)

data = response.json()
if data.get('success'):
  decoded_content = base64.b64decode(data['content']).decode('utf-8')
  print(decoded_content)
```

## ⚙️ 配置说明

### 环境变量

🎉 **好消息**：新版本设计无需配置任何服务器端环境变量！

| 配置项 | 位置 | 说明 |
|--------|------|------|
| `Gemini API Key` | 客户端请求头 | 用户在每次请求时提供自己的 API Key |
| `服务器配置` | 无需配置 | 服务器不存储任何密钥信息 |

### Vercel 配置

项目包含 `vercel.json` 配置文件，定义了：
- Python 运行时环境
- 路由规则
- CORS 头设置
- 函数超时时间（30秒）

## 🔧 故障排除

### 常见问题

1. **401 Invalid API Key**
   - 检查是否在请求头中提供了 Gemini API Key
   - 确认 API Key 格式正确（不是占位符如 'YOUR_TOKEN'）
   - 支持的头格式：`X-API-Key`、`Authorization: Bearer`、`x-goog-api-key`

2. **400 Bad Request**
   - 确保请求体是有效的 JSON 格式
   - 检查是否包含必需的 `text` 字段

3. **502 External API Error**
   - 检查你的 Gemini API Key 是否有效
   - 确认 Gemini API 服务状态
   - 检查 API Key 是否有足够的配额

4. **部署失败**
   - 检查 `requirements.txt` 文件是否存在
   - ✅ 新版本无需配置环境变量，部署更简单！

### 调试技巧

- 查看 Vercel 函数日志：访问 Vercel Dashboard → 项目 → Functions 标签
- 本地测试：使用 `python api/index.py` 在本地运行服务
- API 测试：访问部署的根路径查看 API 信息

## 📄 许可证

本项目基于原始项目 [wayne0926/gemini-proxy](https://github.com/wayne0926/gemini-proxy) 进行改造，适配 Vercel 部署。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 支持

如果你在使用过程中遇到问题，可以：
- 提交 [GitHub Issue](https://github.com/Astral719/gemini-proxy/issues)
- 查看 [Vercel 文档](https://vercel.com/docs)
- 参考 [Google Gemini API 文档](https://ai.google.dev/docs)
