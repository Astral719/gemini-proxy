import os
import json
import base64
import requests
from flask import Flask, request, jsonify

# 创建Flask应用
app = Flask(__name__)

# 从环境变量获取配置
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'YOUR_TOKEN')
SECRET_KEY = os.environ.get('SECRET_KEY', 'YOUR_SECRET_KEY')

# 定义生成内容的模型的API地址和请求头信息
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"

# 创建会话对象，用于发送HTTP请求并保持连接池
session = requests.Session()

def verify_token(token):
    """验证令牌的函数"""
    if not token:
        return False
    # 移除 Bearer 前缀（如果存在）
    if token.startswith('Bearer '):
        token = token[7:]
    return token == SECRET_KEY

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
                'description': 'Reverse proxy for Google Gemini Pro API',
                'version': '1.0.0',
                'endpoints': {
                    'POST /': 'Generate content using Gemini Pro',
                    'POST /api': 'Generate content using Gemini Pro'
                },
                'usage': {
                    'method': 'POST',
                    'headers': {
                        'Content-Type': 'application/json',
                        'Authorization': 'your-secret-key'
                    },
                    'body': {
                        'text': 'Your prompt here'
                    }
                }
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

        # 处理POST请求
        if request.method == 'POST':
            # 从请求头中获取令牌
            token = request.headers.get('Authorization')

            # 验证令牌
            if not verify_token(token):
                response = jsonify({'error': 'Unauthorized', 'message': 'Invalid or missing authorization token'})
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

            # 准备请求头
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
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
