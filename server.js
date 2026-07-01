const express = require('express');
const multer = require('multer');
const path = require('path');
const cors = require('cors');
const fs = require('fs');

const app = express();
const port = process.env.PORT || 3000;

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));
app.use('/uploads', express.static('uploads'));

// 数据文件路径（Vercel 上复制到 /tmp 以支持读写）
const isVercel = !!process.env.VERCEL;
const DATA_PATH = isVercel ? '/tmp/uploads.json' : './uploads.json';
if (isVercel && !fs.existsSync(DATA_PATH)) {
    fs.copyFileSync('./uploads.json', DATA_PATH);
    console.log('数据文件已复制到 /tmp/');
}

// 加载数据
function loadData() {
    try {
        return JSON.parse(fs.readFileSync(DATA_PATH, 'utf-8'));
    } catch (err) {
        console.error('读取数据错误:', err.message);
        return [];
    }
}

// 保存数据
function saveData(data) {
    try {
        fs.writeFileSync(DATA_PATH, JSON.stringify(data, null, 2), 'utf-8');
    } catch (err) {
        console.error('保存数据错误:', err.message);
    }
}

// 创建上传目录
const uploadsDir = isVercel ? '/tmp/uploads' : './uploads';
if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
}

// 配置multer
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
    limits: { fileSize: 50 * 1024 * 1024 }
});

// 自动生成自增ID
function nextId(data) {
    return data.length > 0 ? Math.max(...data.map(r => r.id)) + 1 : 1;
}

// =========== API 路由 ===========

// 获取文件列表
app.get('/api/uploads', (req, res) => {
    try {
        let data = loadData();
        const { module: moduleName } = req.query;

        if (moduleName) {
            data = data.filter(r => r.module_name === moduleName);
        }

        data.sort((a, b) => (b.upload_time || '').localeCompare(a.upload_time || ''));
        res.json(data);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 文件上传
app.post('/api/upload', upload.single('file'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: '请选择要上传的文件' });
    }

    try {
        const { module, sub_module, description, uploader } = req.body;
        const data = loadData();
        const newId = nextId(data);

        const record = {
            id: newId,
            module_name: module || 'general',
            sub_module: sub_module || null,
            file_name: req.file.filename,
            original_name: req.file.originalname,
            file_size: req.file.size,
            file_type: req.file.mimetype,
            upload_time: new Date().toISOString(),
            description: description || '',
            uploader: uploader || '匿名'
        };

        data.push(record);
        saveData(data);

        res.json({
            success: true,
            message: '文件上传成功',
            fileId: newId,
            fileData: record
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 文件下载（重定向到 GitHub Raw）
app.get('/api/download/:id', (req, res) => {
    try {
        const data = loadData();
        const row = data.find(r => r.id === parseInt(req.params.id));

        if (!row) {
            return res.status(404).json({ error: '文件不存在' });
        }

        const rawUrl = `https://raw.githubusercontent.com/11wN/sizheng-project/main/uploads/${encodeURIComponent(row.module_name)}/${row.file_name}`;
        res.redirect(rawUrl);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 文件删除
app.delete('/api/upload/:id', (req, res) => {
    try {
        const data = loadData();
        const idx = data.findIndex(r => r.id === parseInt(req.params.id));

        if (idx === -1) {
            return res.status(404).json({ error: '文件不存在' });
        }

        const row = data[idx];
        const filePath = path.join(uploadsDir, row.module_name, row.file_name);

        try {
            if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
        } catch (err) {
            console.error('删除文件错误:', err);
        }

        data.splice(idx, 1);
        saveData(data);

        res.json({ success: true, message: '文件删除成功' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 健康检查
app.get('/ping', (req, res) => {
    res.json({
        status: 'ok',
        time: new Date().toISOString(),
        cwd: __dirname,
        recordCount: loadData().length,
        hasIndex: fs.existsSync('./index.html')
    });
});

// 启动服务器
app.listen(port, () => {
    console.log(`服务器运行在 http://localhost:${port}`);
    console.log('文件上传系统已启动');
});
