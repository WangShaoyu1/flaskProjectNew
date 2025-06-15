import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Switch, 
  Typography, 
  Space,
  Divider,
  Alert,
  message,
  Row,
  Col
} from 'antd';
import { 
  SettingOutlined, 
  SaveOutlined,
  ReloadOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { toolsAPI } from '../api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const Settings = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [systemInfo, setSystemInfo] = useState(null);

  useEffect(() => {
    loadSystemInfo();
    loadSettings();
  }, []);

  const loadSystemInfo = async () => {
    try {
      const response = await toolsAPI.getSystemInfo();
      setSystemInfo(response.data);
    } catch (error) {
      console.error('加载系统信息失败:', error);
    }
  };

  const loadSettings = () => {
    // 从 localStorage 加载设置
    const savedSettings = localStorage.getItem('platform_settings');
    if (savedSettings) {
      const settings = JSON.parse(savedSettings);
      form.setFieldsValue(settings);
    } else {
      // 默认设置
      form.setFieldsValue({
        rasa_server_url: 'http://localhost:5005',
        auto_train: false,
        gpu_enabled: true,
        training_epochs: 100,
        confidence_threshold: 0.3,
        fallback_threshold: 0.1,
        max_history: 5,
        debug_mode: false,
        log_level: 'INFO'
      });
    }
  };

  const handleSaveSettings = async (values) => {
    setLoading(true);
    try {
      // 保存到 localStorage
      localStorage.setItem('platform_settings', JSON.stringify(values));
      message.success('设置保存成功');
    } catch (error) {
      message.error('设置保存失败');
      console.error('保存设置失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResetSettings = () => {
    localStorage.removeItem('platform_settings');
    loadSettings();
    message.success('设置已重置为默认值');
  };

  const renderSystemInfo = () => {
    if (!systemInfo) return null;

    return (
      <Card title="系统信息" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <div>
              <Text strong>操作系统:</Text>
              <div>{systemInfo.platform}</div>
            </div>
          </Col>
          <Col span={12}>
            <div>
              <Text strong>Python 版本:</Text>
              <div>{systemInfo.python_version}</div>
            </div>
          </Col>
          <Col span={12}>
            <div>
              <Text strong>CPU 核心数:</Text>
              <div>{systemInfo.cpu_count} 核</div>
            </div>
          </Col>
          <Col span={12}>
            <div>
              <Text strong>内存总量:</Text>
              <div>{(systemInfo.memory_total / 1024 / 1024 / 1024).toFixed(2)} GB</div>
            </div>
          </Col>
          <Col span={12}>
            <div>
              <Text strong>GPU 状态:</Text>
              <div>
                {systemInfo.gpu_available ? (
                  <Text type="success">可用 ({systemInfo.gpu_devices?.length || 0} 个设备)</Text>
                ) : (
                  <Text type="warning">不可用</Text>
                )}
              </div>
            </div>
          </Col>
          <Col span={12}>
            <div>
              <Text strong>Rasa 服务:</Text>
              <div>
                {systemInfo.rasa_status ? (
                  <Text type="success">运行中</Text>
                ) : (
                  <Text type="danger">未运行</Text>
                )}
              </div>
            </div>
          </Col>
        </Row>
      </Card>
    );
  };

  return (
    <div>
      {renderSystemInfo()}

      <Card 
        title={
          <Space>
            <SettingOutlined />
            系统设置
          </Space>
        }
        extra={
          <Space>
            <Button 
              icon={<ReloadOutlined />}
              onClick={handleResetSettings}
            >
              重置默认
            </Button>
            <Button 
              type="primary"
              icon={<SaveOutlined />}
              onClick={() => form.submit()}
              loading={loading}
            >
              保存设置
            </Button>
          </Space>
        }
      >
        <Form
          form={form}
          onFinish={handleSaveSettings}
          layout="vertical"
        >
          {/* Rasa 服务配置 */}
          <Title level={4}>Rasa 服务配置</Title>
          
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Form.Item
                name="rasa_server_url"
                label="Rasa 服务地址"
                rules={[{ required: true, message: '请输入 Rasa 服务地址' }]}
              >
                <Input placeholder="http://localhost:5005" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="auto_train"
                label="自动训练"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 训练配置 */}
          <Title level={4}>训练配置</Title>
          
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <Form.Item
                name="gpu_enabled"
                label="启用 GPU 加速"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="training_epochs"
                label="训练轮次"
                rules={[{ required: true, message: '请输入训练轮次' }]}
              >
                <Input type="number" min={1} max={1000} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="max_history"
                label="最大历史长度"
                rules={[{ required: true, message: '请输入最大历史长度' }]}
              >
                <Input type="number" min={1} max={20} />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 预测配置 */}
          <Title level={4}>预测配置</Title>
          
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Form.Item
                name="confidence_threshold"
                label="置信度阈值"
                rules={[{ required: true, message: '请输入置信度阈值' }]}
              >
                <Input 
                  type="number" 
                  min={0} 
                  max={1} 
                  step={0.1}
                  placeholder="0.3"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="fallback_threshold"
                label="Fallback 阈值"
                rules={[{ required: true, message: '请输入 Fallback 阈值' }]}
              >
                <Input 
                  type="number" 
                  min={0} 
                  max={1} 
                  step={0.1}
                  placeholder="0.1"
                />
              </Form.Item>
            </Col>
          </Row>

          <Alert
            message="阈值说明"
            description="置信度阈值用于判断预测结果的可信度，Fallback 阈值用于触发兜底回复。建议根据实际测试结果调整这些参数。"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Divider />

          {/* 系统配置 */}
          <Title level={4}>系统配置</Title>
          
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <Form.Item
                name="debug_mode"
                label="调试模式"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="log_level"
                label="日志级别"
                rules={[{ required: true, message: '请选择日志级别' }]}
              >
                <select style={{ width: '100%', padding: '4px 8px' }}>
                  <option value="DEBUG">DEBUG</option>
                  <option value="INFO">INFO</option>
                  <option value="WARNING">WARNING</option>
                  <option value="ERROR">ERROR</option>
                </select>
              </Form.Item>
            </Col>
          </Row>

          <Alert
            message="配置说明"
            description={
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li>调试模式会输出更详细的日志信息，有助于问题排查</li>
                <li>日志级别控制系统输出的日志详细程度</li>
                <li>修改配置后可能需要重启相关服务才能生效</li>
              </ul>
            }
            type="warning"
            showIcon
          />
        </Form>
      </Card>
    </div>
  );
};

export default Settings;

