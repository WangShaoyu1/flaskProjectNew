# 系统词槽Rasa配置指南

## 概述
本文档详细说明智能对话训练平台中5个系统词槽在Rasa中的配置方法和识别机制。

## 系统词槽详解

### 1. duration (时长)

#### 在Rasa中的作用
- **用途**：识别时间持续长度表达
- **Rasa组件**：DucklingEntityExtractor
- **ISO 8601格式**：返回标准的持续时间格式

#### 配置方法
```yaml
# config.yml
pipeline:
  - name: DucklingEntityExtractor
    dimensions: ["duration"]
    locale: "zh_CN"  # 支持中文
    timezone: "Asia/Shanghai"
```

#### 训练数据示例
```yaml
# nlu.yml
nlu:
- intent: set_timer
  examples: |
    - 设置[15分钟](duration)的定时器
    - 倒计时[2小时](duration)
    - [30秒](duration)后提醒我
    - 休眠[1天](duration)
    - 等待[半小时](duration)
```

#### 识别结果
```json
{
  "entity": "duration",
  "start": 2,
  "end": 6,
  "value": "PT15M",  // ISO 8601: 15分钟
  "confidence": 0.99
}
```

#### Domain配置
```yaml
# domain.yml
entities:
  - duration

slots:
  duration:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: duration
```

### 2. number (数字)

#### 在Rasa中的作用
- **用途**：识别数字表达（阿拉伯数字、中文数字）
- **Rasa组件**：DucklingEntityExtractor
- **标准化**：统一转换为数值

#### 配置方法
```yaml
# config.yml
pipeline:
  - name: DucklingEntityExtractor
    dimensions: ["number"]
    locale: "zh_CN"
```

#### 训练数据示例
```yaml
# nlu.yml
nlu:
- intent: set_volume
  examples: |
    - 音量调到[50](number)
    - 设置为[八十](number)
    - 调成[100](number)
    - 音量[三](number)
```

#### 识别结果
```json
{
  "entity": "number",
  "start": 4,
  "end": 6,
  "value": 50,
  "confidence": 0.98
}
```

### 3. quantity (数量)

#### 在Rasa中的作用
- **用途**：识别数量表达（数字+量词）
- **实现方式**：自定义实体识别器或正则表达式
- **扩展性**：支持各种量词组合

#### 配置方法
```yaml
# config.yml
pipeline:
  - name: RegexEntityExtractor
    case_sensitive: false
  - name: DIETClassifier
    epochs: 100
```

#### 正则表达式配置
```yaml
# nlu.yml
regex:
- name: quantity
  examples: |
    - \d+[个台件条张]
    - [一二三四五六七八九十]+[个台件条张]
    - (几|一些|很多|少量)[个台件条张]?
```

#### 训练数据示例
```yaml
# nlu.yml
nlu:
- intent: control_device
  examples: |
    - 打开[三台](quantity)空调
    - 关闭[两个](quantity)灯
    - 启动[一些](quantity)设备
    - 控制[五件](quantity)家电
```

### 4. time (时间)

#### 在Rasa中的作用
- **用途**：识别具体时间点
- **Rasa组件**：DucklingEntityExtractor
- **格式**：ISO 8601时间格式

#### 配置方法
```yaml
# config.yml
pipeline:
  - name: DucklingEntityExtractor
    dimensions: ["time"]
    locale: "zh_CN"
    timezone: "Asia/Shanghai"
```

#### 训练数据示例
```yaml
# nlu.yml
nlu:
- intent: schedule_task
  examples: |
    - [明天上午9点](time)开会
    - [下午3点](time)提醒我
    - [今晚8点](time)关灯
    - [周五](time)发送报告
```

#### 识别结果
```json
{
  "entity": "time",
  "start": 0,
  "end": 6,
  "value": "2024-01-02T09:00:00.000+08:00",
  "confidence": 0.97
}
```

### 5. volume (音量)

#### 在Rasa中的作用
- **用途**：识别音量相关表达
- **实现方式**：自定义训练（非Duckling内置）
- **应用场景**：智能音箱、音频设备控制

#### 配置方法
```yaml
# config.yml
pipeline:
  - name: DIETClassifier
    epochs: 100
  - name: EntitySynonymMapper
```

#### 同义词配置
```yaml
# nlu.yml
synonym:
- synonym: 大声
  examples: |
    - 大声
    - 大点声
    - 声音大
    - 高音量
    - 大音量

- synonym: 小声
  examples: |
    - 小声
    - 小点声
    - 声音小
    - 低音量
    - 静音
```

#### 训练数据示例
```yaml
# nlu.yml
nlu:
- intent: adjust_volume
  examples: |
    - 音量调[大声](volume)
    - 声音[小](volume)点
    - 调到[50%](volume)
    - 音量[最大](volume)
    - [静音](volume)
```

## 完整的Rasa配置

### config.yml 完整配置
```yaml
# Rasa配置文件
language: zh

pipeline:
  # 分词器
  - name: JiebaTokenizer
  
  # 特征提取
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: CountVectorsFeaturizer
    analyzer: "char_wb"
    min_ngram: 1
    max_ngram: 4
  
  # Duckling实体提取器（系统词槽）
  - name: DucklingEntityExtractor
    dimensions: ["time", "duration", "number"]
    locale: "zh_CN"
    timezone: "Asia/Shanghai"
  
  # 正则实体提取器
  - name: RegexEntityExtractor
    case_sensitive: false
  
  # DIET分类器（意图分类+实体识别）
  - name: DIETClassifier
    epochs: 100
    constrain_similarities: true
  
  # 实体同义词映射
  - name: EntitySynonymMapper
  
  # 响应选择器
  - name: ResponseSelector
    epochs: 100

# 对话策略
policies:
  - name: MemoizationPolicy
  - name: TEDPolicy
    max_history: 5
    epochs: 100
  - name: RulePolicy
```

### domain.yml 词槽配置
```yaml
# Domain配置
entities:
  - duration
  - number
  - quantity
  - time
  - volume

slots:
  duration:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: duration
  
  number:
    type: float
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: number
  
  quantity:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: quantity
  
  time:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: time
  
  volume:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: volume

intents:
  - greet
  - set_timer
  - set_volume
  - control_device
  - schedule_task
  - adjust_volume

responses:
  utter_timer_set:
  - text: "已设置{duration}的定时器"
  
  utter_volume_adjusted:
  - text: "音量已调整为{volume}"
  
  utter_device_controlled:
  - text: "已控制{quantity}设备"
```

## 使用示例

### 对话流程示例
```
用户: "设置15分钟的定时器"
Rasa识别:
- intent: set_timer
- entities: [{"entity": "duration", "value": "PT15M"}]
- slots: {"duration": "PT15M"}
机器人: "已设置15分钟的定时器"

用户: "明天上午9点提醒我"
Rasa识别:
- intent: schedule_task
- entities: [{"entity": "time", "value": "2024-01-02T09:00:00"}]
- slots: {"time": "2024-01-02T09:00:00"}
机器人: "已设置明天上午9点的提醒"
```

## 最佳实践

### 1. 系统词槽优势
- **准确性高**：Duckling组件经过大量训练，识别准确率高
- **多语言支持**：支持中英文混合识别
- **标准格式**：返回标准化的时间和数字格式
- **维护成本低**：无需自己训练和维护

### 2. 训练数据建议
- **覆盖全面**：包含各种表达方式
- **真实场景**：基于实际用户输入
- **平衡分布**：各种表达方式均衡分布
- **持续优化**：根据实际使用情况调整

### 3. 性能优化
- **合理配置**：只启用需要的Duckling维度
- **缓存机制**：利用Rasa的缓存机制
- **模型优化**：定期重新训练模型
- **监控指标**：监控实体识别准确率

### 4. 错误处理
- **置信度阈值**：设置合理的置信度阈值
- **回退机制**：提供实体识别失败的回退处理
- **用户确认**：对重要实体进行用户确认
- **日志记录**：记录识别错误以便优化

## 总结

这5个系统词槽为智能对话系统提供了强大的基础实体识别能力：

1. **duration** 和 **time**：利用Duckling的强大时间识别能力
2. **number**：提供准确的数字识别和标准化
3. **quantity** 和 **volume**：通过自定义训练支持业务特定需求

通过合理配置和使用这些系统词槽，可以大大提高对话系统的实体识别准确性和用户体验。 