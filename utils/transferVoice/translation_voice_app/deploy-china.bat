@echo off
chcp 65001 > nul
echo 🇨🇳 开始部署到阿里云...

REM 检查Node.js
node --version > nul 2>&1
if errorlevel 1 (
    echo ❌ 请先安装Node.js: https://nodejs.org
    pause
    exit /b 1
)

REM 检查npm
npm --version > nul 2>&1
if errorlevel 1 (
    echo ❌ 请先安装npm（通常随Node.js一起安装）
    pause
    exit /b 1
)

REM 检查Git
git --version > nul 2>&1
if errorlevel 1 (
    echo ❌ 请先安装Git: https://git-scm.com
    pause
    exit /b 1
)

echo ✅ 基础工具检查完成

REM 检查阿里云CLI
ossutil --version > nul 2>&1
if errorlevel 1 (
    echo ⚠️  未检测到阿里云CLI工具
    echo 请先安装: https://help.aliyun.com/document_detail/120075.html
    set /p continue_without_oss=是否继续（仅构建前端）？(y/n): 
    if not "%continue_without_oss%"=="y" (
        pause
        exit /b 1
    )
)

REM 构建前端
echo 🏗️  构建前端应用...
cd react_app
call npm install
if errorlevel 1 (
    echo ❌ npm install 失败
    pause
    exit /b 1
)

call npm run build
if errorlevel 1 (
    echo ❌ 前端构建失败
    pause
    exit /b 1
)

echo ✅ 前端构建成功

REM 上传到OSS（如果有CLI）
ossutil --version > nul 2>&1
if not errorlevel 1 (
    echo 📤 上传到阿里云OSS...
    set /p bucket_name=请输入OSS存储桶名称: 
    if not "%bucket_name%"=="" (
        ossutil cp -r build/ oss://%bucket_name%/ --update
        echo ✅ 前端上传完成
        echo 🌐 请在阿里云控制台配置CDN和域名
    ) else (
        echo ⚠️  跳过OSS上传
    )
) else (
    echo 📁 前端构建文件位置: %cd%\build\
    echo 📋 手动上传步骤:
    echo 1. 登录阿里云控制台
    echo 2. 进入OSS服务
    echo 3. 上传build文件夹中的所有文件
)

REM 生成配置文件
echo.
echo 📝 生成配置文件...
cd ..
if not exist deploy-configs mkdir deploy-configs

REM 创建systemd服务文件
echo [Unit] > deploy-configs\voice-app.service
echo Description=Voice Synthesis App >> deploy-configs\voice-app.service
echo After=network.target >> deploy-configs\voice-app.service
echo. >> deploy-configs\voice-app.service
echo [Service] >> deploy-configs\voice-app.service
echo Type=simple >> deploy-configs\voice-app.service
echo User=root >> deploy-configs\voice-app.service
echo WorkingDirectory=/root/translation_voice_app/h5_api_server >> deploy-configs\voice-app.service
echo ExecStart=/usr/bin/python3 app.py >> deploy-configs\voice-app.service
echo Restart=always >> deploy-configs\voice-app.service
echo Environment=FLASK_ENV=production >> deploy-configs\voice-app.service
echo Environment=PORT=5000 >> deploy-configs\voice-app.service
echo. >> deploy-configs\voice-app.service
echo [Install] >> deploy-configs\voice-app.service
echo WantedBy=multi-user.target >> deploy-configs\voice-app.service

REM 创建Nginx配置文件
echo server { > deploy-configs\nginx.conf
echo     listen 80; >> deploy-configs\nginx.conf
echo     server_name your-domain.com; >> deploy-configs\nginx.conf
echo. >> deploy-configs\nginx.conf
echo     location / { >> deploy-configs\nginx.conf
echo         proxy_pass http://127.0.0.1:5000; >> deploy-configs\nginx.conf
echo         proxy_set_header Host $host; >> deploy-configs\nginx.conf
echo         proxy_set_header X-Real-IP $remote_addr; >> deploy-configs\nginx.conf
echo         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; >> deploy-configs\nginx.conf
echo         proxy_set_header X-Forwarded-Proto $scheme; >> deploy-configs\nginx.conf
echo. >> deploy-configs\nginx.conf
echo         # 支持大文件上传 >> deploy-configs\nginx.conf
echo         client_max_body_size 100M; >> deploy-configs\nginx.conf
echo. >> deploy-configs\nginx.conf
echo         # 超时设置 >> deploy-configs\nginx.conf
echo         proxy_connect_timeout 60s; >> deploy-configs\nginx.conf
echo         proxy_send_timeout 60s; >> deploy-configs\nginx.conf
echo         proxy_read_timeout 60s; >> deploy-configs\nginx.conf
echo     } >> deploy-configs\nginx.conf
echo. >> deploy-configs\nginx.conf
echo     # 静态文件缓存 >> deploy-configs\nginx.conf
echo     location ~* \.(js^|css^|png^|jpg^|jpeg^|gif^|ico^|svg)$ { >> deploy-configs\nginx.conf
echo         expires 1y; >> deploy-configs\nginx.conf
echo         add_header Cache-Control "public, immutable"; >> deploy-configs\nginx.conf
echo     } >> deploy-configs\nginx.conf
echo } >> deploy-configs\nginx.conf

echo ✅ 配置文件已生成到 deploy-configs\ 目录

REM 后端部署指导
echo.
echo 🔧 后端部署指导:
echo 1. 创建阿里云ECS实例
echo 2. 配置安全组（开放80, 443, 5000端口）
echo 3. 连接到ECS实例
echo 4. 执行以下命令:
echo.
echo    # 安装依赖
echo    yum update -y
echo    yum install -y python3 python3-pip git nginx
echo.
echo    # 克隆代码
echo    git clone ^<your-repo-url^>
echo    cd translation_voice_app
echo.
echo    # 安装Python依赖
echo    pip3 install -r requirements.txt
echo.
echo    # 创建服务文件
echo    sudo cp deploy-configs/voice-app.service /etc/systemd/system/
echo    sudo systemctl daemon-reload
echo    sudo systemctl enable voice-app
echo    sudo systemctl start voice-app
echo.
echo    # 配置Nginx
echo    sudo cp deploy-configs/nginx.conf /etc/nginx/conf.d/voice-app.conf
echo    sudo systemctl restart nginx

echo.
echo 🔐 SSL证书配置:
echo 1. 获取域名并解析到ECS公网IP
echo 2. 安装Let's Encrypt证书:
echo    yum install -y certbot python3-certbot-nginx
echo    certbot --nginx -d your-domain.com

echo.
echo 🎉 部署脚本执行完成！
echo.
echo 📋 下一步操作:
echo 1. 配置阿里云OSS和CDN
echo 2. 创建ECS实例并部署后端
echo 3. 配置域名和SSL证书
echo 4. 测试应用功能
echo.
echo 💡 提示: 您的应用已集成阿里云TTS，在国内访问速度更快！

pause 