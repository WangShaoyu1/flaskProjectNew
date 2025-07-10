#!/bin/bash

# 中国境内部署脚本 - 阿里云版本
echo "🇨🇳 开始部署到阿里云..."

# 检查必要工具
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ 请先安装 $1"
        echo "安装命令: $2"
        exit 1
    fi
}

echo "🔍 检查必要工具..."
check_tool "node" "https://nodejs.org"
check_tool "npm" "随Node.js一起安装"
check_tool "git" "yum install git 或 apt install git"

# 检查阿里云CLI
if ! command -v ossutil &> /dev/null; then
    echo "⚠️  未检测到阿里云CLI工具"
    echo "请先安装: https://help.aliyun.com/document_detail/120075.html"
    read -p "是否继续（仅构建前端）？(y/n): " continue_without_oss
    if [[ $continue_without_oss != "y" ]]; then
        exit 1
    fi
fi

# 构建前端
echo "🏗️  构建前端应用..."
cd react_app
npm install
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 前端构建成功"
else
    echo "❌ 前端构建失败"
    exit 1
fi

# 上传到OSS（如果有CLI）
if command -v ossutil &> /dev/null; then
    echo "📤 上传到阿里云OSS..."
    read -p "请输入OSS存储桶名称: " bucket_name
    
    if [ -n "$bucket_name" ]; then
        ossutil cp -r build/ oss://$bucket_name/ --update
        echo "✅ 前端上传完成"
        echo "🌐 请在阿里云控制台配置CDN和域名"
    else
        echo "⚠️  跳过OSS上传"
    fi
else
    echo "📁 前端构建文件位置: $(pwd)/build/"
    echo "📋 手动上传步骤:"
    echo "1. 登录阿里云控制台"
    echo "2. 进入OSS服务"
    echo "3. 上传build文件夹中的所有文件"
fi

# 后端部署指导
echo ""
echo "🔧 后端部署指导:"
echo "1. 创建阿里云ECS实例"
echo "2. 配置安全组（开放80, 443, 5000端口）"
echo "3. 连接到ECS实例"
echo "4. 执行以下命令:"
echo ""
echo "   # 安装依赖"
echo "   yum update -y"
echo "   yum install -y python3 python3-pip git nginx"
echo ""
echo "   # 克隆代码"
echo "   git clone <your-repo-url>"
echo "   cd translation_voice_app"
echo ""
echo "   # 安装Python依赖"
echo "   pip3 install -r requirements.txt"
echo ""
echo "   # 创建服务文件"
echo "   sudo cp deploy-configs/voice-app.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable voice-app"
echo "   sudo systemctl start voice-app"
echo ""
echo "   # 配置Nginx"
echo "   sudo cp deploy-configs/nginx.conf /etc/nginx/conf.d/voice-app.conf"
echo "   sudo systemctl restart nginx"

# 生成配置文件
echo ""
echo "📝 生成配置文件..."
mkdir -p ../deploy-configs

# 创建systemd服务文件
cat > ../deploy-configs/voice-app.service << 'EOF'
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

# 创建Nginx配置文件
cat > ../deploy-configs/nginx.conf << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 支持大文件上传
        client_max_body_size 100M;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

echo "✅ 配置文件已生成到 deploy-configs/ 目录"

# 域名和SSL提醒
echo ""
echo "🔐 SSL证书配置:"
echo "1. 获取域名并解析到ECS公网IP"
echo "2. 安装Let's Encrypt证书:"
echo "   yum install -y certbot python3-certbot-nginx"
echo "   certbot --nginx -d your-domain.com"

echo ""
echo "🎉 部署脚本执行完成！"
echo ""
echo "📋 下一步操作:"
echo "1. 配置阿里云OSS和CDN"
echo "2. 创建ECS实例并部署后端"
echo "3. 配置域名和SSL证书"
echo "4. 测试应用功能"
echo ""
echo "💡 提示: 您的应用已集成阿里云TTS，在国内访问速度更快！" 