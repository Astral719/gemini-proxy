from http.server import BaseHTTPRequestHandler
import json
import base64
import requests

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求，返回API信息"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key, x-goog-api-key')
        self.end_headers()

        response_data = {
            'name': 'Gemini Proxy API',
            'description': 'Reverse proxy for Google Gemini Pro API - Client provides API Key',
            'version': '2.0.0',
            'status': 'Working! 🎉',
            'endpoints': {
                'POST /': 'Generate content using Gemini Pro',
                'GET /': 'Get API information'
            },
            'usage': {
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'your-gemini-api-key'
                },
                'body': {
                    'text': 'Your prompt here'
                }
            },
            'features': [
                '✅ 客户端提供自己的 Gemini API Key',
                '✅ 服务器不存储任何 API Key',
                '✅ 支持多种 API Key 传递方式',
                '✅ 完整的 CORS 支持',
                '✅ Base64 编码响应'
            ]
        }

        self.wfile.write(json.dumps(response_data, ensure_ascii=False, indent=2).encode('utf-8'))

    def do_POST(self):
        """处理POST请求，转发到Gemini API"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            # 解析JSON数据
            try:
                data = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                self.send_error_response(400, f'Invalid JSON format: {str(e)}. Received data: {post_data.decode("utf-8", errors="ignore")[:100]}')
                return

            # 提取API Key
            api_key = self.extract_api_key()
            if not api_key:
                self.send_error_response(401, 'Missing or invalid API Key. Please provide API key in X-API-Key, Authorization, or x-goog-api-key header')
                return

            # 验证请求数据 - 支持多种格式
            text = ''
            model = 'gemini-1.5-flash'  # 默认模型
            original_data = None  # 保存原始数据用于直接转发

            if isinstance(data, dict):
                # 格式1: 简化格式 {"text": "消息", "model": "模型名"}
                if 'text' in data:
                    text = data.get('text', '').strip()
                    if 'model' in data:
                        model = data.get('model', '').strip() or model
                # 格式2: Gemini原始格式 {"contents": [...]}
                elif 'contents' in data:
                    # 如果是完整的Gemini格式，直接转发
                    original_data = data
                    contents = data.get('contents', [])
                    if contents and isinstance(contents, list) and len(contents) > 0:
                        parts = contents[0].get('parts', [])
                        if parts and isinstance(parts, list) and len(parts) > 0:
                            text = parts[0].get('text', '').strip()
                # 格式3: 从URL路径提取模型名 (如果客户端通过路径指定模型)
                if hasattr(self, 'path') and '/models/' in self.path:
                    # 提取路径中的模型名，如 /models/gemini-pro:generateContent
                    path_parts = self.path.split('/models/')
                    if len(path_parts) > 1:
                        model_part = path_parts[1].split(':')[0]
                        if model_part:
                            model = model_part

            if not text:
                self.send_error_response(400, f'Missing required field: text. Supported formats: {{"text": "message"}} or Gemini API format. Received: {str(data)[:200]}...')
                return

            # 验证 API Key 格式
            if not api_key or len(api_key) < 20:
                self.send_error_response(401, f'Invalid API Key format. Length: {len(api_key) if api_key else 0}')
                return

            # 调用Gemini API
            result = self.call_gemini_api(api_key, text, model, original_data)
            if result['success']:
                self.send_success_response(result['data'])
            else:
                self.send_error_response(result['status_code'], result['message'])

        except Exception as e:
            self.send_error_response(500, f'Internal server error: {str(e)}')

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key, x-goog-api-key')
        self.end_headers()

    def extract_api_key(self):
        """从请求头中提取API Key"""
        # 方式1: X-API-Key
        api_key = self.headers.get('X-API-Key')
        if api_key:
            return api_key.strip()

        # 方式2: Authorization Bearer
        auth_header = self.headers.get('Authorization')
        if auth_header:
            if auth_header.startswith('Bearer '):
                return auth_header[7:].strip()
            else:
                return auth_header.strip()

        # 方式3: x-goog-api-key
        api_key = self.headers.get('x-goog-api-key')
        if api_key:
            return api_key.strip()

        return None

    def call_gemini_api(self, api_key, text, model='gemini-1.5-flash', original_data=None):
        """调用Gemini API"""
        try:
            # 模型名称映射和验证
            model_mapping = {
                # 新模型映射到确实可用的模型
                'gemini-2.5-pro': 'gemini-1.5-pro',  # 映射到可用模型
                'gemini-2.5-flash': 'gemini-1.5-flash',  # 映射到可用模型
                'gemini-2.0-flash': 'gemini-1.5-flash',  # 映射到可用模型
                'gemini-pro': 'gemini-1.5-pro',  # 旧版本兼容
                'gemini-pro-vision': 'gemini-1.5-pro',  # 旧版本兼容
            }

            # 确实可用的模型列表
            verified_models = [
                'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-1.5-flash-8b'
            ]

            # 应用模型映射
            if model in model_mapping:
                original_model = model
                model = model_mapping[model]
                print(f"INFO: Mapping model '{original_model}' to '{model}'")

            # 如果模型仍然不在验证列表中，使用默认模型
            if model not in verified_models:
                print(f"WARNING: Model '{model}' not verified. Using gemini-1.5-flash as fallback.")
                model = 'gemini-1.5-flash'
            url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            }

            # 如果有原始数据，直接使用；否则构造标准格式
            if original_data:
                data = original_data
            else:
                data = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": text}
                            ]
                        }
                    ]
                }

            # 添加调试信息
            print(f"DEBUG: Calling Gemini API with model: {model}")
            print(f"DEBUG: URL: {url}")
            print(f"DEBUG: Data: {str(data)[:200]}...")

            response = requests.post(url, headers=headers, json=data, timeout=30)

            # 添加响应调试信息
            print(f"DEBUG: Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"DEBUG: Response text: {response.text}")
                print(f"DEBUG: Request headers: {headers}")
                print(f"DEBUG: API Key length: {len(api_key) if api_key else 'None'}")
                print(f"DEBUG: API Key starts with: {api_key[:10] if api_key else 'None'}...")

            response.raise_for_status()

            result = response.json()

            # 提取生成的内容
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                    content_text = candidate['content']['parts'][0].get('text', '')

                    # Base64编码
                    encoded_content = base64.b64encode(content_text.encode()).decode()

                    return {
                        'success': True,
                        'data': {
                            'success': True,
                            'content': encoded_content,
                            'original_length': len(content_text)
                        }
                    }

            return {
                'success': False,
                'status_code': 500,
                'message': 'No content generated by Gemini API'
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'status_code': 502,
                'message': f'Gemini API request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'status_code': 500,
                'message': f'Unexpected error: {str(e)}'
            }

    def send_success_response(self, data):
        """发送成功响应"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def send_error_response(self, status_code, message):
        """发送错误响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        error_data = {
            'error': 'API Error',
            'message': message
        }

        self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))