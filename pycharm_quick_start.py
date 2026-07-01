#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyCharm快速启动脚本 - 红色思政教育网站文件上传系统
专门为PyCharm环境优化的启动脚本
"""

import os
import sys
import subprocess
import webbrowser
import time

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("❌ Python版本过低！需要Python 3.6或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"✅ Python版本检查通过: {sys.version}")
    return True

def check_required_files():
    """检查必需文件是否存在"""
    required_files = [
        'upload_server.py',
        'wangye.html',
        'admin.html'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ 缺少必需文件:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ 所有必需文件检查通过")
    return True

def create_project_structure():
    """创建项目目录结构"""
    directories = ['uploads']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 创建目录: {directory}")
        else:
            print(f"📁 目录已存在: {directory}")

def start_server():
    """启动文件上传服务器"""
    print("\n🚀 正在启动文件上传服务器...")
    
    # 使用subprocess启动服务器
    try:
        # 在后台启动服务器
        process = subprocess.Popen([sys.executable, 'upload_server.py'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True)
        
        # 等待服务器启动
        time.sleep(3)
        
        # 检查进程是否在运行
        if process.poll() is None:
            print("✅ 服务器启动成功！")
            return process
        else:
            # 获取错误信息
            stdout, stderr = process.communicate()
            print("❌ 服务器启动失败:")
            if stderr:
                print(f"错误信息: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动服务器时出错: {e}")
        return None

def open_browser():
    """自动打开浏览器"""
    urls = [
        'http://localhost:8000/wangye.html',
        'http://localhost:8000/admin.html'
    ]
    
    print("\n🌐 正在打开浏览器...")
    
    for url in urls:
        try:
            webbrowser.open(url)
            print(f"✅ 已打开: {url}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ 无法打开 {url}: {e}")

def show_usage_instructions():
    """显示使用说明"""
    print("\n" + "="*60)
    print("📋 使用说明")
    print("="*60)
    print("1. 文件上传:")
    print("   • 打开 http://localhost:8000/wangye.html")
    print("   • 点击任意模块的'上传'按钮")
    print("   • 选择文件并填写信息")
    print("   • 点击'开始上传'")
    print("")
    print("2. 文件管理:")
    print("   • 打开 http://localhost:8000/admin.html")
    print("   • 查看、搜索、下载、删除文件")
    print("")
    print("3. 停止服务器:")
    print("   • 在PyCharm中按 Ctrl+C")
    print("   • 或在终端窗口中按 Ctrl+C")
    print("="*60)

def main():
    """主函数"""
    print("="*60)
    print("🔥 PyCharm快速启动 - 红色思政文件上传系统")
    print("="*60)
    
    # 检查环境
    if not check_python_version():
        return
    
    if not check_required_files():
        return
    
    # 创建目录结构
    create_project_structure()
    
    # 启动服务器
    server_process = start_server()
    if not server_process:
        print("\n❌ 无法启动服务器，请检查错误信息")
        return
    
    # 打开浏览器
    open_browser()
    
    # 显示使用说明
    show_usage_instructions()
    
    print("\n🎉 系统启动完成！您现在可以开始使用文件上传功能。")
    print("\n💡 提示：在PyCharm中，您可以直接运行 upload_server.py 文件")
    print("     或使用右上角的运行按钮启动服务器")
    
    try:
        # 等待用户中断
        print("\n⏳ 服务器运行中...按 Ctrl+C 停止")
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务器...")
        server_process.terminate()
        server_process.wait()
        print("✅ 服务器已停止")

if __name__ == "__main__":
    # 检查是否在PyCharm中运行
    if 'PYCHARM_HOSTED' in os.environ:
        print("🔍 检测到PyCharm环境")
    
    try:
        main()
    except Exception as e:
        print(f"\n💥 发生错误: {e}")
        print("\n🔧 建议解决方案:")
        print("1. 检查Python是否安装正确")
        print("2. 确认项目文件完整")
        print("3. 尝试手动运行: python upload_server.py")
        print("4. 查看PyCharm导入指南.md 获取详细帮助")