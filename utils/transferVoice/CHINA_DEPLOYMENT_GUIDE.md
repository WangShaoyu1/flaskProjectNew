# 🇨🇳 中国境内部署指南

针对中国境内访问优化的部署方案，确保稳定快速的访问体验。

## 🎯 推荐方案

### 方案一：阿里云 + 腾讯云（推荐）
- **前端**: 阿里云OSS + CDN
- **后端**: 阿里云ECS/函数计算
- **语音服务**: 阿里云TTS（已集成）

### 方案二：腾讯云全栈
- **前端**: 腾讯云COS + CDN
- **后端**: 腾讯云云函数/CVM
- **语音服务**: 腾讯云TTS

### 方案三：华为云
- **前端**: 华为云OBS + CDN
- **后端**: 华为云函数工作流/ECS
- **语音服务**: 华为云TTS

## 🏗️ 详细部署方案

## 方案一：阿里云部署（推荐）

### 前端部署到阿里云OSS + CDN

#### 1. 创建OSS存储桶
```bash
# 登录阿里云控制台
# 创建OSS存储桶，选择就近地域
# 开启静态网站托管
```

#### 2. 配置CDN加速
```bash
# 在CDN控制台添加域名
# 源站设置为OSS存储桶
# 配置HTTPS证书
```

#### 3. 构建和上传
```bash
cd translation_voice_app/react_app
npm run build

# 使用阿里云CLI上传
ossutil cp -r build/ oss://your-bucket-name/
```

### 后端部署到阿里云ECS

#### 1. 创建ECS实例
```bash
# 选择合适的实例规格
# 安装Python 3.9
# 配置安全组（开放5000端口）
```

#### 2. 部署应用
```bash
# 连接到ECS实例
ssh root@your-ecs-ip

# 安装依赖
yum update -y
yum install -y python3 python3-pip git

# 克隆代码
git clone your-repo-url
cd translation_voice_app

# 安装Python依赖
pip3 install -r requirements.txt

# 使用systemd管理服务
sudo tee /etc/systemd/system/voice-app.service > /dev/null <<EOF
[Unit]
Description=Voice Synthesis App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/translation_voice_app/h5_api_server
ExecStart=/usr/bin/python3 app.py
Restart=always
Environment=FLASK_ENV=production
Environment=PORT=5000

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable voice-app
sudo systemctl start voice-app
```

### 配置Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 方案二：腾讯云部署

### 前端部署到腾讯云COS

#### 1. 创建COS存储桶
```bash
# 登录腾讯云控制台
# 创建COS存储桶
# 开启静态网站功能
```

#### 2. 使用腾讯云CLI部署
```bash
# 安装腾讯云CLI
pip install coscmd

# 配置
coscmd config -a your-secret-id -s your-secret-key -b your-bucket -r your-region

# 上传文件
cd translation_voice_app/react_app
npm run build
coscmd upload -r build/ /
```

### 后端部署到腾讯云函数

#### 1. 创建云函数
```python
# 创建 main.py
import json
import sys
import os

# 添加项目路径
sys.path.append('/var/user')

from h5_api_server.app import app

def main_handler(event, context):
    # 处理API Gateway事件
    return app(event, context)
```

#### 2. 配置函数
```yaml
# serverless.yml
service: voice-synthesis-app

provider:
  name: tencent
  runtime: Python3.6
  region: ap-beijing

functions:
  api:
    handler: main.main_handler
    events:
      - apigw:
          path: /
          method: ANY
      - apigw:
          path: /{proxy+}
          method: ANY
```

## 方案三：华为云部署

### 前端部署到华为云OBS
```bash
# 创建OBS桶
# 配置静态网站托管
# 使用华为云CLI上传文件
```

### 后端部署到华为云ECS
```bash
# 类似阿里云ECS部署流程
# 使用华为云的弹性云服务器
```

## 🔧 优化配置

### 1. 修改API配置以支持国内CDN
```javascript
// 在 api.js 中添加国内CDN支持
const API_ENDPOINTS = {
  production: process.env.REACT_APP_API_BASE_URL || 'https://your-domain.com',
  development: 'http://localhost:5000'
};

const api = axios.create({
  baseURL: API_ENDPOINTS[process.env.NODE_ENV] || API_ENDPOINTS.development,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### 2. 使用国内语音服务
```python
# 在 app.py 中优先使用阿里云TTS
def get_tts_service():
    # 优先使用阿里云TTS（国内访问稳定）
    if alitts_service and alitts_service.is_available():
        return alitts_service
    # 备用Google TTS（可能需要代理）
    elif tts_service and tts_service.is_available():
        return tts_service
    else:
        raise Exception("没有可用的TTS服务")
```

## 🚀 自动化部署脚本

### 阿里云部署脚本
```bash
#!/bin/bash
# deploy-aliyun.sh

echo "🚀 开始部署到阿里云..."

# 构建前端
cd react_app
npm run build

# 上传到OSS
ossutil cp -r build/ oss://your-bucket-name/ --update

# 部署后端到ECS
ssh root@your-ecs-ip << 'EOF'
cd /root/translation_voice_app
git pull origin main
pip3 install -r requirements.txt
sudo systemctl restart voice-app
EOF

echo "✅ 部署完成！"
```

### 腾讯云部署脚本
```bash
#!/bin/bash
# deploy-tencent.sh

echo "🚀 开始部署到腾讯云..."

# 构建前端
cd react_app
npm run build

# 上传到COS
coscmd upload -r build/ /

# 部署云函数
serverless deploy

echo "✅ 部署完成！"
```

## 💰 成本对比

### 阿里云（月费用估算）
- **ECS**: ¥100-300/月
- **OSS**: ¥10-50/月
- **CDN**: ¥20-100/月
- **域名**: ¥55/年
- **SSL证书**: 免费

### 腾讯云（月费用估算）
- **云函数**: ¥50-200/月
- **COS**: ¥10-50/月
- **CDN**: ¥20-100/月
- **域名**: ¥55/年

### 华为云（月费用估算）
- **ECS**: ¥100-300/月
- **OBS**: ¥10-50/月
- **CDN**: ¥20-100/月

## 🔒 安全配置

### 1. 配置HTTPS
```bash
# 使用Let's Encrypt免费证书
certbot --nginx -d your-domain.com
```

### 2. 配置防火墙
```bash
# 只开放必要端口
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 3. 设置访问控制
```python
# 在app.py中添加IP白名单
ALLOWED_IPS = ['127.0.0.1', 'your-frontend-ip']

@app.before_request
def limit_remote_addr():
    if request.remote_addr not in ALLOWED_IPS:
        abort(403)
```

## 📊 性能优化

### 1. 启用Gzip压缩
```nginx
gzip on;
gzip_vary on;
gzip_min_length 10240;
gzip_proxied expired no-cache no-store private must-revalidate auth;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
```

### 2. 配置缓存
```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. 使用Redis缓存
```python
import redis
r = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/api/voices')
def get_voices():
    cached = r.get('voices')
    if cached:
        return cached
    
    voices = get_voice_list()
    r.setex('voices', 3600, json.dumps(voices))
    return voices
```

## 🎯 推荐方案总结

**最佳选择**: 阿里云ECS + OSS + CDN
- ✅ 国内访问速度最快
- ✅ 稳定性最好
- ✅ 已集成阿里云TTS
- ✅ 成本相对较低
- ✅ 技术支持完善

**备选方案**: 腾讯云函数 + COS + CDN
- ✅ 无服务器架构
- ✅ 按量付费
- ✅ 自动扩缩容
- ❌ 冷启动延迟

---

🎉 **选择适合您的方案开始部署吧！** 推荐从阿里云方案开始，它提供了最佳的国内访问体验。 