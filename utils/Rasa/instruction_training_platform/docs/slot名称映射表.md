# Slot名称映射表

## 概述
本文档维护了智能家居指令系统中所有slot的中英文名称映射关系，确保代码的国际化兼容性和可维护性。

## 映射规则
- **英文名称**：使用snake_case命名风格
- **中文说明**：保留原始中文含义
- **类型说明**：标注slot的数据类型
- **使用场景**：说明该slot的应用场景

## 完整映射表

### 基础属性类
| 英文名称 | 中文名称 | 类型 | 值范围 | 使用场景 |
|---------|---------|------|--------|----------|
| `portion` | 份量 | categorical | 小份, 大份, 中份 | 烹饪指令中的分量控制 |
| `taste` | 口感 | categorical | 脆嫩, 软烂, 嫩滑, 紧实, 脆爽, 软糯, 默认, 肉嫩味美, 松软, 软韧, 适中 | 烹饪效果设定 |
| `category` | 品类 | categorical | 水产类, 肉类, 蔬菜类, 饮品, 即食品, 剩菜 | 食材分类 |
| `power` | 火力 | categorical | 低火, 中火, 高火, 解冻, 中高火 | 加热功率设定 |

### 时间设置类
| 英文名称 | 中文名称 | 类型 | 值范围 | 使用场景 |
|---------|---------|------|--------|----------|
| `sleep_time` | 休眠时间 | categorical | 15秒, 30秒, 1分钟, 2分钟, 5分钟, 10分钟, 永不 | 设备休眠设置 |
| `cooking_time` | 烹饪时间 | text | 自由文本 | 烹饪时长设定 |
| `timing` | 定时 | text | 自由文本 | 定时功能设置 |

### 系统设置类
| 英文名称 | 中文名称 | 类型 | 值范围 | 使用场景 |
|---------|---------|------|--------|----------|
| `broadcast_mode` | 播报模式 | categorical | 标准模式, 简易模式 | 语音播报设置 |
| `volume_level` | 音量 | categorical | 静音, 低音量, 中音量, 高音量, 最大音量 | 音量控制 |
| `brightness` | 亮度 | categorical | 暗, 中等, 亮, 最亮 | 屏幕亮度设置 |

### 序号和判断类
| 英文名称 | 中文名称 | 类型 | 值范围 | 使用场景 |
|---------|---------|------|--------|----------|
| `number` | 第N | categorical | 第一, 第二, 第三, 第四, 第五, 1, 2, 3, 4, 5 | 序号选择 |
| `confirm` | 肯否判断 | categorical | 肯定, 否定 | 确认操作 |

### 内容标识类
| 英文名称 | 中文名称 | 类型 | 值范围 | 使用场景 |
|---------|---------|------|--------|----------|
| `dish_name` | 菜品名称 | categorical | 各种菜品名称 | 菜谱识别 |
| `page_name` | 页面名称 | categorical | 使用帮助页, 语言切换页, 设备信息页, 网络设置页, 设置页, 烹饪记录 | 界面导航 |

## 使用示例

### Domain.yml 配置示例
```yaml
slots:
  # 基础属性类
  portion:        # 份量
    type: categorical
    values:
    - 小份
    - 大份
    - 中份
    mappings:
    - type: from_entity
      entity: 份量

  taste:          # 口感
    type: categorical
    values:
    - 脆嫩
    - 软烂
    - 嫩滑
    - 紧实
    - 脆爽
    - 软糯
    - 默认
    - 肉嫩味美
    - 松软
    - 软韧
    - 适中
    mappings:
    - type: from_entity
      entity: 口感

  # 时间设置类
  sleep_time:     # 休眠时间
    type: categorical
    values:
    - 15秒
    - 30秒
    - 1分钟
    - 2分钟
    - 5分钟
    - 10分钟
    - 永不
    mappings:
    - type: from_entity
      entity: 休眠时间
```

### 代码中的使用示例
```python
# 在自定义动作中使用slot
class ActionSetPortion(Action):
    def name(self) -> Text:
        return "action_set_portion"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # 获取份量设置 (中文: 份量)
        portion = tracker.get_slot("portion")
        
        if portion:
            dispatcher.utter_message(text=f"已设置份量为：{portion}")
        
        return []
```

## 命名规范

### 1. 英文命名规则
- 使用小写字母和下划线
- 采用snake_case命名风格
- 名称要有意义且简洁
- 避免使用缩写，除非是通用缩写

### 2. 注释规范
- 每个slot定义后添加中文注释
- 在代码中使用时添加说明注释
- 重要的业务逻辑要详细说明

### 3. 文档维护
- 新增slot时及时更新映射表
- 定期检查映射关系的一致性
- 保持文档的时效性

## 迁移指南

### 已完成的映射
以下slot已经完成中英文映射：
- ✅ 份量 → portion
- ✅ 休眠时间 → sleep_time
- ✅ 口感 → taste
- ✅ 品类 → category
- ✅ 播报模式 → broadcast_mode
- ✅ 火力 → power
- ✅ 第N → number
- ✅ 肯否判断 → confirm
- ✅ 菜品名称 → dish_name
- ✅ 页面名称 → page_name

### 待确认的映射
如果发现新的中文slot，请按照以下步骤处理：
1. 在此映射表中添加新的映射关系
2. 更新domain.yml文件
3. 检查相关的训练数据
4. 测试功能是否正常

## 维护日志

| 日期 | 操作 | 说明 |
|------|------|------|
| 2025-01-20 | 创建 | 初始创建映射表，包含所有已知slot |
| | | |

## 注意事项

1. **一致性**：确保在所有文件中使用统一的英文名称
2. **向后兼容**：修改时要考虑现有功能的兼容性
3. **文档同步**：修改slot名称时要同步更新所有相关文档
4. **测试验证**：每次修改后都要进行完整的功能测试

## 相关文件

- `rasa/data/domain.yml` - slot定义文件
- `rasa/data/nlu.yml` - NLU训练数据
- `backend/services/rasa_service.py` - Rasa服务接口
- `public/intents.json` - 意图数据源 