# Gemini Proxy

一个用于 Google Gemini Pro API 的反向代理服务，已优化用于 Vercel 部署。

## ✨ 特性

- 🚀 **Serverless 部署** - 基于 Vercel 的无服务器架构
- 🔐 **安全认证** - 支持自定义密钥验证
- 🌐 **CORS 支持** - 完整的跨域资源共享支持
- 📝 **Base64 编码** - 自动对响应内容进行 Base64 编码
- ⚡ **高性能** - 使用连接池优化网络请求
- 🛡️ **错误处理** - 完善的错误处理和日志记录

## 🚀 快速开始

### 1. 获取 Google Gemini API Key

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建新的 API Key
3. 保存你的 API Key（稍后需要用到）

### 2. 部署到 Vercel

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

3. **配置环境变量**
   在 Vercel 项目设置中添加以下环境变量：
   ```
   GEMINI_API_KEY=你的_Gemini_API_密钥
   SECRET_KEY=你的_自定义_密钥
   ```

4. **部署**
   - Vercel 会自动检测项目类型并开始部署
   - 部署完成后，你会获得一个 `.vercel.app` 域名

### 3. 本地开发

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   ```bash
   # 复制环境变量模板
   cp .env.example .env

   # 编辑 .env 文件，填入你的配置
   GEMINI_API_KEY=你的_Gemini_API_密钥
   SECRET_KEY=你的_自定义_密钥
   ```

3. **运行服务**
   ```bash
   python api/index.py
   ```

   服务将在 `http://localhost:8000` 启动

## 📖 API 使用说明

### 端点信息

- **GET /** - 获取 API 信息和使用说明
- **POST /** - 生成内容（主要端点）

### 请求格式

```bash
curl -X POST https://your-domain.vercel.app/ \
  -H "Content-Type: application/json" \
  -H "Authorization: 你的_SECRET_KEY" \
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
    'Authorization': 'your-secret-key'
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
    'Authorization': 'your-secret-key'
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

| 变量名 | 必需 | 说明 |
|--------|------|------|
| `GEMINI_API_KEY` | ✅ | Google Gemini API 密钥 |
| `SECRET_KEY` | ✅ | 用于验证请求的自定义密钥 |

### Vercel 配置

项目包含 `vercel.json` 配置文件，定义了：
- Python 运行时环境
- 路由规则
- CORS 头设置
- 函数超时时间（30秒）

## 🔧 故障排除

### 常见问题

1. **401 Unauthorized**
   - 检查 `Authorization` 头是否正确设置
   - 确认 `SECRET_KEY` 环境变量配置正确

2. **400 Bad Request**
   - 确保请求体是有效的 JSON 格式
   - 检查是否包含必需的 `text` 字段

3. **502 External API Error**
   - 检查 `GEMINI_API_KEY` 是否有效
   - 确认 Gemini API 服务状态

4. **部署失败**
   - 检查 `requirements.txt` 文件是否存在
   - 确认所有环境变量都已正确设置

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
