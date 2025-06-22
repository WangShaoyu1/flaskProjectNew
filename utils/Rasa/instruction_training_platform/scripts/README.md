# 启动停止脚本集合

本文件夹包含了智能家居指令训练平台的所有启动和停止脚本。

## 📁 文件说明

### 🚀 启动脚本

#### 1. 完整服务启动
- **`start_all_services.bat`** - Windows批处理脚本，启动所有服务
- **`start_all_services.py`** - Python脚本，启动所有服务（后端+前端+Rasa）

#### 2. Rasa服务启动
- **`start_rasa_gpu.bat`** - Windows批处理脚本，启动GPU加速版Rasa
- **`start_rasa_gpu.py`** - Python脚本，GPU优化的Rasa启动（专为RTX 3080Ti优化）
- **`start_rasa_simple.py`** - Python脚本，简化版Rasa启动（推荐使用）

### 🛑 停止脚本
- **`stop_all_services.bat`** - Windows批处理脚本，停止所有服务

## 🎯 推荐使用方式

### 快速启动（推荐）
```bash
# 方式1: 使用批处理文件（Windows）
scripts/start_all_services.bat

# 方式2: 使用Python脚本
python scripts/start_all_services.py
```

### 单独启动Rasa服务
```bash
# 简化版启动（推荐）
python scripts/start_rasa_simple.py

# GPU加速版启动
python scripts/start_rasa_gpu.py

# 或使用批处理文件
scripts/start_rasa_gpu.bat
```

### 停止所有服务
```bash
scripts/stop_all_services.bat
```

## 📋 脚本详细说明

### start_all_services.bat / start_all_services.py
**功能**: 一键启动完整的智能家居指令训练平台
**包含服务**:
- 后端API服务 (FastAPI, 端口: 8081)
- 前端界面服务 (React, 端口: 3000)
- Rasa NLU服务 (端口: 5005)

**使用场景**: 
- 首次启动系统
- 完整的开发和测试环境
- 演示和生产环境

### start_rasa_simple.py
**功能**: 启动简化版的Rasa服务
**特点**:
- 轻量级启动，启动速度快
- 自动检查必要文件
- 适合日常开发和调试

**使用场景**:
- 只需要Rasa服务时
- 快速测试NLU功能
- 开发调试阶段

### start_rasa_gpu.py
**功能**: 启动GPU加速版的Rasa服务
**特点**:
- 专为RTX 3080Ti优化
- 包含GPU环境检查
- 启用CUDA加速
- 内存优化配置

**使用场景**:
- 有GPU硬件支持时
- 需要高性能训练时
- 大规模数据处理

### stop_all_services.bat
**功能**: 停止所有相关服务
**包含操作**:
- 关闭后端API服务
- 关闭前端服务
- 关闭Rasa服务
- 清理相关进程

## 🔧 故障排除

### 常见问题

#### 1. 端口占用
```bash
# 检查端口占用
netstat -ano | findstr :5005
netstat -ano | findstr :8081
netstat -ano | findstr :3000

# 强制关闭进程
taskkill /F /PID <进程ID>
```

#### 2. Python环境问题
```bash
# 检查Python版本
python --version

# 检查关键包
python -c "import rasa; print('Rasa:', rasa.__version__)"
python -c "import tensorflow as tf; print('TensorFlow:', tf.__version__)"
```

#### 3. TensorFlow错误
```bash
# 运行修复工具
python tools/fix_tensorflow_bug.py
```

### 启动顺序建议

1. **首次启动**:
   ```bash
   # 1. 检查环境
   python -c "import rasa, tensorflow"
   
   # 2. 启动所有服务
   python scripts/start_all_services.py
   ```

2. **日常开发**:
   ```bash
   # 只启动需要的服务
   python scripts/start_rasa_simple.py
   ```

3. **停止服务**:
   ```bash
   scripts/stop_all_services.bat
   ```

## 📝 配置说明

### 环境变量
脚本会自动设置以下环境变量：
- `PYTHONUNBUFFERED=1` - 实时输出
- `RASA_TELEMETRY_ENABLED=false` - 禁用遥测
- `TF_CPP_MIN_LOG_LEVEL=2` - 减少TensorFlow日志

### 端口配置
- **后端API**: 8081
- **前端界面**: 3000  
- **Rasa服务**: 5005

### 模型文件
Rasa服务会自动加载最新的模型文件：
- `rasa/models/20250619-111126-composite-float.tar.gz`

## 🔄 更新说明

### 最近更新 (2025-01-20)
- ✅ 修复了TensorFlow 2.12.0兼容性问题
- ✅ 优化了GPU启动脚本
- ✅ 添加了环境检查功能
- ✅ 统一了脚本存放位置

### 历史版本
- 支持GPU加速启动
- 集成了前后端服务
- 添加了自动化停止脚本

## 📞 技术支持

如果遇到问题，请参考：
1. `../Rasa启动问题诊断报告.md` - 详细的问题诊断
2. `../docs/README.md` - 系统使用指南
3. `../tools/` - 各种诊断和修复工具

---

**维护者**: AI Assistant  
**创建时间**: 2025-01-20  
**最后更新**: 2025-01-20 