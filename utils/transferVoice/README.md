# 语音合成翻译应用

一个基于React + Flask的现代化语音合成翻译应用，支持多语言翻译、智能语音合成、批量处理等功能。

## 🎯 项目概述

本项目是一个完整的语音合成解决方案，提供了直观的Web界面和强大的后端API服务。用户可以轻松进行文本翻译、语音合成，并支持批量处理和多种下载选项。

### 核心特性

- 🌍 **智能翻译**：支持中英文互译，自动检测空字段并翻译
- 🎵 **多音色合成**：支持Google TTS和阿里云TTS，提供女声、男声、蛋宝、艾彤等音色
- ⚡ **批量处理**：支持JSON文件批量上传，一键生成大量语音文件
- 📦 **ZIP打包下载**：自动打包多个音频文件为ZIP，避免多次下载对话框
- 🎛️ **精细控制**：可调节语速（0.5x-2.0x），支持测试模式（仅处理前5项）
- 📱 **响应式设计**：现代化UI，适配不同设备和屏幕尺寸
- 🔧 **配置管理**：支持阿里云TTS Token配置，12小时有效期
- 📄 **多格式导出**：支持完整版和简单版JSON文件下载

## 🏗️ 项目架构

```
├── translation_voice_app/           # 主应用目录
│   ├── react_app/                  # React前端应用
│   │   ├── src/
│   │   │   ├── components/         # React组件
│   │   │   │   └── VoiceSynthesis.js    # 核心语音合成组件
│   │   │   ├── services/           # API服务层
│   │   │   │   └── api.js          # API接口封装
│   │   │   └── utils/              # 工具函数
│   │   ├── public/                 # 静态资源
│   │   └── package.json            # 前端依赖配置
│   ├── h5_api_server/              # Flask后端API
│   │   ├── app.py                  # 主API服务器
│   │   ├── services/               # 后端服务
│   │   └── temp_files/             # 临时文件存储
│   ├── services/                   # 共享服务模块
│   ├── config/                     # 配置文件
│   ├── start.py                    # 统一启动脚本
│   ├── dev.py                      # 开发者快速启动
│   ├── requirements.txt            # Python依赖
│   └── README.md                   # 应用说明文档
├── 复盘总结.md                      # 项目复盘文档
└── README.md                       # 项目主文档（本文件）
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 方式一：开发者菜单（推荐）

```bash
cd translation_voice_app
python dev.py
```

### 方式二：统一启动脚本

```bash
cd translation_voice_app

# 完整启动（前端+后端）
python start.py

# 仅启动后端API
python start.py --backend-only

# 仅启动前端
python start.py --frontend-only

# 跳过依赖检查
python start.py --skip-deps
```

### 方式三：手动启动

```bash
# 1. 启动后端API服务器
cd translation_voice_app/h5_api_server
pip install -r ../requirements.txt
python app.py

# 2. 启动React前端（新终端）
cd translation_voice_app/react_app
npm install
npm start
```

### 访问地址

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:5000
- **API健康检查**: http://localhost:5000/api/health

## 💡 功能详解

### 1. 单个语音合成

- 输入文本，选择发音人和语速
- 支持实时预览和语音生成
- 可下载生成的音频文件

### 2. 批量语音生成

#### JSON文件格式
```json
{
  "data": [
    {"chinese": "你好", "english": "Hello"},
    {"chinese": "世界", "english": "World"},
    {"chinese": "测试", "english": ""}
  ]
}
```

#### 批量处理流程
1. 上传JSON文件（拖拽或点击上传）
2. 系统自动处理数据（空英文字段自动翻译）
3. 预览处理结果
4. 一键生成所有语音文件
5. ZIP打包下载

#### 测试模式
- 开启：仅处理前5个数据项，用于快速验证
- 关闭：处理全部数据项
- 可随时切换，自动重新处理数据

### 3. 下载选项

#### ZIP批量下载
- 自动打包所有音频文件
- 避免多次下载对话框
- 支持大文件处理和错误回退

#### JSON文件下载
- **完整版**：包含所有处理信息和元数据
- **简单版**：仅包含index、chinese、english三个字段
- 文件名自动包含模式标识（test/full）和时间戳

### 4. 音色和语速

#### 支持的音色
- **女声**：Google TTS女声
- **男声**：Google TTS男声  
- **蛋宝**：Google TTS特色音色
- **艾彤**：阿里云TTS专业女声（需配置Token）

#### 语速控制
- 范围：0.5x - 2.0x
- 艾彤音色：自动转换为阿里云格式（-500~500）
- 实时预览效果

## 🔧 配置说明

### 阿里云TTS配置

1. 点击右上角"设置"按钮
2. 切换到"阿里云TTS"选项卡
3. 输入有效的Token（12小时有效期）
4. 点击"测试连接"验证
5. 保存配置

### 端口配置

可在 `translation_voice_app/config/ports.json` 中修改：
```json
{
  "frontend": 3000,
  "backend": 5000
}
```

## 🛠️ 技术实现

### 前端技术栈
- **React 18**：现代化前端框架
- **Ant Design 5**：企业级UI组件库
- **Axios**：HTTP客户端
- **状态管理**：React Hooks

### 后端技术栈
- **Flask**：轻量级Web框架
- **Google Cloud TTS**：语音合成服务
- **阿里云TTS**：专业语音合成
- **Flask-CORS**：跨域资源共享

### 核心功能实现

#### 语音合成流程
```python
# 后端API接口
@app.route('/api/synthesize', methods=['POST'])
def synthesize_voice():
    # 1. 接收文本和参数
    # 2. 选择TTS服务（Google/阿里云）
    # 3. 生成音频文件
    # 4. 返回文件信息
```

#### 批量处理逻辑
```javascript
// 前端处理流程
const processBatchData = async (jsonData) => {
  // 1. 验证JSON格式
  // 2. 根据测试模式筛选数据
  // 3. 自动翻译空字段
  // 4. 生成处理结果
};
```

#### ZIP下载实现
```python
# 后端ZIP打包
@app.route('/api/batch-download', methods=['POST'])
def batch_download():
    # 1. 接收文件名列表
    # 2. 创建ZIP压缩包
    # 3. 添加文件到ZIP
    # 4. 返回ZIP文件
```

## 📊 项目特色

### 1. 用户体验优化
- **智能提示**：根据模式动态显示状态信息
- **进度反馈**：详细的处理进度和状态提示
- **错误处理**：完善的错误提示和回退机制
- **一键操作**：批量处理、ZIP下载、数据清空

### 2. 技术架构优势
- **前后端分离**：React + Flask，职责清晰
- **API设计**：RESTful接口，易于扩展
- **状态管理**：集中化状态管理，逻辑清晰
- **错误处理**：多层错误处理和用户反馈

### 3. 性能优化
- **文件处理**：后端处理大文件，前端轻量化
- **批量操作**：智能批量处理，减少网络请求
- **缓存机制**：临时文件管理和清理
- **流式传输**：大文件分块传输

## 🚨 故障排除

### 常见问题

1. **前端启动警告**
   ```
   [DEP_WEBPACK_DEV_SERVER_ON_AFTER_SETUP_MIDDLEWARE] DeprecationWarning
   ```
   这是react-scripts版本兼容性警告，可忽略，不影响功能。

2. **阿里云TTS连接失败**
   - 检查Token是否有效（12小时有效期）
   - 确认网络连接正常
   - 重新获取Token并配置

3. **批量下载失败**
   - 系统会自动回退到逐个下载
   - 检查文件是否存在
   - 确认浏览器允许下载

4. **翻译功能异常**
   - 检查网络连接
   - 确认翻译服务可用
   - 重试操作

### 日志查看

- **后端日志**：在后端终端查看详细错误信息
- **前端日志**：在浏览器开发者工具Console查看
- **网络请求**：在浏览器Network面板查看API调用

## 📈 项目复盘

详细的项目开发复盘和经验总结请参考：[复盘总结.md](复盘总结.md)

主要包含：
- ZIP下载功能的多次失败分析
- 测试模式逻辑的反复错误原因
- 技术方案选择的经验教训
- 用户体验优化的思考过程

## 🤝 开发指南

### 代码规范
- 前端：遵循React最佳实践，使用Hooks和函数组件
- 后端：遵循Flask规范，API设计RESTful风格
- 命名：使用有意义的变量和函数名
- 注释：关键逻辑添加清晰注释

### 扩展开发
1. **新增音色**：在services中添加新的TTS服务
2. **新增语言**：扩展翻译服务支持的语言对
3. **新增功能**：遵循现有架构模式，前后端分离
4. **性能优化**：关注用户体验，优化加载和处理速度

## 📄 许可证

本项目仅供学习和开发使用。

---

**项目版本**：v2.0 - 用户体验优化版  
**最后更新**：2024年12月  
**维护状态**：积极维护 