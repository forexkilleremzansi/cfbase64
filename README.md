# Base64 Decoder Proxy

通过Cloudflare Workers实现的Base64解码代理工具。

## 功能

访问 `https://your-domain/https://target-url` 会自动获取目标URL的内容并进行base64解码后返回。

## 使用示例

```
https://your-domain/https://prada.xiaoyao-88.com/s/8b56223b8bc3438713d131e79db02a96
```

## 部署

1. 安装依赖（如果需要）：
```bash
npm install -g wrangler
```

2. 登录Cloudflare：
```bash
wrangler login
```

3. 部署：
```bash
wrangler deploy
```

## 本地开发

```bash
wrangler dev
```
