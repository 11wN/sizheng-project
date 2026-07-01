const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.send('OK - Vercel works!');
});

app.get('/ping', (req, res) => {
    res.json({ status: 'ok', time: new Date().toISOString() });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
