# PyCharm项目导入和启动完整指南

## 第一步：准备PyCharm环境

### 1.1 确保已安装PyCharm
- 下载并安装PyCharm Community（免费版）或Professional版
- 下载地址：https://www.jetbrains.com/pycharm/download/

### 1.2 检查Python环境
- 打开命令提示符，输入 `python --version`
- 确保Python版本为3.6或更高
- 如果没有安装Python，请从 https://www.python.org/downloads/ 下载安装

## 第二步：导入项目到PyCharm

### 2.1 打开PyCharm并导入项目
1. **启动PyCharm**
2. 选择 **"Open"** 或 **"Open Folder"**
3. 浏览到 `C:\Users\xing\Desktop\思政` 文件夹
4. 点击 **"OK"** 导入项目

### 2.2 配置Python解释器
1. 进入 **File > Settings** (Windows) 或 **PyCharm > Preferences** (Mac)
2. 选择 **Project > Python Interpreter**
3. 点击齿轮图标，选择 **"Add Interpreter"**
4. 选择 **"System Interpreter"**
5. 确保Python解释器路径正确（通常会自动检测）
6. 点击 **"OK"** 完成配置

### 2.3 项目结构确认
导入后，您的项目结构应该如下：
```
思政/ (项目根目录)
├── wangye.html
├── admin.html
├── upload_server.py      ← 主要服务器文件
├── 启动服务器.bat
├── README.md
└── (其他文件)
```

## 第三步：配置运行配置

### 3.1 创建运行配置
1. 点击PyCharm右上角的 **"Add Configuration"**
2. 点击 **"+"** 按钮，选择 **"Python"**
3. 配置如下参数：
   - **Name**: `红色思政上传服务器`
   - **Script path**: 选择 `upload_server.py`
   - **Python interpreter**: 选择配置好的解释器
   - **Working directory**: 选择项目根目录
4. 点击 **"OK"** 保存配置

### 3.2 配置模板（可选）
在 **Settings > Editor > File and Code Templates** 中，可以添加Python文件模板：
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
${NAME}
Created on ${DATE}
@author: ${USER}
"""
```

## 第四步：启动服务器

### 4.1 通过PyCharm启动（推荐）
1. 确保 `upload_server.py` 文件在编辑器中打开
2. 点击PyCharm右上角的绿色运行按钮 ▶️
3. 或者在 `upload_server.py` 文件上右键，选择 **"Run 'upload_server.py'"**

### 4.2 通过终端启动
1. 打开PyCharm内置终端：**View > Tool Windows > Terminal**
2. 输入命令：
   ```bash
   python upload_server.py
   ```

### 4.3 通过批处理文件启动
1. 在PyCharm中右键点击 `启动服务器.bat`
2. 选择 **"Run '启动服务器.bat'"**

## 第五步：验证服务器运行

### 5.1 检查控制台输出
成功启动后，您应该看到类似输出：
```
============================================================
红色思政教育网站文件上传系统 - Python版本
============================================================
服务器运行在: http://localhost:8000
主页面: http://localhost:8000/wangye.html
管理后台: http://localhost:8000/admin.html
按 Ctrl+C 停止服务器
============================================================
```

### 5.2 测试网站访问
1. 打开浏览器
2. 访问以下地址：
   - 主页面：http://localhost:8000/wangye.html
   - 管理后台：http://localhost:8000/admin.html

## 第六步：测试文件上传功能

### 6.1 上传测试文件
1. 打开 http://localhost:8000/wangye.html
2. 点击任意模块的"上传"按钮
3. 选择测试文件（如：图片、文档等）
4. 填写文件描述（可选）
5. 点击"开始上传"
6. 观察进度条和成功提示

### 6.2 验证文件管理
1. 打开 http://localhost:8000/admin.html
2. 查看上传的文件是否出现在列表中
3. 测试搜索和筛选功能
4. 尝试下载和删除文件

## 第七步：项目调试和优化

### 7.1 使用PyCharm调试功能
1. 在代码中设置断点（点击行号左侧）
2. 点击调试按钮（虫子图标）启动调试
3. 使用调试工具查看变量值和执行流程

### 7.2 代码检查
PyCharm会自动检查代码问题：
- 语法错误（红色下划线）
- 代码风格建议（黄色下划线）
- 未使用的导入等

## 常见问题解决方案

### 问题1：端口被占用
**错误信息**：`Address already in use`
**解决方案**：
1. 修改 `upload_server.py` 中的端口号（第269行）
2. 将 `server_address = ('', 8000)` 改为其他端口，如 `8001`
3. 重新启动服务器

### 问题2：Python模块缺失
**错误信息**：`ModuleNotFoundError`
**解决方案**：
1. 在PyCharm终端中安装所需模块：
   ```bash
   pip install sqlite3
   ```
2. 实际上，sqlite3是Python内置模块，通常不需要安装

### 问题3：文件权限错误
**错误信息**：`Permission denied`
**解决方案**：
1. 以管理员身份运行PyCharm
2. 或者修改项目文件夹权限

### 问题4：浏览器无法访问
**症状**：页面无法加载
**解决方案**：
1. 检查防火墙设置，允许Python访问网络
2. 确认服务器确实在运行（查看PyCharm控制台）
3. 尝试使用 http://127.0.0.1:8000 访问

## 高级配置

### 修改服务器配置
在 `upload_server.py` 中可以修改以下配置：
- **端口号**：修改第269行的 `8000`
- **上传限制**：可以添加文件大小限制
- **支持的文件类型**：修改MIME类型检查

### 数据库管理
使用PyCharm的Database工具：
1. 打开 **View > Tool Windows > Database**
2. 添加SQLite数据源，选择 `uploads.db`
3. 可以直接查看和管理数据库内容

## 项目部署建议

### 开发环境
- 使用PyCharm进行开发和调试
- 利用版本控制（Git）管理代码变更
- 定期备份数据库文件

### 生产环境
- 考虑使用更稳定的Web服务器（如Nginx + uWSGI）
- 配置域名和SSL证书
- 设置定期备份机制

## 技术支持

如果在导入或运行过程中遇到问题：
1. 检查PyCharm控制台的错误信息
2. 确认Python环境配置正确
3. 查看项目文件是否完整
4. 尝试重新启动PyCharm和系统

按照以上步骤操作，您应该能够成功在PyCharm中导入并运行完整的文件上传系统！