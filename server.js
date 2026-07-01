const express = require('express');
const multer = require('multer');
const path = require('path');
const cors = require('cors');
const Database = require('better-sqlite3');
const fs = require('fs');

const app = express();
const port = process.env.PORT || 3000;

// 中间件配置
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));
app.use('/uploads', express.static('uploads'));

// 数据库路径（Vercel 上复制到 /tmp 以支持读写）
const DB_PATH = process.env.VERCEL ? '/tmp/uploads.db' : './uploads.db';
if (process.env.VERCEL && !fs.existsSync(DB_PATH)) {
    fs.copyFileSync('./uploads.db', DB_PATH);
    console.log('数据库已复制到 /tmp/');
}

// 创建数据库连接（better-sqlite3 同步 API）
let db;
try {
    db = new Database(DB_PATH);
    console.log('成功连接到SQLite数据库');
} catch (err) {
    console.error('数据库连接错误:', err.message);
    process.exit(1);
}

// 初始化数据库表
db.exec(`
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
`);
console.log('数据表已就绪');

// 创建上传目录（Vercel 只能写 /tmp，本地用 ./uploads）
const uploadsDir = process.env.VERCEL ? '/tmp/uploads' : './uploads';
if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
}

// 配置multer文件上传
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        const moduleDir = path.join(uploadsDir, req.body.module || 'general');
        if (!fs.existsSync(moduleDir)) {
            fs.mkdirSync(moduleDir, { recursive: true });
        }
        cb(null, moduleDir);
    },
    filename: function (req, file, cb) {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        const ext = path.extname(file.originalname);
        cb(null, file.fieldname + '-' + uniqueSuffix + ext);
    }
});

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
        fileSize: 50 * 1024 * 1024
    }
});

// API路由

// 获取上传文件列表
app.get('/api/uploads', (req, res) => {
    try {
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

        const rows = db.prepare(sql).all(...params);
        res.json(rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 文件上传接口
app.post('/api/upload', upload.single('file'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: '请选择要上传的文件' });
    }

    const { module, sub_module, description, uploader } = req.body;

    try {
        const stmt = db.prepare(`INSERT INTO uploads (module_name, sub_module, file_name, original_name, file_size, file_type, description, uploader)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)`);
        const result = stmt.run(
            module || 'general',
            sub_module || null,
            req.file.filename,
            req.file.originalname,
            req.file.size,
            req.file.mimetype,
            description || '',
            uploader || '匿名'
        );

        res.json({
            success: true,
            message: '文件上传成功',
            fileId: result.lastInsertRowid,
            fileData: {
                module_name: module || 'general',
                file_name: req.file.filename,
                original_name: req.file.originalname,
                file_size: req.file.size,
                file_type: req.file.mimetype,
                description: description || '',
                uploader: uploader || '匿名'
            }
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 文件下载接口（重定向到 GitHub Raw）
app.get('/api/download/:id', (req, res) => {
    try {
        const row = db.prepare('SELECT * FROM uploads WHERE id = ?').get(req.params.id);

        if (!row) {
            return res.status(404).json({ error: '文件不存在' });
        }

        const rawUrl = `https://raw.githubusercontent.com/11wN/sizheng-project/main/uploads/${encodeURIComponent(row.module_name)}/${row.file_name}`;
        res.redirect(rawUrl);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 删除文件接口
app.delete('/api/upload/:id', (req, res) => {
    try {
        const row = db.prepare('SELECT * FROM uploads WHERE id = ?').get(req.params.id);

        if (!row) {
            return res.status(404).json({ error: '文件不存在' });
        }

        const filePath = path.join(uploadsDir, row.module_name, row.file_name);

        try {
            fs.unlinkSync(filePath);
        } catch (err) {
            if (err.code !== 'ENOENT') {
                console.error('删除文件错误:', err);
            }
        }

        db.prepare('DELETE FROM uploads WHERE id = ?').run(req.params.id);
        res.json({ success: true, message: '文件删除成功' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 健康检查端点
app.get('/ping', (req, res) => {
    const testDir = fs.readdirSync(__dirname).slice(0, 10);
    res.json({
        status: 'ok',
        time: new Date().toISOString(),
        cwd: __dirname,
        files: testDir,
        hasUploads: fs.existsSync('./uploads'),
        hasIndex: fs.existsSync('./index.html')
    });
});

// 启动服务器
app.listen(port, () => {
    console.log(`服务器运行在 http://localhost:${port}`);
    console.log('文件上传系统已启动');
});
