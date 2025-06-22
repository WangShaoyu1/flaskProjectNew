# 智能家居指令训练平台 - Slot映射系统

## 概述

本项目采用英文slot名称映射的方式来解决Rasa框架不支持中文slot名称的问题。通过维护一套完整的中英文映射关系，既保证了系统的技术兼容性，又保持了中文业务逻辑的清晰性。

## 系统架构

```
智能家居指令系统
├── 前端界面 (React)
├── 后端API (FastAPI)
├── Rasa NLU服务
└── Slot映射系统 ⭐
    ├── 映射表维护
    ├── 验证工具
    └── 文档管理
```

## 核心文件

### 1. 映射表文档
- **文件**: `docs/slot名称映射表.md`
- **作用**: 维护完整的中英文slot映射关系
- **包含**: 映射表、使用示例、命名规范、维护指南

### 2. 配置文件
- **文件**: `rasa/data/domain.yml`
- **作用**: Rasa领域配置，使用英文slot名称
- **特点**: 每个slot都有中文注释说明

### 3. 验证工具
- **文件**: `tools/validate_slot_mapping.py`
- **作用**: 自动验证映射关系的一致性
- **功能**: 检查映射完整性、生成验证报告

## 快速开始

### 1. 查看当前映射关系
```bash
# 查看映射表
cat docs/slot名称映射表.md

# 运行验证工具
python tools/validate_slot_mapping.py
```

### 2. 添加新的slot映射

#### 步骤1: 更新映射表
在 `docs/slot名称映射表.md` 中添加新的映射关系：

```markdown
| `new_slot` | 新功能 | categorical | 值1, 值2, 值3 | 功能说明 |
```

#### 步骤2: 更新domain.yml
在 `rasa/data/domain.yml` 中添加slot定义：

```yaml
slots:
  new_slot:        # 新功能
    type: categorical
    values:
    - 值1
    - 值2  
    - 值3
    mappings:
    - type: from_entity
      entity: 新功能
```

#### 步骤3: 更新验证工具
在 `tools/validate_slot_mapping.py` 的 `get_expected_mappings()` 函数中添加：

```python
'new_slot': '新功能',
```

#### 步骤4: 验证映射
```bash
python tools/validate_slot_mapping.py
```

### 3. 在代码中使用slot

#### 后端Python代码
```python
# 获取slot值 (使用英文名称)
portion = tracker.get_slot("portion")  # 份量
taste = tracker.get_slot("taste")      # 口感
power = tracker.get_slot("power")      # 火力

# 添加注释说明中文含义
if portion:  # 份量设置
    dispatcher.utter_message(text=f"已设置份量为：{portion}")
```

#### 前端JavaScript代码
```javascript
// API调用时使用英文slot名称
const slotData = {
    portion: "大份",      // 份量
    taste: "脆嫩",        // 口感  
    power: "中火"         // 火力
};
```

## 当前映射关系

| 英文名称 | 中文名称 | 状态 | 值数量 |
|---------|---------|------|--------|
| `portion` | 份量 | ✅ | 3 |
| `sleep_time` | 休眠时间 | ✅ | 7 |
| `taste` | 口感 | ✅ | 11 |
| `category` | 品类 | ✅ | 6 |
| `broadcast_mode` | 播报模式 | ✅ | 2 |
| `power` | 火力 | ✅ | 5 |
| `number` | 第N | ✅ | 100 |
| `confirm` | 肯否判断 | ✅ | 2 |
| `dish_name` | 菜品名称 | ✅ | 705 |
| `page_name` | 页面名称 | ✅ | 6 |

## 开发规范

### 1. 命名规范
- **英文名称**: 使用 `snake_case` 格式
- **有意义**: 名称要能清楚表达功能
- **简洁**: 避免过长的名称
- **一致性**: 同类功能使用相似的命名模式

### 2. 注释规范
```yaml
# ✅ 好的示例
portion:        # 份量
  type: categorical
  values:
  - 小份        # 小份量
  - 大份        # 大份量
  - 中份        # 中份量

# ❌ 不好的示例  
portion:
  type: categorical
  values:
  - 小份
  - 大份
  - 中份
```

### 3. 文档维护
- 新增slot时必须同时更新映射表
- 定期运行验证工具检查一致性
- 重要变更要更新维护日志

## 工具使用

### 验证工具详解

#### 基本用法
```bash
python tools/validate_slot_mapping.py
```

#### 输出说明
- ✅ 验证通过：映射关系正确
- ❌ 验证失败：存在不一致的映射
- ⚠️ 警告：发现未映射的slot

#### 报告文件
验证工具会生成详细报告：`tools/slot_mapping_validation_report.md`

### 批量操作

#### 检查所有配置文件
```bash
# 检查domain.yml语法
python -c "import yaml; yaml.safe_load(open('rasa/data/domain.yml', 'r', encoding='utf-8'))"

# 验证映射关系
python tools/validate_slot_mapping.py

# 检查NLU数据
python -m rasa data validate
```

## 故障排除

### 常见问题

#### 1. 映射验证失败
**问题**: Entity映射错误
```
❌ Entity映射错误: portion -> 份量设置, 预期: 份量
```

**解决**: 检查domain.yml中的entity名称是否正确

#### 2. Rasa训练失败
**问题**: slot名称包含中文字符
```
Key '份量' does not match any regex '[A-Za-z]+'. Path: '/slots'
```

**解决**: 确保所有slot名称都是英文

#### 3. 新slot未生效
**问题**: 添加新slot后不起作用

**解决步骤**:
1. 检查映射表是否更新
2. 验证domain.yml配置
3. 运行验证工具
4. 重新训练Rasa模型

### 调试技巧

#### 1. 查看slot值
```python
# 在自定义动作中调试
def run(self, dispatcher, tracker, domain):
    # 打印所有slot值
    slots = tracker.current_slot_values()
    print(f"当前slot值: {slots}")
    
    # 检查特定slot
    portion = tracker.get_slot("portion")
    print(f"份量设置: {portion}")
```

#### 2. 验证NLU识别
```bash
# 测试NLU识别
curl -X POST http://localhost:5005/model/parse \\
  -H "Content-Type: application/json" \\
  -d '{"text": "设置大份量"}'
```

## 最佳实践

### 1. 开发流程
1. **设计阶段**: 先确定中文业务名称
2. **映射阶段**: 设计对应的英文slot名称
3. **实现阶段**: 在代码中使用英文名称，添加中文注释
4. **测试阶段**: 运行验证工具确保一致性
5. **部署阶段**: 更新文档和维护日志

### 2. 团队协作
- 统一使用映射表中的名称
- 重要变更要通知团队成员
- 定期review映射关系
- 保持文档同步更新

### 3. 版本管理
- 映射表变更要记录在维护日志中
- 重大变更要创建新的版本标签
- 保持向后兼容性

## 技术背景

### 为什么需要英文映射？

1. **Rasa限制**: Rasa使用正则表达式 `[A-Za-z]+` 验证slot名称
2. **国际化**: 英文名称便于国际化和团队协作
3. **兼容性**: 避免编码和系统兼容性问题
4. **标准化**: 符合软件开发的命名规范

### 技术实现原理

```
中文业务逻辑 ←→ 英文slot名称 ←→ Rasa处理
     ↑              ↑              ↑
  用户界面        映射层          NLU引擎
```

## 相关文档

- [Rasa中文slot名称支持调研报告.md](../Rasa中文slot名称支持调研报告.md)
- [Rasa服务状态报告.md](../Rasa服务状态报告.md)
- [slot名称映射表.md](./slot名称映射表.md)

## 维护团队

- 负责人: AI Assistant
- 创建时间: 2025-01-20
- 最后更新: 2025-01-20

---

💡 **提示**: 遇到问题时，首先运行验证工具检查映射关系的一致性！ 