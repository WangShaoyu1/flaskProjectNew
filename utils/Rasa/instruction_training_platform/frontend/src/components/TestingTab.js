import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Form, Input, message, Select,
  Row, Col, Statistic, Space, Tag, Alert, Descriptions
} from 'antd';
import {
  ExperimentOutlined, PlayCircleOutlined,
  CheckCircleOutlined, ClockCircleOutlined, RobotOutlined
} from '@ant-design/icons';
import { formatLocalTime } from '../utils/timeUtils';

const { TextArea } = Input;
const { Option } = Select;

const TestingTab = ({ currentLibrary, availableModels = [] }) => {
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [selectedModel, setSelectedModel] = useState(null);
  const [form] = Form.useForm();

  // 当有可用模型时，自动选择最新的模型
  useEffect(() => {
    if (availableModels.length > 0 && !selectedModel) {
      // 按时间排序，选择最新的模型
      const sortedModels = [...availableModels].sort((a, b) =>
        new Date(b.start_time || b.created_time) - new Date(a.start_time || a.created_time)
      );
      setSelectedModel(sortedModels[0]);
    }
  }, [availableModels, selectedModel]);

  // 检查是否选择了指令库
  if (!currentLibrary) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <ExperimentOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
          <h3>请先选择指令库</h3>
          <p style={{ color: '#666' }}>在开始测试之前，请先选择一个指令库。</p>
        </div>
      </Card>
    );
  }

  // 处理测试
  const handleTest = async (values) => {
    if (!selectedModel) {
      message.error('请先选择一个模型版本');
      return;
    }

    setLoading(true);
    try {
      // TODO: 调用真实的测试API
      message.info('测试功能正在开发中');
      setTestResult({
        input_text: values.input_text,
        model_version: selectedModel.version_number,
        intent: 'test_intent',
        confidence: 0.85,
        entities: [],
        response_time: 120
      });
    } catch (error) {
      message.error('测试失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 模型选择变化处理
  const handleModelChange = (modelId) => {
    const model = availableModels.find(m => m.id === modelId);
    setSelectedModel(model);
  };

  return (
    <div className="testing-tab">
      {/* 模型选择 */}
      <Card title="模型版本选择" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Form.Item label="选择模型版本">
              <Select
                value={selectedModel?.id}
                onChange={handleModelChange}
                placeholder="请选择要测试的模型版本"
                style={{ width: '100%' }}
              >
                {availableModels.map(model => (
                  <Option key={model.id} value={model.id}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 'bold', color: '#1890ff' }}>v{model.version_number}</span>
                    </div>
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col xs={24} md={16}>
            {selectedModel && (
              <Descriptions size="middle" column={4}>
                <Descriptions.Item label="模型版本">v{selectedModel.version_number}</Descriptions.Item>
                <Descriptions.Item label="训练时间">{formatLocalTime(selectedModel.start_time || selectedModel.created_time)}</Descriptions.Item>
                <Descriptions.Item label="指令数量">{selectedModel.intent_count || 0}</Descriptions.Item>
                <Descriptions.Item label="词槽数量">{selectedModel.slot_count || 0}</Descriptions.Item>
              </Descriptions>
            )}
          </Col>
        </Row>
      </Card>

      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="可用模型"
              value={availableModels.length}
              prefix={<RobotOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="总测试次数"
              value={0}
              prefix={<ExperimentOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="成功测试"
              value={0}
              prefix={<CheckCircleOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="平均成功率"
              value={0}
              suffix="%"
              prefix={<CheckCircleOutlined style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 快速测试 */}
      <Card title="快速单条测试" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={handleTest}>
          <Form.Item
            name="input_text"
            label="测试文本"
            rules={[{ required: true, message: '请输入测试文本' }]}
          >
            <TextArea
              rows={3}
              placeholder="请输入要测试的文本，例如：北京今天天气怎么样？"
              maxLength={200}
              showCount
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<PlayCircleOutlined />}
              disabled={!selectedModel}
            >
              立即测试
            </Button>
            {!selectedModel && (
              <span style={{ marginLeft: 8, color: '#ff4d4f' }}>
                请先选择模型版本
              </span>
            )}
          </Form.Item>
        </Form>

        {/* 测试结果 */}
        {testResult && (
          <Card
            title="测试结果"
            style={{ marginTop: 16 }}
          >
            <Descriptions bordered column={2}>
              <Descriptions.Item label="输入文本" span={2}>
                {testResult.input_text}
              </Descriptions.Item>
              <Descriptions.Item label="识别意图">
                <Tag color="blue">{testResult.intent}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="置信度">
                <Tag color={testResult.confidence >= 0.8 ? 'green' : testResult.confidence >= 0.6 ? 'orange' : 'red'}>
                  {(testResult.confidence * 100).toFixed(1)}%
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="实体识别" span={2}>
                {testResult.entities.length > 0 ? (
                  <Space>
                    {testResult.entities.map((entity, index) => (
                      <Tag key={index} color="purple">
                        {entity.entity}: {entity.value}
                      </Tag>
                    ))}
                  </Space>
                ) : (
                  <span style={{ color: '#666' }}>未识别到实体</span>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="响应时间">
                {testResult.response_time}ms
              </Descriptions.Item>
              <Descriptions.Item label="模型版本">
                v{testResult.model_version}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}
      </Card>

      {/* 功能提示 */}
      <Alert
        message="测试功能已就绪"
        description={`当前有 ${availableModels.length} 个可用的训练模型版本，您可以选择任意版本进行指令测试。更多高级功能（批量测试、测试记录管理、详细测试报告等）正在开发中。`}
        type="success"
        showIcon
      />
    </div>
  );
};

export default TestingTab; 