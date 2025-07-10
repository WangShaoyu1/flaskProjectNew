"""
CDN配置文件
提供多个国内CDN选项，确保API文档在各种网络环境下都能正常访问
"""

# 国内CDN配置选项
CDN_CONFIGS = {
    "bytedance": {
        "name": "字节跳动CDN",
        "swagger_js": "https://lf3-cdn-tos.bytecdntp.com/cdn/expire-1-M/swagger-ui-dist/4.15.5/swagger-ui-bundle.min.js",
        "swagger_css": "https://lf3-cdn-tos.bytecdntp.com/cdn/expire-1-M/swagger-ui-dist/4.15.5/swagger-ui.min.css",
        "redoc_js": "https://lf3-cdn-tos.bytecdntp.com/cdn/expire-1-M/redoc/2.0.0/bundles/redoc.standalone.js",
        "description": "字节跳动提供的CDN服务，国内访问速度快"
    },
    "bootcdn": {
        "name": "BootCDN",
        "swagger_js": "https://cdn.bootcdn.net/ajax/libs/swagger-ui/4.15.5/swagger-ui-bundle.min.js",
        "swagger_css": "https://cdn.bootcdn.net/ajax/libs/swagger-ui/4.15.5/swagger-ui.min.css",
        "redoc_js": "https://cdn.bootcdn.net/ajax/libs/redoc/2.0.0/bundles/redoc.standalone.js",
        "description": "Bootstrap中文网提供的CDN服务"
    },
    "staticfile": {
        "name": "七牛云CDN",
        "swagger_js": "https://cdn.staticfile.org/swagger-ui/4.15.5/swagger-ui-bundle.min.js",
        "swagger_css": "https://cdn.staticfile.org/swagger-ui/4.15.5/swagger-ui.min.css",
        "redoc_js": "https://cdn.staticfile.org/redoc/2.0.0/bundles/redoc.standalone.js",
        "description": "七牛云提供的静态文件CDN服务"
    },
    "unpkg": {
        "name": "UNPKG CDN",
        "swagger_js": "https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js",
        "swagger_css": "https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css",
        "redoc_js": "https://unpkg.com/redoc@2.0.0/bundles/redoc.standalone.js",
        "description": "UNPKG提供的NPM包CDN服务，在国内有镜像"
    }
}

# 当前使用的CDN配置
CURRENT_CDN = "bytedance"

def get_current_cdn_config():
    """获取当前CDN配置"""
    return CDN_CONFIGS.get(CURRENT_CDN, CDN_CONFIGS["bytedance"])

def get_all_cdn_options():
    """获取所有可用的CDN选项"""
    return CDN_CONFIGS

def test_cdn_availability():
    """测试CDN可用性（可以在生产环境中实现）"""
    # 这里可以添加CDN可用性测试逻辑
    # 比如发送HTTP请求检查响应时间和状态
    pass

# 本地文件下载说明
LOCAL_FILES_GUIDE = """
如果CDN访问仍有问题，可以下载静态文件到本地：

1. 创建静态文件目录：
   mkdir -p backend/static/swagger-ui
   mkdir -p backend/static/redoc

2. 下载Swagger UI文件：
   wget https://github.com/swagger-api/swagger-ui/releases/download/v4.15.5/swagger-ui-dist.zip
   unzip swagger-ui-dist.zip -d backend/static/swagger-ui/

3. 下载ReDoc文件：
   wget https://github.com/Redocly/redoc/releases/download/v2.0.0/redoc.standalone.js
   mv redoc.standalone.js backend/static/redoc/

4. 修改app.py中的URL路径为本地路径：
   swagger_js_url="/static/swagger-ui/swagger-ui-bundle.js"
   swagger_css_url="/static/swagger-ui/swagger-ui.css"
   redoc_js_url="/static/redoc/redoc.standalone.js"
"""

print("CDN配置模块已加载")
print(f"当前使用CDN: {get_current_cdn_config()['name']}")
print("如需切换CDN，请修改 CURRENT_CDN 变量") 