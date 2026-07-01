#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
红色思政教育网站文件上传服务器 - Python版本
"""

import os
import sqlite3
import json
import time
import random
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi
import mimetypes


class FileUploadHandler(BaseHTTPRequestHandler):
    """文件上传处理类"""
    
    def do_get(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        # 静态文件服务
        if parsed_path.path == '/' or parsed_path.path.endswith('.html'):
            self.serve_static_file(parsed_path.path)
        elif parsed_path.path == '/favicon.ico':
            # 处理favicon.ico请求，返回204 No Content
            self.send_response(204)
            self.end_headers()
            return
        
        # API接口
        elif parsed_path.path.startswith('/api/'):
            self.handle_api_request(parsed_path)
        
        else:
            self.send_error(404)
    
    def do_post(self):
        """处理POST请求（文件上传）"""
        if self.path == '/api/upload':
            self.handle_file_upload()
        else:
            self.send_error(404)
    
    def serve_static_file(self, path):
        """提供静态文件服务"""
        if path == '/':
            path = '/wangye.html'
        
        file_path = '.' + path
        
        if not os.path.exists(file_path):
            self.send_error(404)
            return
        
        # 设置MIME类型
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        self.send_response(200)
        self.send_header('Content-type', mime_type)
        self.end_headers()
        
        with open(file_path, 'rb') as f:
            self.wfile.write(f.read())
    
    # 重写父类方法以符合命名规范
    def do_GET(self):
        """处理GET请求"""
        self.do_get()
    
    def do_POST(self):
        """处理POST请求"""
        self.do_post()
    
    def get_form_value(self, form, field_name, default=''):
        """安全获取表单值，避免布尔类型转换错误"""
        try:
            # 使用正确的FieldStorage字段获取方式
            if field_name in form:
                field = form[field_name]
                # 安全获取值
                if hasattr(field, 'value'):
                    value = field.value
                    if value is None:
                        return default
                    return value if value else default
            
            return default
        except Exception:
            return default

    def handle_api_request(self, parsed_path):
        """处理API请求"""
        if parsed_path.path == '/api/uploads':
            self.get_upload_list(parsed_path)
        elif parsed_path.path.startswith('/api/download/'):
            file_id = parsed_path.path.split('/')[-1]
            self.download_file(file_id)
        else:
            self.send_error(404)
    
    def get_upload_list(self, parsed_path):
        """获取上传文件列表"""
        query_params = parse_qs(parsed_path.query)
        module_name = query_params.get('module', [None])[0]
        
        conn = sqlite3.connect('uploads.db')
        cursor = conn.cursor()
        
        # 使用参数化查询避免SQL注入
        if module_name:
            cursor.execute(
                'SELECT * FROM uploads WHERE module_name = ? ORDER BY upload_time DESC', 
                (module_name,)
            )
        else:
            cursor.execute('SELECT * FROM uploads ORDER BY upload_time DESC')
        
        files = []
        for row in cursor.fetchall():
            file_data = {
                'id': row[0],
                'module_name': row[1],
                'sub_module': row[2],
                'file_name': row[3],
                'original_name': row[4],
                'file_size': row[5],
                'file_type': row[6],
                'upload_time': row[7],
                'description': row[8],
                'uploader': row[9]
            }
            files.append(file_data)
        
        conn.close()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        self.wfile.write(json.dumps(files).encode('utf-8'))
    
    def handle_file_upload(self):
        """处理文件上传"""
        try:
            # 解析multipart/form-data
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_error(400, 'Invalid content type')
                return
            
            # 解析表单数据 - 修复布尔类型转换问题
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': content_type},
                keep_blank_values=True  # 修复布尔转换问题
            )
            
            # 安全获取表单数据
            module = self.get_form_value(form, 'module', 'general')
            description = self.get_form_value(form, 'description', '')
            uploader = self.get_form_value(form, 'uploader', '匿名')
            
            # 安全获取文件
            if 'file' not in form:
                self.send_error(400, 'No file provided')
                return
            
            file_item = form['file']
            if not hasattr(file_item, 'filename') or not file_item.filename:
                self.send_error(400, 'No file provided')
                return
            
            # 创建上传目录
            upload_dir = os.path.join('uploads', module)
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成唯一文件名
            timestamp = int(time.time())
            file_ext = os.path.splitext(file_item.filename)[1] or '.bin'
            random_str = str(random.randint(100000, 999999))
            unique_filename = f'file-{timestamp}-{random_str}{file_ext}'
            file_path = os.path.join(upload_dir, unique_filename)
            
            # 保存文件
            if hasattr(file_item, 'file'):
                file_data = file_item.file.read()
            else:
                file_data = file_item.value
                
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            file_type = file_item.type or 'application/octet-stream'
            
            # 保存到数据库
            conn = sqlite3.connect('uploads.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO uploads 
                (module_name, file_name, original_name, file_size, file_type, description, uploader)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (module, unique_filename, file_item.filename, file_size, 
                  file_type, description, uploader))
            
            file_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # 返回成功响应
            response = {
                'success': True,
                'message': '文件上传成功',
                'fileId': file_id,
                'fileData': {
                    'module_name': module,
                    'original_name': file_item.filename,
                    'file_size': file_size,
                    'file_type': file_type
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            error_msg = str(e)
            print(f"上传错误: {error_msg}")
            # 安全发送错误信息，避免截断
            try:
                self.send_error(500, f'Upload failed: {error_msg}')
            except:
                self.send_error(500, 'Upload failed: Internal server error')
    
    def download_file(self, file_id):
        """下载文件"""
        conn = sqlite3.connect('uploads.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM uploads WHERE id = ?', (file_id,))
        row = cursor.fetchone()
        
        if not row:
            self.send_error(404, 'File not found')
            conn.close()
            return
        
        file_path = os.path.join('uploads', row[1], row[3])
        
        if not os.path.exists(file_path):
            self.send_error(404, 'File not found')
            conn.close()
            return
        
        # 设置下载头
        self.send_response(200)
        
        # 根据文件类型设置Content-Type和Content-Disposition
        file_ext = os.path.splitext(row[4])[1].lower()
        if file_ext == '.pdf':
            self.send_header('Content-type', 'application/pdf')
            self.send_header('Content-Disposition', f'inline; filename="{row[4]}"')
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
            # 图片也设置为inline
            self.send_header('Content-type', 'image/' + file_ext[1:])
            self.send_header('Content-Disposition', f'inline; filename="{row[4]}"')
        elif file_ext == '.txt':
            # 文本文件也设置为inline
            self.send_header('Content-type', 'text/plain')
            self.send_header('Content-Disposition', f'inline; filename="{row[4]}"')
        else:
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{row[4]}"')
        
        file_size = os.path.getsize(file_path)
        self.send_header('Content-Length', str(file_size))
        self.end_headers()
        
        # 发送文件内容
        with open(file_path, 'rb') as f:
            self.wfile.write(f.read())
        
        conn.close()
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect('uploads.db')
    cursor = conn.cursor()
    
    # SQLite兼容的语法
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_name TEXT NOT NULL,
            sub_module TEXT,
            file_name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_type TEXT NOT NULL,
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            uploader TEXT DEFAULT '匿名'
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # 创建上传目录
    os.makedirs('uploads', exist_ok=True)

def main():
    """主函数"""
    # 初始化数据库
    init_database()
    
    # 启动服务器
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, FileUploadHandler)
    
    print('=' * 60)
    print('红色思政教育网站文件上传系统 - Python版本')
    print('=' * 60)
    print(f'服务器运行在: http://localhost:8000')
    print(f'主页面: http://localhost:8000/wangye.html')
    print(f'管理后台: http://localhost:8000/admin.html')
    print('按 Ctrl+C 停止服务器')
    print('=' * 60)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n服务器已停止')

if __name__ == '__main__':
    main()