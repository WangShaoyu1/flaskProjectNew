# 指令训练平台部署指南

## 快速开始

### 环境要求

- Windows 10/11
- Python 3.8+
- Node.js 16+
- CUDA 11.2+ (GPU 支持)
- 8GB+ RAM
- RTX 3080 Ti 或同等级 GPU

### 安装步骤

#### 1. 克隆项目
```bash
git clone <repository-url>
cd instruction_training_platform
```

#### 2. 后端环境配置
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### 3. Rasa 环境配置
```bash
cd rasa
pip install rasa[full]==3.6.21
pip install jieba
```

#### 4. 前端环境配置
```bash
cd frontend
npm install
```

#### 5. 数据库初始化
```bash
cd backend
python -c "from database import create_tables; create_tables()"
```

### 启动服务

#### 1. 启动后端服务
```bash
cd backend
python app.py
```
访问：http://localhost:8000

#### 2. 启动 Rasa 服务
```bash
cd rasa
rasa run --enable-api --cors "*" --port 5005
```

#### 3. 启动前端服务
```bash
cd frontend
npm start
```
访问：http://localhost:3000

## 使用说明

### 1. 意图管理
- 创建意图：定义意图名称和描述
- 添加相似问：为每个意图添加训练样本
- 配置话术：设置成功、失败、兜底话术

### 2. 模型训练
- 点击"开始训练"按钮
- 监控训练进度
- 查看训练日志

### 3. 测试验证
- 单条测试：输入文本查看识别结果
- 批量测试：上传测试数据评估性能

### 4. 数据管理
- 导入训练数据（支持 CSV、JSON、YAML）
- 导出训练数据
- 数据统计和分析

## 故障排除

### 常见问题

1. **GPU 不可用**
   - 检查 CUDA 安装
   - 验证 TensorFlow GPU 支持

2. **Rasa 服务启动失败**
   - 检查端口占用
   - 验证依赖安装

3. **前端无法连接后端**
   - 检查 CORS 配置
   - 验证 API 地址

### 日志查看
```bash
# 后端日志
tail -f backend/logs/app.log

# Rasa 日志
rasa run --debug
```

## 配置说明

### 后端配置
- 数据库：SQLite（默认）
- API 端口：8000
- 日志级别：INFO

### Rasa 配置
- 语言：中文 (zh)
- 端口：5005
- GPU 加速：启用

### 前端配置
- 开发端口：3000
- API 地址：http://localhost:8000
- 构建输出：dist/

## 性能优化

### GPU 优化
```python
# 设置 GPU 内存增长
import tensorflow as tf
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    tf.config.experimental.set_memory_growth(gpus[0], True)
```

### 训练优化
- 批次大小：根据 GPU 内存调整
- 训练轮次：100（默认）
- 学习率：0.001

## 扩展开发

### 添加新意图
1. 在意图管理页面创建意图
2. 添加相似问训练样本
3. 配置响应话术
4. 重新训练模型

### 自定义动作
1. 编辑 `rasa/actions/actions.py`
2. 实现自定义动作类
3. 更新 `domain.yml`
4. 重启 Actions 服务

### API 扩展
1. 在 `backend/api/` 下添加新路由
2. 实现业务逻辑
3. 更新 API 文档
4. 前端调用新接口

## 生产部署

### 性能配置
```python
# 生产环境配置
uvicorn.run(
    "app:app",
    host="0.0.0.0",
    port=8000,
    workers=4,
    access_log=False
)
```

### 监控配置
- 日志轮转：10MB 文件大小
- 性能监控：请求耗时统计
- 错误告警：异常自动记录

### 安全配置
- CORS 策略：生产环境限制域名
- API 限流：防止恶意请求
- 数据备份：定期备份数据库

## 技术支持

### 文档资源
- [Rasa 官方文档](https://rasa.com/docs/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://reactjs.org/docs/)

### 社区支持
- Rasa 社区论坛
- GitHub Issues
- 技术交流群

---

更多详细信息请参考 `docs/技术设计方案.md`

