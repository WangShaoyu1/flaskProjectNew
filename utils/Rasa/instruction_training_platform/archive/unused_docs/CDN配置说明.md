# API文档CDN配置说明

## 📖 背景说明

FastAPI默认使用国外CDN（如cdn.jsdelivr.net）来加载Swagger UI和ReDoc的静态资源。在国内网络环境下，这些CDN经常因为网络问题导致：
- API文档页面无法正常加载
- 页面显示空白或报错
- 需要VPN才能正常访问

为了解决这个问题，我们已经配置了多个国内CDN选项。

## 🚀 已配置的国内CDN

### 1. 字节跳动CDN (当前默认)
- **服务商**: 字节跳动
- **特点**: 国内访问速度快，稳定性好
- **URL**: `lf3-cdn-tos.bytecdntp.com`

### 2. BootCDN
- **服务商**: Bootstrap中文网
- **特点**: 专注前端资源，更新及时
- **URL**: `cdn.bootcdn.net`

### 3. 七牛云CDN
- **服务商**: 七牛云
- **特点**: 企业级CDN服务，可靠性高
- **URL**: `cdn.staticfile.org`

### 4. UNPKG CDN
- **服务商**: UNPKG (国内有镜像)
- **特点**: NPM包CDN，资源丰富
- **URL**: `unpkg.com`

## 🛠️ 使用方法

### 查看当前CDN配置
```bash
cd backend
python manage_cdn.py current
```

### 测试所有CDN可用性
```bash
cd backend
python manage_cdn.py test
```

### 查看所有可用CDN
```bash
cd backend
python manage_cdn.py list
```

### 切换CDN配置
```bash
cd backend
python manage_cdn.py switch
```

## 📊 测试结果示例

运行 `python manage_cdn.py test` 后，您会看到类似输出：

```
🌐 开始测试所有CDN配置...
============================================================

🔍 测试 字节跳动CDN (bytedance)
--------------------------------------------------
✅ Swagger JS: 150.23ms
✅ Swagger CSS: 120.45ms
✅ ReDoc JS: 180.67ms
🎯 平均响应时间: 150.45ms

📊 测试结果汇总
============================================================
✅ 可用的CDN (按响应速度排序):
1. 字节跳动CDN (bytedance): 150.45ms
2. BootCDN (bootcdn): 200.12ms
3. 七牛云CDN (staticfile): 250.78ms

🚀 推荐使用: 字节跳动CDN (bytedance)
   平均响应时间: 150.45ms
```

## 🔧 手动切换CDN

如果需要手动切换，可以直接编辑 `backend/cdn_config.py` 文件：

```python
# 修改这一行
CURRENT_CDN = "bootcdn"  # 可选值: bytedance, bootcdn, staticfile, unpkg
```

然后重启后端服务：
```bash
cd backend
python app.py
```

## 📥 本地文件配置（终极解决方案）

如果所有CDN都无法访问，可以下载静态文件到本地：

### 1. 创建静态文件目录
```bash
mkdir -p backend/static/swagger-ui
mkdir -p backend/static/redoc
```

### 2. 下载Swagger UI文件
```bash
# 方法1: 直接下载
wget https://github.com/swagger-api/swagger-ui/releases/download/v4.15.5/swagger-ui-dist.zip
unzip swagger-ui-dist.zip -d backend/static/swagger-ui/

# 方法2: 使用国内镜像
wget https://ghproxy.com/https://github.com/swagger-api/swagger-ui/releases/download/v4.15.5/swagger-ui-dist.zip
```

### 3. 下载ReDoc文件
```bash
# 下载ReDoc standalone文件
wget https://github.com/Redocly/redoc/releases/download/v2.0.0/redoc.standalone.js -O backend/static/redoc/redoc.standalone.js
```

### 4. 配置静态文件服务
在 `backend/app.py` 中添加静态文件服务：

```python
from fastapi.staticfiles import StaticFiles

# 添加静态文件路由
app.mount("/static", StaticFiles(directory="static"), name="static")
```

### 5. 修改CDN配置
在 `backend/cdn_config.py` 中添加本地配置：

```python
CDN_CONFIGS["local"] = {
    "name": "本地文件",
    "swagger_js": "/static/swagger-ui/swagger-ui-bundle.js",
    "swagger_css": "/static/swagger-ui/swagger-ui.css",
    "redoc_js": "/static/redoc/redoc.standalone.js",
    "description": "使用本地静态文件，无需网络连接"
}

# 切换到本地配置
CURRENT_CDN = "local"
```

## 🔍 故障排除

### 问题1: API文档页面空白
**原因**: CDN资源加载失败
**解决方案**: 
1. 运行 `python manage_cdn.py test` 测试CDN
2. 切换到可用的CDN
3. 或使用本地文件配置

### 问题2: 文档加载缓慢
**原因**: 当前CDN响应速度慢
**解决方案**:
1. 测试所有CDN找到最快的
2. 使用 `python manage_cdn.py switch` 切换

### 问题3: 某些资源加载失败
**原因**: CDN部分资源不可用
**解决方案**:
1. 切换到其他CDN
2. 使用本地文件配置

## 📋 快速检查清单

访问API文档时，如果遇到问题，请按以下步骤检查：

- [ ] 后端服务是否正常运行 (http://localhost:8001)
- [ ] 网络连接是否正常
- [ ] 运行CDN测试: `python manage_cdn.py test`
- [ ] 检查浏览器控制台是否有错误信息
- [ ] 尝试切换CDN或使用本地文件

## 🌟 推荐配置

对于不同的使用场景：

### 开发环境
- **推荐**: 字节跳动CDN (默认)
- **备选**: BootCDN

### 生产环境
- **推荐**: 本地文件配置
- **备选**: 企业内部CDN

### 离线环境
- **推荐**: 本地文件配置
- **必需**: 预先下载所有静态资源

---

## 💡 小贴士

1. **定期测试**: 建议定期运行CDN测试，确保服务可用
2. **备份方案**: 准备多个CDN配置和本地文件作为备选
3. **网络监控**: 在生产环境中监控CDN响应时间
4. **缓存策略**: 浏览器可能缓存旧资源，必要时清除缓存

现在您的API文档应该可以在不需要VPN的情况下正常访问了！🎉 