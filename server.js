const express = require('express');
const multer = require('multer');
const path = require('path');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');

const app = express();
const port = process.env.PORT || 3000;

// 中间件配置
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname)); // 提供静态文件服务
app.use('/uploads', express.static('uploads')); // 让上传的文件能通过 URL 访问

// 创建数据库连接
const db = new sqlite3.Database('./uploads.db', (err) => {
    if (err) {
        console.error('数据库连接错误:', err.message);
    } else {
        console.log('成功连接到SQLite数据库');
        initializeDatabase();
    }
});

// 初始化数据库表
function initializeDatabase() {
    const createTableSQL = `
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
    `;
    
    db.run(createTableSQL, (err) => {
        if (err) {
            console.error('创建表错误:', err.message);
        } else {
            console.log('数据表已就绪');
        }
    });
}

// 创建上传目录
const uploadsDir = './uploads';
if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
}

// 配置multer文件上传
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        // 根据模块创建子目录
        const moduleDir = path.join(uploadsDir, req.body.module || 'general');
        if (!fs.existsSync(moduleDir)) {
            fs.mkdirSync(moduleDir, { recursive: true });
        }
        cb(null, moduleDir);
    },
    filename: function (req, file, cb) {
        // 生成唯一文件名，保留扩展名
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        const ext = path.extname(file.originalname);
        cb(null, file.fieldname + '-' + uniqueSuffix + ext);
    }
});

// 文件类型过滤
const fileFilter = (req, file, cb) => {
    const allowedTypes = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'video/mp4', 'video/mpeg', 'video/quicktime',
        'text/plain', 'application/octet-stream'
    ];
    
    if (allowedTypes.includes(file.mimetype)) {
        cb(null, true);
    } else {
        cb(new Error('不支持的文件类型'), false);
    }
};

const upload = multer({ 
    storage: storage,
    fileFilter: fileFilter,
    limits: {
        fileSize: 50 * 1024 * 1024 // 50MB限制
    }
});

// API路由

// 获取上传文件列表
app.get('/api/uploads', (req, res) => {
    const { module: moduleName, sub_module: subModule } = req.query;
    let sql = 'SELECT * FROM uploads';
    let params = [];
    
    if (moduleName) {
        sql += ' WHERE module_name = ?';
        params.push(moduleName);
        if (subModule) {
            sql += ' AND sub_module = ?';
            params.push(subModule);
        }
    }
    
    sql += ' ORDER BY upload_time DESC';
    
    db.all(sql, params, (err, rows) => {
        if (err) {
            res.status(500).json({ error: err.message });
            return;
        }
        res.json(rows);
    });
});

// 文件上传接口
app.post('/api/upload', upload.single('file'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: '请选择要上传的文件' });
    }
    
    const { module, sub_module, description, uploader } = req.body;
    
    const fileData = {
        module_name: module || 'general',
        sub_module: sub_module || null,
        file_name: req.file.filename,
        original_name: req.file.originalname,
        file_size: req.file.size,
        file_type: req.file.mimetype,
        description: description || '',
        uploader: uploader || '匿名'
    };
    
    const sql = `INSERT INTO uploads (module_name, sub_module, file_name, original_name, file_size, file_type, description, uploader) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)`;
    
    db.run(sql, [
        fileData.module_name,
        fileData.sub_module,
        fileData.file_name,
        fileData.original_name,
        fileData.file_size,
        fileData.file_type,
        fileData.description,
        fileData.uploader
    ], function(err) {
        if (err) {
            res.status(500).json({ error: err.message });
            return;
        }
        
        res.json({
            success: true,
            message: '文件上传成功',
            fileId: this.lastID,
            fileData: fileData
        });
    });
});

// 文件下载接口
app.get('/api/download/:id', (req, res) => {
    const fileId = req.params.id;
    
    db.get('SELECT * FROM uploads WHERE id = ?', [fileId], (err, row) => {
        if (err) {
            res.status(500).json({ error: err.message });
            return;
        }
        
        if (!row) {
            res.status(404).json({ error: '文件不存在' });
            return;
        }
        
        const filePath = path.join(uploadsDir, row.module_name, row.file_name);
        
        if (!fs.existsSync(filePath)) {
            res.status(404).json({ error: '文件不存在' });
            return;
        }
        
        res.download(filePath, row.original_name);
    });
});

// 删除文件接口
app.delete('/api/upload/:id', (req, res) => {
    const fileId = req.params.id;
    
    db.get('SELECT * FROM uploads WHERE id = ?', [fileId], (err, row) => {
        if (err) {
            res.status(500).json({ error: err.message });
            return;
        }
        
        if (!row) {
            res.status(404).json({ error: '文件不存在' });
            return;
        }
        
        const filePath = path.join(uploadsDir, row.module_name, row.file_name);
        
        // 删除物理文件
        fs.unlink(filePath, (err) => {
            if (err && err.code !== 'ENOENT') {
                console.error('删除文件错误:', err);
            }
            
            // 删除数据库记录
            db.run('DELETE FROM uploads WHERE id = ?', [fileId], function(err) {
                if (err) {
                    res.status(500).json({ error: err.message });
                    return;
                }
                
                res.json({ success: true, message: '文件删除成功' });
            });
        });
    });
});

// 启动服务器
app.listen(port, () => {
    console.log(`服务器运行在 http://localhost:${port}`);
    console.log('文件上传系统已启动');
});

// 优雅关闭
process.on('SIGINT', () => {
    console.log('正在关闭服务器...');
    db.close((err) => {
        if (err) {
            console.error('关闭数据库错误:', err.message);
        } else {
            console.log('数据库连接已关闭');
        }
        process.exit(0);
    });
});