import React, { useState, useEffect } from 'react';
import { 
  Card, Tabs, Switch, Select, Slider, Button, Form, Input, 
  Row, Col, Divider, Avatar, Badge, Space, Alert, Modal,
  Typography, Progress, Statistic, Tag, Radio, ColorPicker,
  Upload, Tooltip, message
} from 'antd';
import {
  SettingOutlined, UserOutlined, BgColorsOutlined, 
  DatabaseOutlined, SecurityScanOutlined, InfoCircleOutlined,
  CloudUploadOutlined, DownloadOutlined, BellOutlined,
  GlobalOutlined, ThunderboltOutlined, EyeOutlined,
  LockOutlined, SaveOutlined, ReloadOutlined, ExportOutlined,
  ImportOutlined, DeleteOutlined, CrownOutlined, RocketOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const SettingsV2 = () => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('appearance');
  const [settings, setSettings] = useState({
    theme: 'light',
    primaryColor: '#1890ff',
    language: 'zh-CN',
    autoSave: true,
    notifications: true,
    performance: 'balanced',
    dataRetention: 30
  });
  
  const [form] = Form.useForm();

  // 保存设置
  const handleSaveSettings = async (values) => {
    setLoading(true);
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSettings({ ...settings, ...values });
      message.success('设置已保存');
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  // 重置设置
  const handleResetSettings = () => {
    Modal.confirm({
      title: '确认重置',
      content: '是否要将所有设置重置为默认值？此操作不可撤销。',
      okText: '确认重置',
      cancelText: '取消',
      okType: 'danger',
      onOk: () => {
        const defaultSettings = {
          theme: 'light',
          primaryColor: '#1890ff',
          language: 'zh-CN',
          autoSave: true,
          notifications: true,
          performance: 'balanced',
          dataRetention: 30
        };
        setSettings(defaultSettings);
        form.setFieldsValue(defaultSettings);
        message.success('设置已重置');
      }
    });
  };

  // 导出设置
  const handleExportSettings = () => {
    const dataStr = JSON.stringify(settings, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = 'system-settings.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    message.success('设置已导出');
  };

  useEffect(() => {
    form.setFieldsValue(settings);
  }, [settings, form]);

  // 外观设置Tab
  const AppearanceTab = () => (
    <div className="settings-tab-content">
      <div className="settings-section">
        <Title level={4} className="section-title">
          <BgColorsOutlined /> 主题配置
        </Title>
        <Row gutter={[24, 24]}>
          <Col xs={24} md={12}>
            <Card className="theme-card" hoverable>
              <div className="theme-preview light-theme">
                <div className="theme-header"></div>
                <div className="theme-sidebar"></div>
                <div className="theme-content"></div>
              </div>
              <div className="theme-info">
                <Text strong>浅色主题</Text>
                <br />
                <Text type="secondary">清新简洁，适合日间使用</Text>
              </div>
              <Radio.Group value={settings.theme} onChange={(e) => setSettings({...settings, theme: e.target.value})}>
                <Radio value="light">选择</Radio>
              </Radio.Group>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card className="theme-card" hoverable>
              <div className="theme-preview dark-theme">
                <div className="theme-header"></div>
                <div className="theme-sidebar"></div>
                <div className="theme-content"></div>
              </div>
              <div className="theme-info">
                <Text strong>深色主题</Text>
                <br />
                <Text type="secondary">护眼舒适，适合夜间使用</Text>
              </div>
              <Radio.Group value={settings.theme} onChange={(e) => setSettings({...settings, theme: e.target.value})}>
                <Radio value="dark">选择</Radio>
              </Radio.Group>
            </Card>
          </Col>
        </Row>
      </div>

      <Divider />

      <div className="settings-section">
        <Title level={4} className="section-title">
          <CrownOutlined /> 高级配色
        </Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <div className="color-option">
              <Text strong>主色调</Text>
              <br />
              <ColorPicker 
                value={settings.primaryColor}
                onChange={(color) => setSettings({...settings, primaryColor: color.toHexString()})}
                showText
              />
            </div>
          </Col>
          <Col xs={24} sm={8}>
            <div className="color-option">
              <Text strong>成功色</Text>
              <br />
              <ColorPicker defaultValue="#52c41a" showText />
            </div>
          </Col>
          <Col xs={24} sm={8}>
            <div className="color-option">
              <Text strong>警告色</Text>
              <br />
              <ColorPicker defaultValue="#faad14" showText />
            </div>
          </Col>
        </Row>
      </div>

      <Divider />

      <div className="settings-section">
        <Title level={4} className="section-title">
          <EyeOutlined /> 界面设置
        </Title>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Row gutter={[24, 16]}>
            <Col span={12}>
              <div className="setting-item">
                <Text strong>紧凑模式</Text>
                <br />
                <Text type="secondary">减少界面元素间距</Text>
              </div>
            </Col>
            <Col span={12}>
              <Switch />
            </Col>
          </Row>
          <Row gutter={[24, 16]}>
            <Col span={12}>
              <div className="setting-item">
                <Text strong>动画效果</Text>
                <br />
                <Text type="secondary">启用界面过渡动画</Text>
              </div>
            </Col>
            <Col span={12}>
              <Switch defaultChecked />
            </Col>
          </Row>
          <Row gutter={[24, 16]}>
            <Col span={12}>
              <div className="setting-item">
                <Text strong>侧边栏折叠</Text>
                <br />
                <Text type="secondary">默认折叠左侧导航栏</Text>
              </div>
            </Col>
            <Col span={12}>
              <Switch />
            </Col>
          </Row>
        </Space>
      </div>
    </div>
  );

  // 系统配置Tab
  const SystemTab = () => (
    <div className="settings-tab-content">
      <Alert
        message="系统配置"
        description="修改这些设置可能会影响系统性能，请谨慎操作。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <div className="settings-section">
        <Title level={4} className="section-title">
          <RocketOutlined /> 性能优化
        </Title>
        <Row gutter={[24, 24]}>
          <Col span={24}>
            <div className="performance-cards">
              <Row gutter={[16, 16]}>
                <Col xs={24} md={8}>
                  <Card className="performance-card" hoverable>
                    <Statistic
                      title="性能模式"
                      value="均衡"
                      prefix={<ThunderboltOutlined style={{ color: '#52c41a' }} />}
                    />
                    <Progress percent={75} strokeColor="#52c41a" />
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card className="performance-card" hoverable>
                    <Statistic
                      title="内存使用"
                      value={68}
                      suffix="%"
                      prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
                    />
                    <Progress percent={68} strokeColor="#1890ff" />
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card className="performance-card" hoverable>
                    <Statistic
                      title="缓存大小"
                      value={256}
                      suffix="MB"
                      prefix={<CloudUploadOutlined style={{ color: '#722ed1' }} />}
                    />
                    <Progress percent={45} strokeColor="#722ed1" />
                  </Card>
                </Col>
              </Row>
            </div>
          </Col>
        </Row>
      </div>

      <Divider />

      <div className="settings-section">
        <Title level={4} className="section-title">
          <DatabaseOutlined /> API配置
        </Title>
        <Form layout="vertical">
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Form.Item label="后端API地址" name="backendUrl">
                <Input defaultValue="http://localhost:8001" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="Rasa API地址" name="rasaUrl">
                <Input defaultValue="http://localhost:5005" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="请求超时时间" name="timeout">
                <Select defaultValue="30">
                  <Option value="10">10秒</Option>
                  <Option value="30">30秒</Option>
                  <Option value="60">60秒</Option>
                  <Option value="120">120秒</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="并发请求数" name="concurrent">
                <Slider defaultValue={5} min={1} max={20} marks={{1: '1', 10: '10', 20: '20'}} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </div>
    </div>
  );

  // 用户偏好Tab
  const PreferencesTab = () => (
    <div className="settings-tab-content">
      <div className="settings-section">
        <Title level={4} className="section-title">
          <GlobalOutlined /> 地区与语言
        </Title>
        <Row gutter={[24, 16]}>
          <Col xs={24} md={12}>
            <Form.Item label="显示语言">
              <Select defaultValue="zh-CN" size="large">
                <Option value="zh-CN">简体中文</Option>
                <Option value="zh-TW">繁体中文</Option>
                <Option value="en-US">English (US)</Option>
                <Option value="ja-JP">日本語</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col xs={24} md={12}>
            <Form.Item label="时区设置">
              <Select defaultValue="Asia/Shanghai" size="large">
                <Option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</Option>
                <Option value="America/New_York">America/New_York (UTC-5)</Option>
                <Option value="Europe/London">Europe/London (UTC+0)</Option>
                <Option value="Asia/Tokyo">Asia/Tokyo (UTC+9)</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
      </div>

      <Divider />

      <div className="settings-section">
        <Title level={4} className="section-title">
          <BellOutlined /> 通知设置
        </Title>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Row gutter={[24, 16]}>
            <Col span={16}>
              <div className="setting-item">
                <Text strong>桌面通知</Text>
                <br />
                <Text type="secondary">接收系统重要通知</Text>
              </div>
            </Col>
            <Col span={8}>
              <Switch defaultChecked />
            </Col>
          </Row>
          <Row gutter={[24, 16]}>
            <Col span={16}>
              <div className="setting-item">
                <Text strong>训练完成通知</Text>
                <br />
                <Text type="secondary">模型训练完成时通知</Text>
              </div>
            </Col>
            <Col span={8}>
              <Switch defaultChecked />
            </Col>
          </Row>
          <Row gutter={[24, 16]}>
            <Col span={16}>
              <div className="setting-item">
                <Text strong>错误提醒</Text>
                <br />
                <Text type="secondary">系统错误时发送提醒</Text>
              </div>
            </Col>
            <Col span={8}>
              <Switch defaultChecked />
            </Col>
          </Row>
          <Row gutter={[24, 16]}>
            <Col span={16}>
              <div className="setting-item">
                <Text strong>邮件通知</Text>
                <br />
                <Text type="secondary">重要事件邮件提醒</Text>
              </div>
            </Col>
            <Col span={8}>
              <Switch />
            </Col>
          </Row>
        </Space>
      </div>
    </div>
  );

  // 数据管理Tab
  const DataTab = () => (
    <div className="settings-tab-content">
      <div className="settings-section">
        <Title level={4} className="section-title">
          <CloudUploadOutlined /> 数据备份
        </Title>
        <Alert
          message="数据安全"
          description="定期备份重要数据，确保数据安全。建议开启自动备份功能。"
          type="success"
          showIcon
          style={{ marginBottom: 24 }}
        />
        
        <Row gutter={[24, 24]}>
          <Col xs={24} md={12}>
            <Card title="自动备份" extra={<Switch defaultChecked />} className="backup-card">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>备份频率：</Text>
                  <Select defaultValue="daily" style={{ marginLeft: 8, width: 120 }}>
                    <Option value="hourly">每小时</Option>
                    <Option value="daily">每日</Option>
                    <Option value="weekly">每周</Option>
                  </Select>
                </div>
                <div>
                  <Text strong>保留天数：</Text>
                  <Slider defaultValue={30} min={7} max={90} style={{ width: 200, marginLeft: 8 }} />
                </div>
                <Button type="primary" icon={<CloudUploadOutlined />}>
                  立即备份
                </Button>
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card title="手动操作" className="backup-card">
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Button 
                  icon={<ExportOutlined />} 
                  block 
                  onClick={handleExportSettings}
                >
                  导出设置
                </Button>
                <Upload>
                  <Button icon={<ImportOutlined />} block>
                    导入设置
                  </Button>
                </Upload>
                <Button icon={<DownloadOutlined />} block>
                  下载数据备份
                </Button>
                <Button 
                  danger 
                  icon={<DeleteOutlined />} 
                  block
                >
                  清理临时数据
                </Button>
              </Space>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );

  // 关于系统Tab
  const AboutTab = () => (
    <div className="settings-tab-content">
      <div className="about-header">
        <div className="about-logo">
          <Avatar size={64} icon={<ThunderboltOutlined />} />
        </div>
        <div className="about-info">
          <Title level={2}>智能对话训练平台</Title>
          <Text type="secondary">Intelligent Training Platform v2.0.0</Text>
          <br />
          <Badge status="success" text="系统运行正常" />
        </div>
      </div>

      <Divider />

      <Row gutter={[24, 24]}>
        <Col xs={24} md={12}>
          <Card title="系统信息" className="info-card">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div className="info-item">
                <Text strong>版本号：</Text>
                <Tag color="blue">v2.0.0</Tag>
              </div>
              <div className="info-item">
                <Text strong>构建时间：</Text>
                <Text code>2025-07-01 20:30:15</Text>
              </div>
              <div className="info-item">
                <Text strong>运行时间：</Text>
                <Text code>2天 15小时 32分钟</Text>
              </div>
              <div className="info-item">
                <Text strong>数据库：</Text>
                <Badge status="success" text="SQLite 连接正常" />
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="技术栈" className="info-card">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div className="tech-item">
                <Text strong>前端：</Text>
                <Tag color="cyan">React 18.2.0</Tag>
                <Tag color="blue">Ant Design 5.0</Tag>
              </div>
              <div className="tech-item">
                <Text strong>后端：</Text>
                <Tag color="green">FastAPI 0.104</Tag>
                <Tag color="orange">Python 3.9</Tag>
              </div>
              <div className="tech-item">
                <Text strong>AI引擎：</Text>
                <Tag color="purple">Rasa 3.6</Tag>
                <Tag color="red">TensorFlow 2.13</Tag>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>

      <Divider />

      <div className="license-section">
        <Title level={4}>许可证信息</Title>
        <Paragraph>
          智能对话训练平台遵循 MIT 许可证。您可以自由使用、修改和分发本软件。
          详细信息请查看 LICENSE 文件。
        </Paragraph>
        <Space>
          <Button type="primary" icon={<InfoCircleOutlined />}>
            查看许可证
          </Button>
          <Button icon={<GlobalOutlined />}>
            访问官网
          </Button>
        </Space>
      </div>
    </div>
  );

  return (
    <div className="settings-v2-modern">
      <style jsx>{`
        .settings-v2-modern {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: calc(100vh - 64px);
          padding: 24px;
        }
        
        .settings-container {
          max-width: 1200px;
          margin: 0 auto;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border-radius: 16px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }
        
        .settings-header {
          background: linear-gradient(90deg, #1890ff, #722ed1);
          color: white;
          padding: 32px;
          text-align: center;
        }
        
        .settings-content {
          padding: 0;
        }
        
        .settings-tab-content {
          padding: 32px;
          min-height: 600px;
        }
        
        .settings-section {
          margin-bottom: 32px;
        }
        
        .section-title {
          color: #262626;
          margin-bottom: 24px !important;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .theme-card {
          border-radius: 12px;
          overflow: hidden;
          transition: all 0.3s ease;
          border: 2px solid transparent;
        }
        
        .theme-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }
        
        .theme-preview {
          height: 120px;
          position: relative;
          border-radius: 8px;
          overflow: hidden;
          margin-bottom: 16px;
        }
        
        .light-theme {
          background: #f0f2f5;
        }
        
        .dark-theme {
          background: #1f1f1f;
        }
        
        .theme-header {
          height: 20px;
          background: #1890ff;
        }
        
        .theme-sidebar {
          position: absolute;
          left: 0;
          top: 20px;
          width: 40px;
          height: 100px;
          background: rgba(0, 0, 0, 0.1);
        }
        
        .theme-content {
          position: absolute;
          left: 40px;
          top: 20px;
          right: 0;
          height: 100px;
          background: rgba(255, 255, 255, 0.8);
        }
        
        .performance-cards .ant-card {
          border-radius: 12px;
          border: none;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }
        
        .color-option {
          text-align: center;
          padding: 16px;
          border: 1px solid #f0f0f0;
          border-radius: 8px;
          transition: all 0.3s ease;
        }
        
        .color-option:hover {
          border-color: #1890ff;
          box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
        }
        
        .setting-item {
          padding: 8px 0;
        }
        
        .backup-card {
          border-radius: 12px;
          height: 100%;
        }
        
        .about-header {
          display: flex;
          align-items: center;
          gap: 24px;
          padding: 24px;
          background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
          border-radius: 12px;
          margin-bottom: 24px;
        }
        
        .info-card {
          border-radius: 12px;
          height: 100%;
        }
        
        .info-item, .tech-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #f0f0f0;
        }
        
        .info-item:last-child, .tech-item:last-child {
          border-bottom: none;
        }
        
        .license-section {
          background: #fafafa;
          padding: 24px;
          border-radius: 12px;
          border-left: 4px solid #1890ff;
        }
        
        .ant-tabs-tab {
          font-weight: 500;
        }
        
        .ant-tabs-tab-active {
          background: linear-gradient(135deg, #1890ff, #722ed1);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
      `}</style>
      
      <div className="settings-container">
        <div className="settings-header">
          <Title level={2} style={{ color: 'white', margin: 0 }}>
            <SettingOutlined style={{ marginRight: 12 }} />
            系统设置
          </Title>
          <Text style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: 16 }}>
            个性化配置您的智能对话训练平台
          </Text>
        </div>
        
        <div className="settings-content">
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            type="card"
            size="large"
            tabPosition="top"
          >
            <TabPane
              tab={
                <span>
                  <BgColorsOutlined />
                  外观设置
                </span>
              }
              key="appearance"
            >
              <AppearanceTab />
            </TabPane>

            <TabPane
              tab={
                <span>
                  <DatabaseOutlined />
                  系统配置
                </span>
              }
              key="system"
            >
              <SystemTab />
            </TabPane>

            <TabPane
              tab={
                <span>
                  <UserOutlined />
                  用户偏好
                </span>
              }
              key="preferences"
            >
              <PreferencesTab />
            </TabPane>

            <TabPane
              tab={
                <span>
                  <CloudUploadOutlined />
                  数据管理
                </span>
              }
              key="data"
            >
              <DataTab />
            </TabPane>

            <TabPane
              tab={
                <span>
                  <InfoCircleOutlined />
                  关于系统
                </span>
              }
              key="about"
            >
              <AboutTab />
            </TabPane>
          </Tabs>
        </div>
        
        {/* 底部操作栏 */}
        <div style={{ 
          padding: '24px 32px', 
          borderTop: '1px solid #f0f0f0',
          background: '#fafafa',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Space>
            <Button 
              type="primary" 
              icon={<SaveOutlined />} 
              size="large"
              loading={loading}
              onClick={() => handleSaveSettings(settings)}
            >
              保存设置
            </Button>
            <Button 
              icon={<ReloadOutlined />} 
              size="large"
              onClick={handleResetSettings}
            >
              重置默认
            </Button>
          </Space>
          
          <Space>
            <Tooltip title="导出当前配置">
              <Button 
                icon={<ExportOutlined />} 
                size="large"
                onClick={handleExportSettings}
              >
                导出配置
              </Button>
            </Tooltip>
          </Space>
        </div>
      </div>
    </div>
  );
};

export default SettingsV2; 