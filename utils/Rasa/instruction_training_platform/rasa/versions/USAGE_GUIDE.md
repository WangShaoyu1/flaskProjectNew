# Rasa配置文件版本管理系统使用指南

## 快速开始

### 1. 创建新版本
当你需要更新yml文件并训练新模型时：

```bash
# 方法一：使用自动化脚本
cd rasa/versions
python create_new_version.py

# 方法二：手动创建
# 1. 创建文件夹：年月日时分_data_config
# 2. 复制当前配置文件到新文件夹
# 3. 更新日志文件
```

### 2. 查看现有版本
```bash
cd rasa/versions
python create_new_version.py  # 选择选项2
```

### 3. 更新日志
每次创建新版本后，请更新以下日志文件：
- `update_log.md` - 记录yml文件变更
- `model_training_log.md` - 记录模型训练信息
- `function_call_log.md` - 记录函数调用信息

## 工作流程

### 标准版本更新流程

1. **准备阶段**
   - 备份当前工作配置
   - 准备更新的yml文件

2. **创建版本**
   ```bash
   cd rasa/versions
   python create_new_version.py
   ```

3. **更新配置**
   - 修改 `rasa/data/` 下的yml文件
   - 或者修改 `rasa/config.yml`

4. **记录变更**
   - 编辑版本文件夹中的 `version_info.md`
   - 更新 `update_log.md` 记录变更详情

5. **模型训练**
   - 使用更新后的配置训练模型
   - 记录训练过程到 `model_training_log.md`

6. **验证部署**
   - 测试新模型性能
   - 更新 `function_call_log.md` 记录调用信息

### 版本回滚流程

如果新版本有问题，需要回滚到旧版本：

1. **找到目标版本**
   ```bash
   cd rasa/versions
   ls -la  # 查看所有版本文件夹
   ```

2. **复制配置文件**
   ```bash
   # 从版本文件夹复制到当前工作目录
   cp 202506210024_data_config/config.yml ../config.yml
   cp 202506210024_data_config/domain.yml ../data/domain.yml
   cp 202506210024_data_config/nlu.yml ../data/nlu.yml
   cp 202506210024_data_config/rules.yml ../data/rules.yml
   ```

3. **重新训练或切换模型**
   - 如果有对应的训练好的模型，直接切换激活
   - 如果没有，使用回滚的配置重新训练

4. **记录回滚操作**
   - 在 `function_call_log.md` 中记录版本切换

## 文件结构说明

```
rasa/
├── versions/                          # 版本管理根目录
│   ├── README.md                      # 版本管理说明
│   ├── USAGE_GUIDE.md                 # 使用指南（本文件）
│   ├── update_log.md                  # yml文件更新日志
│   ├── model_training_log.md          # 模型训练日志
│   ├── function_call_log.md           # 函数调用日志
│   ├── create_new_version.py          # 版本管理脚本
│   ├── 202506210024_data_config/      # 版本1：2025-06-21 00:24
│   │   ├── config.yml
│   │   ├── domain.yml
│   │   ├── nlu.yml
│   │   ├── rules.yml
│   │   └── version_info.md
│   └── 202506222244_data_config/      # 版本2：2025-06-22 22:44
│       ├── config.yml
│       ├── domain.yml
│       ├── nlu.yml
│       ├── rules.yml
│       └── version_info.md
├── data/                              # 当前工作数据文件
│   ├── domain.yml
│   ├── nlu.yml
│   └── rules.yml
├── config.yml                         # 当前工作配置文件
└── models/                            # 训练好的模型文件
    ├── 20250621-002404-asymptotic-cymbal.tar.gz
    └── 20250622-224446-rainy-combination.tar.gz
```

## 最佳实践

### 1. 版本命名
- 严格按照 `年月日时分_data_config` 格式
- 例如：`202506230930_data_config` 表示2025年6月23日09:30的版本

### 2. 文件管理
- **工作文件**：`rasa/config.yml` 和 `rasa/data/` 下的文件用于日常开发
- **版本文件**：`rasa/versions/` 下的文件只用于归档，不要直接修改
- **模型文件**：训练好的模型保存在 `rasa/models/` 下

### 3. 日志记录
- 每次创建版本都要记录到 `update_log.md`
- 每次训练模型都要记录到 `model_training_log.md`
- 每次切换配置都要记录到 `function_call_log.md`

### 4. 版本控制
- 使用Git管理整个项目，包括版本文件夹
- 重要的版本配置文件要提交到Git
- 模型文件过大，建议使用Git LFS或单独存储

## 常见问题

### Q: 如何查看某个模型使用的配置？
A: 通过模型文件名中的时间戳，找到对应的版本文件夹。例如 `20250622-224446-rainy-combination.tar.gz` 对应 `202506222244_data_config` 版本。

### Q: 可以删除旧版本吗？
A: 建议保留所有版本，特别是对应已训练模型的版本。如果存储空间不足，可以删除没有对应模型的版本。

### Q: 如何批量测试不同版本的性能？
A: 可以编写脚本，依次使用不同版本的配置进行训练和测试，对比性能指标。

### Q: 版本文件夹可以重命名吗？
A: 不建议重命名，因为文件夹名称与模型训练时间对应。如果必须重命名，请同时更新所有相关日志文件。

## 自动化建议

为了进一步提高效率，可以考虑：

1. **训练脚本集成**：修改训练脚本，自动创建版本并记录日志
2. **CI/CD集成**：在持续集成中自动进行版本管理
3. **性能监控**：自动记录不同版本的性能指标
4. **配置验证**：训练前自动验证配置文件的正确性

## 支持与反馈

如果在使用过程中遇到问题或有改进建议，请：
1. 检查相关日志文件
2. 查看版本文件夹的完整性
3. 记录问题现象和操作步骤
4. 联系系统维护人员 