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

## 通过GitHub集成部署

1. Fork本仓库到你的GitHub账号

2. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)

3. 进入 Workers & Pages

4. 点击 "Create application" → "Pages" → "Connect to Git"

5. 授权并选择你fork的仓库

6. 配置构建设置：
   - Framework preset: 选择 `None`
   - Build command: 留空
   - Build output directory: 留空

7. 点击 "Save and Deploy"

部署完成后，Cloudflare会自动为你生成一个访问地址，每次push到GitHub仓库时会自动重新部署。
