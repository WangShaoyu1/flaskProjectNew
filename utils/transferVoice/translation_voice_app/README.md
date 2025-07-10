# 🎤 翻译语音合成应用

一个基于React + Flask的多语言翻译和语音合成应用，支持批量处理和多种语音类型。

## ✨ 主要功能

- 🌍 **多语言翻译**: 支持中英日韩等多种语言互译
- 🎵 **语音合成**: 集成Google TTS和阿里云TTS
- 📊 **批量处理**: 支持JSON文件批量导入和处理
- 📦 **批量下载**: ZIP打包下载，支持完整版和简化版JSON导出
- 🔄 **测试模式**: 可切换全量/测试模式，便于调试
- 🎛️ **多种语音**: 支持女声、男声、蛋宝、艾彤等多种发音人

## 🏗️ 技术架构

### 前端
- **React 18**: 现代化前端框架
- **Ant Design 5**: 企业级UI组件库
- **Axios**: HTTP请求库

### 后端
- **Flask**: 轻量级Web框架
- **Google Cloud TTS**: 高质量语音合成
- **阿里云TTS**: 国内语音合成服务
- **多语言翻译**: 支持多种翻译引擎

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd translation_voice_app
```

### 2. 后端设置
```bash
# 安装Python依赖
cd h5_api_server
pip install -r requirements.txt

# 配置Google Cloud凭证（可选）
# 将您的Google Cloud凭证文件放置到 config/google_credentials.json

# 启动后端服务
python app.py
```

### 3. 前端设置
```bash
# 安装Node.js依赖
cd react_app
npm install

# 启动前端开发服务器
npm start
```

### 4. 访问应用
- 前端: http://localhost:3000
- 后端API: http://localhost:5000

## 📝 使用说明

### 单个文本处理
1. 在文本框中输入要翻译的文本
2. 选择源语言和目标语言
3. 点击"翻译"按钮
4. 选择语音类型和语速
5. 点击"生成语音"或"预览"

### 批量处理
1. 点击"批量上传"按钮
2. 选择JSON文件（格式：`[{"index": 1, "chinese": "文本"}]`）
3. 选择处理模式（全部/测试）
4. 点击"开始处理"
5. 处理完成后可批量下载或导出JSON

### 语音设置
- **阿里云TTS**: 在设置中配置Token
- **Google TTS**: 配置凭证文件

## 🔧 配置说明

### 环境变量
- `FLASK_ENV`: Flask环境（development/production）
- `PORT`: 服务端口（默认5000）

### 配置文件
- `config/settings.py`: 主配置文件
- `config/google_credentials.json`: Google Cloud凭证
- `config/user_settings.json`: 用户设置

## 📦 项目结构

```
translation_voice_app/
├── react_app/              # React前端应用
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── services/       # API服务
│   │   └── App.js          # 主应用组件
│   └── package.json
├── h5_api_server/          # Flask后端API
│   ├── app.py              # 主应用文件
│   ├── temp_files/         # 临时文件存储
│   └── requirements.txt    # Python依赖
├── services/               # 后端服务模块
│   ├── tts_service.py      # Google TTS服务
│   ├── alitts_service.py   # 阿里云TTS服务
│   ├── translator.py       # 翻译服务
│   └── ...
├── config/                 # 配置文件
│   ├── settings.py         # 主配置
│   ├── languages.json      # 语言配置
│   └── ...
└── README.md
```

## 🌐 部署说明

### 本地开发
推荐使用本地开发环境，已经完全满足业务需求。

### 云端部署
如需部署到云端，推荐使用阿里云方案以获得最佳的国内访问体验：

```bash
# 使用阿里云部署脚本
chmod +x deploy-china.sh
./deploy-china.sh
```

详细部署说明请参考：
- `CHINA_DEPLOYMENT_GUIDE.md` - 中国境内部署指南
- `DEPLOYMENT_COMPARISON.md` - 部署方案对比

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- Google Cloud Text-to-Speech API
- 阿里云语音合成服务
- React & Ant Design 社区
- Flask 框架

---

⭐ 如果这个项目对您有帮助，请给它一个星标！ 