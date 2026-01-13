const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8091;
const ROOT = process.cwd();

const MIME_TYPES = {
    ".html": "text/html", ".js": "text/javascript", ".json": "application/json",
    ".css": "text/css", ".png": "image/png", ".jpg": "image/jpeg",
    ".wav": "audio/wav", ".ogg": "audio/ogg", ".jar": "application/java-archive",
    ".wasm": "application/wasm", ".class": "application/java-vm",
    ".ship": "application/json", ".variant": "application/json",
    ".system": "application/json", ".wpn": "application/json",
    ".proj": "application/json", ".faction": "application/json",
    ".xml": "text/xml", ".properties": "text/plain", ".csv": "text/plain"
};

const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/log') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            console.log("[CLIENT-LOG]", body);
            res.writeHead(200);
            res.end();
        });
        return;
    }
    
    // Allow Cross-Origin for CDN
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Expose-Headers', '*');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('Accept-Ranges', 'bytes');
    res.setHeader('Cross-Origin-Embedder-Policy', 'credentialless');
    res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');

    let reqPath = decodeURI(req.url.split("?")[0]);
    if (reqPath === '/starsector-core' || reqPath === '/starsector-core/') reqPath = '/';
    else if (reqPath.startsWith('/starsector-core/')) reqPath = reqPath.substring(16);
    if (reqPath.startsWith('/17/conf/')) reqPath = '/jre_linux/conf/' + reqPath.substring(9);
    
    let safePath = path.normalize(reqPath);
    if (safePath === "." || safePath === "\\") safePath = "/";
    const filePath = path.join(ROOT, safePath);

    fs.stat(filePath, (err, stats) => {
        if (err || !stats) {
            console.log(`[404] ${req.url}`);
            res.writeHead(404);
            res.end('404 Not Found');
            return;
        }
        
        const ext = path.extname(filePath).toLowerCase();
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';

        if (stats.isDirectory()) {
            if (req.method === 'HEAD') {
                res.writeHead(200, { 'Content-Type': 'text/html', 'Accept-Ranges': 'bytes' });
                res.end();
                return;
            }
            fs.readdir(filePath, (err, files) => {
                if (err) { res.writeHead(500); res.end(); return; }
                const html = "<html><body>" + files.map(f => "<a href=\"" + f + "\">" + f + "</a>").join("") + "</body></html>";
                res.writeHead(200, { 
                    "Content-Type": "text/html", 
                    "Content-Length": Buffer.byteLength(html),
                    "Accept-Ranges": "bytes"
                });
                res.end(html);
            });
            return;
        }

        if (req.method === 'HEAD') {
             res.writeHead(200, {
                 'Content-Length': stats.size,
                 'Accept-Ranges': 'bytes',
                 'Content-Type': contentType
             });
             res.end();
             return;
        }

        const range = req.headers.range;
        if (range) {
            const parts = range.replace(/bytes=/, "").split("-");
            const sStr = parts[0], eStr = parts[1];
            let start, end;
            if (sStr === "") { start = stats.size - parseInt(eStr, 10); end = stats.size - 1; }
            else if (eStr === "") { start = parseInt(sStr, 10); end = stats.size - 1; }
            else { start = parseInt(sStr, 10); end = parseInt(eStr, 10); }
            
            if (start < 0) start = 0;
            if (end >= stats.size) end = stats.size - 1;
            
            if (start > end) {
                res.writeHead(416, { 'Content-Range': `bytes */${stats.size}` });
                res.end();
                return;
            }
            
            res.writeHead(206, {
                'Content-Range': `bytes ${start}-${end}/${stats.size}`,
                'Content-Length': (end - start) + 1,
                'Content-Type': contentType,
                'Accept-Ranges': 'bytes'
            });
            const stream = fs.createReadStream(filePath, { start, end });
            stream.pipe(res);
            res.on('close', () => stream.destroy());
        } else {
            res.writeHead(200, { 
                'Content-Length': stats.size, 
                'Content-Type': contentType,
                'Accept-Ranges': 'bytes' 
            });
            const stream = fs.createReadStream(filePath);
            stream.pipe(res);
            res.on('close', () => stream.destroy());
        }
        console.log(`[REQ] ${req.url} ${range ? '('+range+')' : ''}`);
    });
});

server.listen(PORT, () => {
    console.log(`--- STARSECTOR NODE.JS SERVER (Port ${PORT}) ---`);
});
