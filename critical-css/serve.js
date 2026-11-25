// gzip static server: node serve.js <root> <port>
const http = require('http'), fs = require('fs'), path = require('path'), zlib = require('zlib');
const [, , root, port] = process.argv;
const T = {'.html':'text/html; charset=utf-8','.css':'text/css','.js':'application/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.gif':'image/gif','.ico':'image/x-icon','.woff2':'font/woff2','.woff':'font/woff','.mp4':'video/mp4','.lottie':'application/zip','.txt':'text/plain','.xml':'application/xml'};
http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]); if (p.endsWith('/')) p += 'index.html';
  const f = path.join(root, path.normalize(p));
  fs.readFile(f, (e, buf) => {
    if (e) { res.writeHead(404); return res.end('nf'); }
    const ext = path.extname(f).toLowerCase(), type = T[ext] || 'application/octet-stream';
    const h = {'Content-Type': type, 'Cache-Control': 'max-age=600'};
    if (/text|javascript|json|svg|xml/.test(type) && /gzip/.test(req.headers['accept-encoding'] || '')) {
      h['Content-Encoding'] = 'gzip'; buf = zlib.gzipSync(buf, {level: 6}); }
    h['Content-Length'] = buf.length; res.writeHead(200, h); res.end(buf);
  });
}).listen(+port, '127.0.0.1');
