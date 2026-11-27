// usage: CHUNK=14000 PAUSE=250 CSSDELAY=500 node serve_chunk.js <root> <port>
const http = require('http'), fs = require('fs'), path = require('path'), zlib = require('zlib');
const [, , root, port] = process.argv; const CH = +process.env.CHUNK || 14000, PA = +process.env.PAUSE || 300;
const T = {'.html':'text/html; charset=utf-8','.css':'text/css','.js':'application/javascript','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.gif':'image/gif','.ico':'image/x-icon','.woff2':'font/woff2','.json':'application/json'};
http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]); if (p.endsWith('/')) p += 'index.html';
  const f = path.join(root, path.normalize(p));
  fs.readFile(f, (e, buf) => {
    if (e) { res.writeHead(404); return res.end('nf'); }
    const ext = path.extname(f).toLowerCase(), type = T[ext] || 'application/octet-stream';
    if (ext === '.html') { res.writeHead(200, {'Content-Type': type, 'Cache-Control': 'no-store'}); let i = 0;
      const send = () => { res.write(buf.subarray(i, i + CH)); i += CH; if (i < buf.length) setTimeout(send, PA); else res.end(); }; return send(); }
    setTimeout(() => { res.writeHead(200, {'Content-Type': type, 'Content-Length': buf.length}); res.end(buf); }, ext === '.css' ? (+process.env.CSSDELAY || 0) : 0);
  });
}).listen(+port, '127.0.0.1');
