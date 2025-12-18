function decodeRecursive(text) {
  let prev;
  do {
    prev = text;
    try { text = decodeURIComponent(text); } catch {}

    // Handle ss:// format specially
    text = text.replace(/(ss|vmess|trojan|vless):\/\/([A-Za-z0-9+/=]+)(@)/g, (match, protocol, base64Part, separator) => {
      try {
        const decoded = atob(base64Part);
        if (protocol === 'ss' && decoded.includes(':')) {
          // For ss://, only decode parts after first colon
          const firstColon = decoded.indexOf(':');
          const method = decoded.substring(0, firstColon);
          const rest = decoded.substring(firstColon + 1);
          // Recursively decode the rest part
          const decodedRest = rest.replace(/[A-Za-z0-9+/]{16,}={0,2}/g, (m) => {
            try {
              const d = atob(m);
              return /^[\x20-\x7E]+$/.test(d) ? d : m;
            } catch {
              return m;
            }
          });
          return protocol + '://' + method + ':' + decodedRest + separator;
        }
        return protocol + '://' + decoded + separator;
      } catch {
        return match;
      }
    });

    // Decode other base64 strings
    text = text.replace(/[A-Za-z0-9+/]{16,}={0,2}/g, (match) => {
      try {
        const decoded = atob(match);
        return /^[\x20-\x7E]+$/.test(decoded) ? decoded : match;
      } catch {
        return match;
      }
    });
  } while (prev !== text);
  return text;
}

export default {
  async fetch(request, env, ctx) {
    try {
      const url = new URL(request.url);
      const pathname = url.pathname;

      if (pathname === '/') {
        return createHomeResponse(url.host);
      }

      const ua = url.searchParams.get('ua') || 'mihomo/1.18.3';
      url.searchParams.delete('ua');

      let route, targetUrl;
      if (pathname.startsWith('/useragent/')) {
        route = 'useragent';
        targetUrl = pathname.substring(11) + (url.search || '');
      } else if (pathname.startsWith('/decoded/')) {
        route = 'decoded';
        targetUrl = pathname.substring(9) + (url.search || '');
      } else if (pathname.startsWith('/base64/')) {
        route = 'base64';
        targetUrl = pathname.substring(8) + (url.search || '');
      } else if (pathname.startsWith('/debase64/')) {
        route = 'debase64';
        targetUrl = pathname.substring(10) + (url.search || '');
      } else {
        return new Response('Invalid route', { status: 404 });
      }

      if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
        return new Response('Invalid URL', { status: 400 });
      }

      const response = await fetch(targetUrl, {
        headers: { 'User-Agent': ua }
      });
      let content = await response.text();

      if (route === 'useragent') {
        return new Response(content, {
          headers: {
            'Content-Type': 'text/plain; charset=utf-8',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }

      if (route === 'base64') {
        return new Response(btoa(content), {
          headers: {
            'Content-Type': 'text/plain; charset=utf-8',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }

      if (route === 'debase64') {
        try {
          content = atob(content.replace(/\s/g, ''));
        } catch {}
        return new Response(content, {
          headers: {
            'Content-Type': 'text/plain; charset=utf-8',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }

      if (route === 'decoded') {
        try {
          content = atob(content.replace(/\s/g, ''));
        } catch {}
        content = decodeRecursive(content);
        return new Response(content, {
          headers: {
            'Content-Type': 'text/plain; charset=utf-8',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }

    } catch (error) {
      return new Response(`Error: ${error.message}`, { status: 500 });
    }
  }
};

function createHomeResponse(domain) {
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Base64 Proxy Tool</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 15px; }
        .container { max-width: 700px; margin: 20px auto; background: white; padding: 25px; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        h1 { color: #333; text-align: center; margin-bottom: 25px; font-size: 32px; font-weight: 600; }
        h2 { color: #667eea; margin: 25px 0 12px 0; font-size: 16px; }
        .input-box { background: #f8f9ff; padding: 15px; border-radius: 10px; margin-bottom: 15px; }
        .input-box input, .input-box select, .input-box textarea { width: 100%; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; transition: border 0.3s; margin-bottom: 10px; }
        .input-box input:focus, .input-box select:focus { outline: none; border-color: #667eea; }
        #proxyLink { margin-top: 12px; padding: 12px; background: #e8f5e9; border-radius: 8px; font-family: 'Courier New', monospace; font-size: 11px; word-break: break-all; display: none; color: #2e7d32; }
        .btn-group { margin-top: 12px; display: flex; gap: 8px; }
        .btn { padding: 12px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.3s; }
        .btn-primary { background: #667eea; color: white; flex: 1; }
        .btn-primary:hover { background: #5568d3; transform: translateY(-2px); }
        .btn-success { background: #28a745; color: white; display: none; }
        .btn-success:hover { background: #218838; }
        .route { background: #fafafa; padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 3px solid #667eea; font-size: 13px; }
        .route strong { color: #333; display: block; margin-bottom: 5px; }
        .route code { background: #e8e8e8; padding: 2px 5px; border-radius: 4px; font-size: 11px; }
        .route em { color: #666; font-size: 12px; display: block; margin-top: 5px; }
        @media (max-width: 600px) {
            .container { padding: 20px; margin: 10px auto; }
            h1 { font-size: 24px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Base64 Proxy Tool</h1>

        <h2>🔗 通过URL解码</h2>
        <div class="input-box">
            <select id="routeType">
                <option value="decoded">递归解码 (decoded)</option>
                <option value="useragent">自定义UA (useragent)</option>
                <option value="debase64">解码Base64 (debase64)</option>
                <option value="base64">编码Base64 (base64)</option>
            </select>
            <input type="text" id="targetUrl" placeholder="输入目标网址，如：https://example.com/api">
            <input type="text" id="userAgent" placeholder="User-Agent (可选，默认: mihomo/1.18.3)">
            <div id="proxyLink"></div>
            <div class="btn-group">
                <button onclick="goProxy()" class="btn btn-primary">访问</button>
                <button onclick="copyProxy()" id="copyBtn" class="btn btn-success">复制链接</button>
            </div>
        </div>

        <h2>📝 直接解码文本</h2>
        <div class="input-box">
            <textarea id="inputText" placeholder="粘贴Base64编码的文本..." style="min-height: 100px; resize: vertical; font-family: monospace;"></textarea>
            <button onclick="decodeText()" class="btn btn-primary" style="max-width: 200px;">解码</button>
            <div id="decodeResult" style="display: none; margin-top: 12px; padding: 12px; background: #e3f2fd; border-radius: 8px; font-family: monospace; font-size: 11px; white-space: pre-wrap; word-break: break-all; max-height: 300px; overflow-y: auto;"></div>
        </div>

        <h2>📋 支持的路由</h2>

        <div class="route">
            <strong>递归解码：</strong> <code>/decoded/:url</code><br>
            <em>自动解码base64和URL编码，支持多层嵌套</em><br>
            <em>示例：</em> https://${domain}/decoded/https://example.com/data
        </div>

        <div class="route">
            <strong>自定义UA：</strong> <code>/useragent/:url</code><br>
            <em>使用指定User-Agent获取原始内容</em><br>
            <em>示例：</em> https://${domain}/useragent/https://example.com/api?ua=mihomo/1.18.3
        </div>

        <div class="route">
            <strong>解码Base64：</strong> <code>/debase64/:url</code><br>
            <em>只解码一次base64，不递归</em><br>
            <em>示例：</em> https://${domain}/debase64/https://example.com/base64content
        </div>

        <div class="route">
            <strong>编码Base64：</strong> <code>/base64/:url</code><br>
            <em>获取内容并编码为base64</em><br>
            <em>示例：</em> https://${domain}/base64/https://example.com/text
        </div>

        <script>
        var currentProxyUrl = '';

        function decodeText() {
            var input = document.getElementById('inputText').value.trim();
            var resultDiv = document.getElementById('decodeResult');
            if (!input) {
                alert('请输入要解码的文本');
                return;
            }
            try {
                var decoded = input;
                try {
                    decoded = atob(input.replace(/\s/g, ''));
                } catch(e) {}
                var prev;
                for (var i = 0; i < 10; i++) {
                    prev = decoded;
                    try { decoded = decodeURIComponent(decoded); } catch(e) {}
                    decoded = decoded.replace(/[A-Za-z0-9+\/]{20,}={0,2}/g, function(m) {
                        try {
                            var d = atob(m);
                            if (/^[\x20-\x7E]+$/.test(d)) return d;
                        } catch(e) {}
                        return m;
                    });
                    if (prev === decoded) break;
                }
                resultDiv.textContent = decoded;
                resultDiv.style.display = 'block';
            } catch (e) {
                resultDiv.textContent = 'Error: ' + e.message;
                resultDiv.style.display = 'block';
            }
        }

        function updateProxyLink() {
            const url = document.getElementById('targetUrl').value.trim();
            const route = document.getElementById('routeType').value;
            const ua = document.getElementById('userAgent').value.trim();
            const linkDiv = document.getElementById('proxyLink');
            const copyBtn = document.getElementById('copyBtn');

            if (!url) {
                linkDiv.style.display = 'none';
                copyBtn.style.display = 'none';
                return;
            }

            try {
                new URL(url);
                currentProxyUrl = window.location.origin + '/' + route + '/' + url;
                if (ua) {
                    currentProxyUrl += '?ua=' + encodeURIComponent(ua);
                }
                linkDiv.textContent = currentProxyUrl;
                linkDiv.style.display = 'block';
                copyBtn.style.display = 'inline-block';
            } catch (e) {
                linkDiv.style.display = 'none';
                copyBtn.style.display = 'none';
            }
        }

        function goProxy() {
            var url = document.getElementById('targetUrl').value.trim();
            if (!url) {
                alert('请输入目标网址');
                return;
            }
            if (!currentProxyUrl) {
                alert('URL格式不正确，请输入完整的URL（如：https://example.com）');
                return;
            }
            window.location.href = currentProxyUrl;
        }

        function copyProxy() {
            if (currentProxyUrl) {
                navigator.clipboard.writeText(currentProxyUrl).then(function() {
                    const btn = document.getElementById('copyBtn');
                    btn.textContent = '已复制!';
                    setTimeout(function() {
                        btn.textContent = '复制链接';
                    }, 2000);
                });
            }
        }

        document.getElementById('targetUrl').addEventListener('input', updateProxyLink);
        document.getElementById('routeType').addEventListener('change', updateProxyLink);
        document.getElementById('userAgent').addEventListener('input', updateProxyLink);
        document.getElementById('targetUrl').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') goProxy();
        });
        </script>
    </div>
</body>
</html>`;

  return new Response(html, {
    headers: {
      'Content-Type': 'text/html;charset=UTF-8',
      'Cache-Control': 'public, max-age=300'
    }
  });
}
