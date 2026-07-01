#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版文件上传服务器 - 解决环境兼容性问题
"""

import os
import sys
import sqlite3
import json
import time
import random
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi

class SimpleUploadHandler(SimpleHTTPRequestHandler):
    """简化版文件上传处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        if self.path.startswith('/api/'):
            self.handle_api_request()
        else:
            # 使用父类的静态文件服务
            super().do_GET()
    
    def do_DELETE(self):
        """处理DELETE请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path.startswith('/api/delete/'):
            file_id = parsed_path.path.split('/')[-1]
            self.delete_file(file_id)
        else:
            self.send_error(404)
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/upload':
            self.handle_file_upload()
        else:
            self.send_error(404)
    
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

    def handle_api_request(self):
        """处理API请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/uploads':
            self.get_upload_list(parsed_path)
        elif parsed_path.path.startswith('/api/download/'):
            file_id = parsed_path.path.split('/')[-1]
            self.download_file(file_id)
        else:
            self.send_error(404)
    
    def get_upload_list(self, parsed_path):
        """获取上传文件列表"""
        try:
            query_params = parse_qs(parsed_path.query)
            module_name = query_params.get('module', [None])[0]
            page = int(query_params.get('page', ['1'])[0])
            page_size = int(query_params.get('page_size', ['50'])[0])
            
            conn = sqlite3.connect('uploads.db')
            cursor = conn.cursor()
            
            if module_name:
                cursor.execute(
                    'SELECT COUNT(*) FROM uploads WHERE module_name = ?', 
                    (module_name,)
                )
                total = cursor.fetchone()[0]
                offset = (page - 1) * page_size
                cursor.execute(
                    'SELECT * FROM uploads WHERE module_name = ? ORDER BY upload_time DESC LIMIT ? OFFSET ?', 
                    (module_name, page_size, offset)
                )
            else:
                cursor.execute('SELECT COUNT(*) FROM uploads')
                total = cursor.fetchone()[0]
                offset = (page - 1) * page_size
                cursor.execute(
                    'SELECT * FROM uploads ORDER BY upload_time DESC LIMIT ? OFFSET ?',
                    (page_size, offset)
                )
            
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
            
            result = {
                'files': files,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            print(f"获取文件列表错误: {e}")
            self.send_error(500, 'Internal Server Error')
    
    def handle_file_upload(self):
        """处理文件上传"""
        try:
            print("开始处理文件上传请求...")
            
            # 解析表单数据
            content_type = self.headers.get('Content-Type', '')
            print(f"Content-Type: {content_type}")
            
            # 简单的表单解析 - 修复布尔类型转换问题
            form_data = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                    'CONTENT_LENGTH': self.headers.get('Content-Length', 0)
                },
                keep_blank_values=True  # 修复布尔转换问题
            )
            
            print("表单数据解析完成")
            
            # 安全获取表单数据
            module = self.get_form_value(form_data, 'module', 'general')
            description = self.get_form_value(form_data, 'description', '')
            uploader = self.get_form_value(form_data, 'uploader', '匿名')
            
            print(f"模块: {module}, 描述: {description}, 上传者: {uploader}")
            
            # 安全获取文件
            if 'file' not in form_data:
                print("文件字段不存在")
                self.send_error(400, 'No file provided')
                return
            
            file_item = form_data['file']
            if not hasattr(file_item, 'filename'):
                print("文件字段没有filename属性")
                self.send_error(400, 'Invalid file field')
                return
            
            if not file_item.filename:
                print("文件名为空")
                self.send_error(400, 'No file provided')
                return
            
            print(f"文件名: {file_item.filename}")
            
            # 创建上传目录
            upload_dir = os.path.join('uploads', module)
            print(f"上传目录: {upload_dir}")
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成唯一文件名
            timestamp = int(time.time())
            file_ext = os.path.splitext(file_item.filename)[1] or '.bin'
            random_str = str(random.randint(100000, 999999))
            unique_filename = f'file-{timestamp}-{random_str}{file_ext}'
            file_path = os.path.join(upload_dir, unique_filename)
            print(f"文件路径: {file_path}")
            
            # 保存文件
            print("开始读取文件数据...")
            if hasattr(file_item, 'file'):
                print("使用file属性读取")
                file_data = file_item.file.read()
            else:
                print("使用value属性读取")
                file_data = file_item.value
            
            print(f"文件数据大小: {len(file_data) if file_data else 0} bytes")
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            print("文件保存完成")
            
            # 获取文件信息
            file_size = len(file_data)
            file_type = file_item.type or 'application/octet-stream'
            
            # 保存到数据库
            conn = sqlite3.connect('uploads.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO uploads 
                (module_name, sub_module, file_name, original_name, file_size, file_type, description, uploader)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (module, '', unique_filename, file_item.filename, file_size, 
                  file_type, description, uploader))
            
            file_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # 返回成功响应
            response = {
                'success': True,
                'message': '文件上传成功',
                'fileId': file_id
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            print(f"文件上传成功: {file_item.filename} -> {module}")
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            print(f"上传错误详情: {error_msg}")
            print(f"错误堆栈:\n{error_traceback}")
            # 安全发送错误信息，避免截断
            try:
                self.send_error(500, f'Upload failed: {error_msg}')
            except:
                self.send_error(500, 'Upload failed: Internal server error')
    
    def download_file(self, file_id):
        """下载文件"""
        try:
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
            
            # 设置下载头 - 修复文件名编码问题
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            
            # 安全处理文件名编码
            filename = row[4]
            try:
                # 尝试UTF-8编码
                filename_encoded = filename.encode('utf-8').decode('latin-1')
                self.send_header('Content-Disposition', f'attachment; filename="{filename_encoded}"')
            except:
                # 如果UTF-8编码失败，使用安全的ASCII文件名
                safe_filename = ''.join(c if ord(c) < 128 else '_' for c in filename)
                self.send_header('Content-Disposition', f'attachment; filename="{safe_filename}"')
            
            file_size = os.path.getsize(file_path)
            self.send_header('Content-Length', str(file_size))
            self.end_headers()
            
            # 发送文件内容
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
            
            conn.close()
            
        except Exception as e:
            print(f"下载错误: {e}")
            self.send_error(500, 'Download failed')
    
    def delete_file(self, file_id):
        """删除文件"""
        try:
            conn = sqlite3.connect('uploads.db')
            cursor = conn.cursor()
            
            # 获取文件信息
            cursor.execute('SELECT * FROM uploads WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            
            if not row:
                self.send_error(404, 'File not found')
                conn.close()
                return
            
            file_path = os.path.join('uploads', row[1], row[3])
            
            # 删除数据库记录
            cursor.execute('DELETE FROM uploads WHERE id = ?', (file_id,))
            
            # 删除物理文件
            if os.path.exists(file_path):
                os.remove(file_path)
            
            conn.commit()
            conn.close()
            
            # 返回成功响应
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                'success': True,
                'message': '文件删除成功'
            }
            
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            print(f"文件删除成功: {row[4]}")
            
        except Exception as e:
            print(f"删除错误: {e}")
            self.send_error(500, 'Delete failed')

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect('uploads.db')
    cursor = conn.cursor()
    
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
    port = 8000
    server_address = ('', port)
    
    try:
        httpd = HTTPServer(server_address, SimpleUploadHandler)
        
        print('=' * 60)
        print('简化版文件上传系统 - 启动成功')
        print('=' * 60)
        print(f'服务器运行在: http://localhost:{port}')
        print(f'主页面: http://localhost:{port}/wangye.html')
        print(f'红色资料: http://localhost:{port}/hongse.html')
        print(f'管理后台: http://localhost:{port}/admin.html')
        print('=' * 60)
        
        httpd.serve_forever()
        
    except Exception as e:
        print(f'服务器启动失败: {e}')
        print('请检查端口是否被占用或Python环境配置')

if __name__ == '__main__':
    main()