# 数据库文件说明

## 📂 数据库文件目录

本目录包含智能对话训练平台的数据库文件，所有SQLite数据库文件统一存放在此目录中。

## 📊 数据库文件说明

### 1. `instruction_platform_new.db` - 主数据库（v2.0.0）⭐
- **用途**: 智能对话训练平台v2.0.0的主数据库
- **状态**: 当前使用中
- **包含表**:
  - `instruction_library_master` - 指令库母版表
  - `instruction_data` - 指令数据表
  - `similar_questions` - 相似问表
  - `slot_definitions` - 词槽定义表
  - `slot_values` - 词槽值表
  - `model_training_records` - 模型训练记录表
  - `instruction_test_records` - 指令测试记录表
  - `test_details` - 测试详情表
  - `system_config` - 系统配置表
  - 以及向后兼容的旧表结构

### 2. `instruction_platform.db` - 旧版数据库
- **用途**: 平台早期版本的数据库
- **状态**: 保留备份，向后兼容
- **包含表**:
  - `intents` - 意图表
  - `utterances` - 相似问表
  - `responses` - 话术表
  - `models` - 模型表
  - `training_tasks` - 训练任务表
  - `upload_records` - 文件上传记录表
  - `batch_test_records` - 批量测试记录表

## 🔧 配置信息

### 数据库连接配置
- **新版数据库**: `backend/models/database_models.py`
- **旧版数据库**: `backend/database.py`

### 默认路径
```python
# 新版数据库路径
DATABASE_URL = "sqlite:///backend/database/instruction_platform_new.db"

# 旧版数据库路径  
DATABASE_URL = "sqlite:///backend/database/instruction_platform.db"
```

### 环境变量覆盖
可以通过设置环境变量 `DATABASE_URL` 来覆盖默认数据库路径：
```bash
export DATABASE_URL="sqlite:///path/to/your/database.db"
# 或者使用其他数据库
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
```

## 📈 数据库版本演进

### v1.0.0 - 基础版本
- 简单的意图识别和响应管理
- 基础的训练和测试功能

### v2.0.0 - 平台化版本
- 指令库母版管理
- 完整的词槽管理系统
- 双屏数据处理支持
- 智能追问逻辑
- 系统性能监控
- 完整的版本管理

## 🛠️ 维护说明

### 备份建议
1. **定期备份**: 建议每日备份主数据库文件
2. **版本控制**: 重要更新前创建数据库快照
3. **迁移记录**: 保留数据库结构变更记录

### 清理策略
1. **日志清理**: 定期清理过期的训练日志
2. **测试记录**: 清理过期的测试详情数据
3. **临时文件**: 清理上传过程中的临时数据

### 性能优化
1. **索引维护**: 定期检查和优化数据库索引
2. **空间回收**: 使用 `VACUUM` 命令回收空间
3. **查询优化**: 监控慢查询并优化

## 🔒 安全注意事项

1. **访问控制**: 确保数据库文件只有应用程序可以访问
2. **备份加密**: 备份文件建议加密存储
3. **敏感数据**: 避免在数据库中存储明文密码或敏感信息
4. **日志安全**: 确保日志文件不包含敏感信息

## 📞 故障排除

### 常见问题
1. **文件锁定**: 如果数据库被锁定，检查是否有其他进程在使用
2. **权限问题**: 确保应用程序对数据库文件有读写权限
3. **空间不足**: 定期检查磁盘空间，确保有足够空间用于数据库增长
4. **编码问题**: 确保数据库使用UTF-8编码

### 恢复步骤
1. **从备份恢复**: 使用最近的备份文件替换损坏的数据库
2. **重建索引**: 如果索引损坏，重建相关索引
3. **数据一致性检查**: 使用SQLite的 `PRAGMA integrity_check` 检查数据完整性

---

**注意**: 此目录下的数据库文件包含平台的核心数据，请谨慎操作，务必在进行任何重要操作前备份数据。 