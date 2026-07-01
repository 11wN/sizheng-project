# 红色思政教育网站文件上传系统

## 系统概述

这是一个完整的文件上传管理系统，专为红色思政教育网站设计。系统支持多种文件类型上传（图片、文档、视频等），具有模块化管理、文件分类、用户权限控制等功能。

## 功能特性

### 前端功能
- ✅ 7个主要模块的文件上传
- ✅ 支持多文件批量上传
- ✅ 实时上传进度显示
- ✅ 文件类型自动识别
- ✅ 响应式设计，支持移动端
- ✅ 美观的上传模态框界面

### 后端功能
- ✅ RESTful API 设计
- ✅ SQLite 数据库存储
- ✅ 文件分类存储（按模块）
- ✅ 文件元数据管理
- ✅ 文件下载和删除功能
- ✅ 错误处理和日志记录

### 管理后台
- ✅ 文件列表查看
- ✅ 按模块/类型筛选
- ✅ 文件搜索功能
- ✅ 统计信息展示
- ✅ 文件下载和删除

## 技术栈

- **前端**: HTML5, CSS3, JavaScript (ES6+), Font Awesome
- **后端**: Node.js, Express.js
- **数据库**: SQLite3
- **文件上传**: Multer
- **服务器**: 内置HTTP服务器

## 安装和运行

### 环境要求
- Node.js (版本 14.0 或更高)
- npm 或 yarn

### 安装步骤

1. **安装依赖包**
   ```bash
   npm install
   ```

2. **启动服务器**
   ```bash
   npm start
   ```
   或者使用开发模式（自动重启）：
   ```bash
   npm run dev
   ```

3. **访问网站**
   - 主页面: http://localhost:3000/wangye.html
   - 管理后台: http://localhost:3000/admin.html
   - API文档: http://localhost:3000/api/uploads

### 文件结构
```
思政/
├── wangye.html          # 主页面（已集成上传功能）
├── admin.html           # 管理后台
├── server.js            # 后端服务器
├── package.json         # 项目配置
├── uploads/             # 文件存储目录（自动创建）
│   ├── 时政要闻/       # 按模块分类存储
│   ├── 红色资料/
│   └── ...
├── uploads.db          # SQLite数据库（自动创建）
└── README.md           # 说明文档
```

## 使用指南

### 文件上传

1. 打开主页面 http://localhost:3000/wangye.html
2. 点击任意模块的"上传"按钮
3. 选择要上传的文件（支持多选）
4. 填写文件描述和上传者信息（可选）
5. 点击"开始上传"，观察进度条
6. 上传完成后会收到成功提示

### 支持的文件类型

| 类型 | 格式 | 最大大小 |
|------|------|----------|
| 图片 | JPG, PNG, GIF, WebP | 50MB |
| 文档 | PDF, DOC, DOCX, PPT, PPTX, TXT | 50MB |
| 视频 | MP4, MPEG, MOV, AVI | 50MB |
| 其他 | 支持常见文件类型 | 50MB |

### 管理后台使用

1. 访问 http://localhost:3000/admin.html
2. 查看文件统计信息
3. 使用筛选器按模块或类型查看文件
4. 使用搜索框查找特定文件
5. 点击"下载"按钮下载文件
6. 点击"删除"按钮删除文件（谨慎操作）

## API 接口文档

### 获取文件列表
```http
GET /api/uploads
GET /api/uploads?module=模块名称
```

### 文件上传
```http
POST /api/upload
Content-Type: multipart/form-data

参数:
- file: 文件内容（必需）
- module: 模块名称（必需）
- description: 文件描述（可选）
- uploader: 上传者名称（可选）
```

### 文件下载
```http
GET /api/download/:id
```

### 文件删除
```http
DELETE /api/upload/:id
```

## 数据库结构

### uploads 表
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| module_name | TEXT | 模块名称 |
| sub_module | TEXT | 子模块（预留） |
| file_name | TEXT | 服务器存储的文件名 |
| original_name | TEXT | 原始文件名 |
| file_size | INTEGER | 文件大小（字节） |
| file_type | TEXT | 文件MIME类型 |
| upload_time | DATETIME | 上传时间 |
| description | TEXT | 文件描述 |
| uploader | TEXT | 上传者 |

## 安全注意事项

1. **文件类型验证**: 系统会验证上传文件的MIME类型
2. **文件大小限制**: 单个文件最大50MB
3. **文件名安全**: 使用唯一文件名防止冲突
4. **路径安全**: 文件按模块分类存储，防止路径遍历攻击

## 故障排除

### 常见问题

1. **上传失败**
   - 检查文件大小是否超过50MB
   - 检查文件类型是否被支持
   - 查看浏览器控制台错误信息

2. **服务器无法启动**
   - 检查端口3000是否被占用
   - 检查Node.js版本是否符合要求
   - 检查依赖包是否安装完整

3. **数据库错误**
   - 检查uploads.db文件权限
   - 删除uploads.db文件重新启动（会丢失数据）

### 日志查看
服务器启动时会显示连接状态和错误信息，请关注控制台输出。

## 扩展开发

### 添加新模块
1. 在 `wangye.html` 中添加新的模块卡片
2. 模块名称会自动识别并创建对应目录

### 自定义文件类型
修改 `server.js` 中的 `allowedTypes` 数组来支持更多文件类型。

### 数据库备份
定期备份 `uploads.db` 文件以防止数据丢失。

## 许可证

MIT License - 可自由使用和修改

## 技术支持

如有问题请联系系统管理员或查看控制台错误信息。