import os
import json
import base64
import requests
from flask import Flask, request, jsonify

# 创建Flask应用
app = Flask(__name__)

# 定义生成内容的模型的API地址
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"

# 创建会话对象，用于发送HTTP请求并保持连接池
session = requests.Session()

def extract_api_key(request_headers):
    """从请求头中提取 Gemini API Key"""
    # 支持多种格式的 API Key 传递方式
    api_key = None

    # 方式1: X-API-Key 头（推荐）
    api_key = request_headers.get('X-API-Key')
    if api_key:
        return api_key.strip()

    # 方式2: Authorization 头（Bearer token 格式）
    auth_header = request_headers.get('Authorization')
    if auth_header:
        if auth_header.startswith('Bearer '):
            return auth_header[7:].strip()
        else:
            return auth_header.strip()

    # 方式3: x-goog-api-key 头（与 Gemini 官方格式一致）
    api_key = request_headers.get('x-goog-api-key')
    if api_key:
        return api_key.strip()

    return None

def validate_api_key(api_key):
    """验证 API Key 格式是否合理"""
    if not api_key:
        return False

    # 基本格式检查
    if len(api_key) < 10:  # API Key 通常比较长
        return False

    # 检查是否包含明显的占位符
    invalid_keys = ['YOUR_TOKEN', 'YOUR_API_KEY', 'your_api_key_here', 'test', 'demo']
    if api_key.lower() in [key.lower() for key in invalid_keys]:
        return False

    return True

def handle_cors():
    """处理CORS预检请求"""
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    return None

@app.route('/', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/api', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/api/', methods=['GET', 'POST', 'OPTIONS'])
def generate_content():
    try:
        # 处理CORS预检请求
        cors_response = handle_cors()
        if cors_response:
            return cors_response

        # 处理GET请求，返回API信息
        if request.method == 'GET':
            response = jsonify({
                'name': 'Gemini Proxy API',
                'description': 'Reverse proxy for Google Gemini Pro API - Client provides API Key',
                'version': '2.0.0',
                'endpoints': {
                    'POST /': 'Generate content using Gemini Pro',
                    'POST /api': 'Generate content using Gemini Pro'
                },
                'usage': {
                    'method': 'POST',
                    'headers': {
                        'Content-Type': 'application/json',
                        'X-API-Key': 'your-gemini-api-key'
                    },
                    'alternative_headers': {
                        'Authorization': 'Bearer your-gemini-api-key',
                        'x-goog-api-key': 'your-gemini-api-key'
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
                ],
                'security': '🔒 您的 API Key 仅用于转发请求，不会被存储或记录'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        # 处理POST请求
        if request.method == 'POST':
            # 从请求头中提取 Gemini API Key
            api_key = extract_api_key(request.headers)

            # 验证 API Key
            if not validate_api_key(api_key):
                response = jsonify({
                    'error': 'Invalid API Key',
                    'message': 'Please provide a valid Gemini API Key in headers',
                    'supported_headers': [
                        'X-API-Key: your-gemini-api-key',
                        'Authorization: Bearer your-gemini-api-key',
                        'x-goog-api-key: your-gemini-api-key'
                    ]
                })
                response.status_code = 401
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            # 从请求体中提取文本
            if not request.is_json:
                response = jsonify({'error': 'Bad Request', 'message': 'Content-Type must be application/json'})
                response.status_code = 400
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            data = request.get_json()
            text = data.get('text', '') if data else ''

            if not text:
                response = jsonify({'error': 'Bad Request', 'message': 'Missing required field: text'})
                response.status_code = 400
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

            # 准备用于POST请求的数据
            gemini_data = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": text}
                        ]
                    }
                ]
            }

            # 准备请求头，使用客户端提供的 API Key
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            }

            # 发送请求到Gemini API
            gemini_response = session.post(GEMINI_API_URL, headers=headers, json=gemini_data)
            gemini_response.raise_for_status()
            
            result = gemini_response.json()
            
            # 提取生成的内容
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                    content_text = candidate['content']['parts'][0].get('text', '')
                    
                    # 对内容进行Base64编码
                    encoded_content = base64.b64encode(content_text.encode()).decode()
                    
                    response = jsonify({
                        'success': True,
                        'content': encoded_content,
                        'original_length': len(content_text)
                    })
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
                else:
                    response = jsonify({'error': 'API Error', 'message': 'No content generated'})
                    response.status_code = 500
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
            else:
                response = jsonify({'error': 'API Error', 'message': 'No candidates returned'})
                response.status_code = 500
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response

    except requests.exceptions.RequestException as e:
        # 处理网络请求错误
        app.logger.error(f"Request error: {e}")
        response = jsonify({'error': 'External API Error', 'message': str(e)})
        response.status_code = 502
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        # 记录异常并返回错误响应
        app.logger.error(f"Error processing request: {e}")
        response = jsonify({'error': 'Internal Server Error', 'message': str(e)})
        response.status_code = 500
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

# Vercel 需要的处理函数
def handler(request):
    """Vercel serverless function handler"""
    with app.test_request_context(request.url, method=request.method, 
                                  headers=dict(request.headers), 
                                  data=request.get_data()):
        return app.full_dispatch_request()

# 如果是本地运行
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
