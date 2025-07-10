import React, { useState } from 'react';
import { 
  Card, Tabs, Switch, Select, Button, Form, Input, 
  Row, Col, Typography, Progress, Statistic, Tag, 
  Space, Alert, Modal, message, Descriptions, Avatar, Badge
} from 'antd';
import {
  SettingOutlined, UserOutlined, BgColorsOutlined, 
  DatabaseOutlined, InfoCircleOutlined, GlobalOutlined, 
  ThunderboltOutlined, RocketOutlined, SaveOutlined, 
  ReloadOutlined, ExportOutlined, StarOutlined, BellOutlined
} from '@ant-design/icons';


const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const SettingsV2 = () => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('appearance');
  const [settings, setSettings] = useState({
    theme: 'classic-blue',
    darkMode: false,
    language: 'zh-CN',
    autoSave: true,
    notifications: true
  });

  // 保存设置
  const handleSaveSettings = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('设置已保存');
      localStorage.setItem('userSettings', JSON.stringify(settings));
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
        setSettings({
          theme: 'classic-blue',
          darkMode: false,
          language: 'zh-CN',
          autoSave: true,
          notifications: true
        });
        message.success('设置已重置为默认值');
      }
    });
  };

  return (
    <div style={{ 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      minHeight: 'calc(100vh - 64px)',
      padding: '24px'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        background: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '16px',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
        overflow: 'hidden'
      }}>
        {/* 页面头部 */}
        <div style={{
          background: 'linear-gradient(90deg, #1890ff, #722ed1)',
          color: 'white',
          padding: '32px',
          textAlign: 'center'
        }}>
          <Title level={2} style={{ color: 'white', margin: 0 }}>
            <SettingOutlined style={{ marginRight: '12px' }} />
            系统设置中心
          </Title>
          <Text style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: 16 }}>
            打造专属的智能对话训练平台体验
          </Text>
        </div>

        {/* Tab内容区域 */}
        <div style={{ padding: '24px' }}>
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            type="card"
            size="large"
            items={[
              {
                key: 'appearance',
                label: (
                  <span style={{ fontSize: '16px' }}>
                    <BgColorsOutlined style={{ marginRight: '8px' }} />
                    外观定制
                  </span>
                ),
                children: (
                  <div style={{ padding: '24px 0' }}>
                    <Card 
                      title={
                        <span>
                          <StarOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                          主题风格
                        </span>
                      }
                      style={{ marginBottom: '24px', borderRadius: '12px' }}
                    >
                      <Row gutter={[16, 16]}>
                        {[
                          { name: '经典蓝', color: '#1890ff', desc: '专业稳重，适合商务场景' },
                          { name: '科技紫', color: '#722ed1', desc: '科技感十足，彰显创新' },
                          { name: '活力橙', color: '#fa541c', desc: '充满活力，激发创造力' },
                          { name: '自然绿', color: '#52c41a', desc: '清新自然，护眼舒适' }
                        ].map((theme, index) => (
                          <Col xs={24} sm={12} md={6} key={index}>
                            <Card 
                              hoverable
                              style={{
                                borderRadius: '12px',
                                textAlign: 'center',
                                border: settings.theme === theme.name ? '2px solid #1890ff' : '1px solid #d9d9d9'
                              }}
                              onClick={() => setSettings({...settings, theme: theme.name})}
                            >
                              <div style={{
                                height: '80px',
                                background: `linear-gradient(135deg, ${theme.color}, ${theme.color}99)`,
                                borderRadius: '8px',
                                marginBottom: '12px'
                              }}></div>
                              <Text strong>{theme.name}</Text>
                              <br />
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                {theme.desc}
                              </Text>
                            </Card>
                          </Col>
                        ))}
                      </Row>
                    </Card>

                    <Card 
                      title={
                        <span>
                          <BgColorsOutlined style={{ marginRight: '8px', color: '#722ed1' }} />
                          界面设置
                        </span>
                      }
                      style={{ borderRadius: '12px' }}
                    >
                      <Space direction="vertical" size="large" style={{ width: '100%' }}>
                        {[
                          { key: 'darkMode', title: '深色模式', desc: '护眼舒适，适合夜间使用' },
                          { key: 'compactMode', title: '紧凑模式', desc: '减少界面元素间距' },
                          { key: 'animationEnabled', title: '动画效果', desc: '启用界面过渡动画' }
                        ].map((item, index) => (
                          <Row key={index} align="middle" justify="space-between">
                            <Col span={18}>
                              <div>
                                <Text strong style={{ fontSize: '16px' }}>{item.title}</Text>
                                <br />
                                <Text type="secondary">{item.desc}</Text>
                              </div>
                            </Col>
                            <Col span={6} style={{ textAlign: 'right' }}>
                              <Switch 
                                checked={settings[item.key]}
                                onChange={(checked) => setSettings({...settings, [item.key]: checked})}
                              />
                            </Col>
                          </Row>
                        ))}
                      </Space>
                    </Card>
                  </div>
                )
              },
              {
                key: 'system',
                label: (
                  <span style={{ fontSize: '16px' }}>
                    <DatabaseOutlined style={{ marginRight: '8px' }} />
                    系统配置
                  </span>
                ),
                children: (
                  <div style={{ padding: '24px 0' }}>
                    <Alert
                      message="系统配置警告"
                      description="修改这些设置可能会影响系统性能，请谨慎操作。"
                      type="warning"
                      showIcon
                      style={{ marginBottom: '24px' }}
                    />

                    <Card 
                      title={
                        <span>
                          <RocketOutlined style={{ marginRight: '8px', color: '#fa541c' }} />
                          性能监控
                        </span>
                      }
                      style={{ marginBottom: '24px', borderRadius: '12px' }}
                    >
                      <Row gutter={[24, 16]}>
                        <Col xs={24} md={8}>
                          <Card style={{ textAlign: 'center', background: '#f6ffed' }}>
                            <Statistic
                              title="CPU使用率"
                              value={28}
                              suffix="%"
                              prefix={<ThunderboltOutlined style={{ color: '#52c41a' }} />}
                              valueStyle={{ color: '#52c41a' }}
                            />
                            <Progress percent={28} strokeColor="#52c41a" />
                          </Card>
                        </Col>
                        <Col xs={24} md={8}>
                          <Card style={{ textAlign: 'center', background: '#f0f9ff' }}>
                            <Statistic
                              title="内存使用"
                              value={68}
                              suffix="%"
                              prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
                              valueStyle={{ color: '#1890ff' }}
                            />
                            <Progress percent={68} strokeColor="#1890ff" />
                          </Card>
                        </Col>
                        <Col xs={24} md={8}>
                          <Card style={{ textAlign: 'center', background: '#f9f0ff' }}>
                            <Statistic
                              title="存储空间"
                              value={45}
                              suffix="%"
                              prefix={<GlobalOutlined style={{ color: '#722ed1' }} />}
                              valueStyle={{ color: '#722ed1' }}
                            />
                            <Progress percent={45} strokeColor="#722ed1" />
                          </Card>
                        </Col>
                      </Row>
                    </Card>

                    <Card 
                      title="API服务配置"
                      style={{ borderRadius: '12px' }}
                    >
                      <Form layout="vertical">
                        <Row gutter={[16, 16]}>
                          <Col xs={24} md={12}>
                            <Form.Item label="后端API地址">
                              <Input defaultValue="http://localhost:8001" />
                            </Form.Item>
                          </Col>
                          <Col xs={24} md={12}>
                            <Form.Item label="Rasa API地址">
                              <Input defaultValue="http://localhost:5005" />
                            </Form.Item>
                          </Col>
                        </Row>
                      </Form>
                    </Card>
                  </div>
                )
              },
              {
                key: 'preferences',
                label: (
                  <span style={{ fontSize: '16px' }}>
                    <UserOutlined style={{ marginRight: '8px' }} />
                    用户偏好
                  </span>
                ),
                children: (
                  <div style={{ padding: '24px 0' }}>
                    <Card 
                      title={
                        <span>
                          <GlobalOutlined style={{ marginRight: '8px', color: '#722ed1' }} />
                          地区与语言
                        </span>
                      }
                      style={{ marginBottom: '24px', borderRadius: '12px' }}
                    >
                      <Row gutter={[24, 16]}>
                        <Col xs={24} md={12}>
                          <Form.Item label="显示语言">
                            <Select defaultValue="zh-CN" size="large">
                              <Option value="zh-CN">🇨🇳 简体中文</Option>
                              <Option value="zh-TW">🇹🇼 繁体中文</Option>
                              <Option value="en-US">🇺🇸 English (US)</Option>
                              <Option value="ja-JP">🇯🇵 日本語</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item label="时区设置">
                            <Select defaultValue="Asia/Shanghai" size="large">
                              <Option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</Option>
                              <Option value="America/New_York">America/New_York (UTC-5)</Option>
                              <Option value="Europe/London">Europe/London (UTC+0)</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                      </Row>
                    </Card>

                    <Card 
                      title={
                        <span>
                          <BellOutlined style={{ marginRight: '8px', color: '#fa541c' }} />
                          通知偏好
                        </span>
                      }
                      style={{ borderRadius: '12px' }}
                    >
                      <Space direction="vertical" size="large" style={{ width: '100%' }}>
                        {[
                          { title: '桌面通知', desc: '重要系统事件的桌面提醒', icon: '🔔' },
                          { title: '训练完成通知', desc: '模型训练完成时的即时通知', icon: '🤖' },
                          { title: '错误警报', desc: '系统异常和错误的及时提醒', icon: '⚠️' },
                          { title: '邮件通知', desc: '重要事件的邮件提醒服务', icon: '📧' }
                        ].map((item, index) => (
                          <Row key={index} align="middle" justify="space-between">
                            <Col span={18}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <span style={{ fontSize: '20px' }}>{item.icon}</span>
                                <div>
                                  <Text strong style={{ fontSize: '16px' }}>{item.title}</Text>
                                  <br />
                                  <Text type="secondary">{item.desc}</Text>
                                </div>
                              </div>
                            </Col>
                            <Col span={6} style={{ textAlign: 'right' }}>
                              <Switch defaultChecked={index < 3} />
                            </Col>
                          </Row>
                        ))}
                      </Space>
                    </Card>
                  </div>
                )
              },
              {
                key: 'about',
                label: (
                  <span style={{ fontSize: '16px' }}>
                    <InfoCircleOutlined style={{ marginRight: '8px' }} />
                    关于系统
                  </span>
                ),
                children: (
                  <div style={{ padding: '24px 0' }}>
                    <Card style={{ marginBottom: '24px', borderRadius: '12px', overflow: 'hidden' }}>
                      <div style={{
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        padding: '32px',
                        margin: '-24px -24px 24px -24px',
                        textAlign: 'center'
                      }}>
                        <Avatar 
                          size={80} 
                          icon={<ThunderboltOutlined />} 
                          style={{ 
                            background: 'rgba(255, 255, 255, 0.2)',
                            marginBottom: '16px'
                          }} 
                        />
                        <Title level={2} style={{ color: 'white', margin: 0 }}>
                          智能对话训练平台
                        </Title>
                        <Text style={{ color: 'rgba(255, 255, 255, 0.9)', fontSize: 16 }}>
                          Intelligent Training Platform v2.0.0
                        </Text>
                        <br />
                        <Badge 
                          status="success" 
                          text="系统运行正常" 
                          style={{ color: 'rgba(255, 255, 255, 0.9)', marginTop: '8px' }}
                        />
                      </div>

                      <Descriptions column={2} bordered>
                        <Descriptions.Item label="版本号">
                          <Tag color="blue">v2.0.0</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="构建时间">
                          <Text code>2025-07-01 20:30:15</Text>
                        </Descriptions.Item>
                        <Descriptions.Item label="运行时间">
                          <Text code>2天 15小时 32分钟</Text>
                        </Descriptions.Item>
                        <Descriptions.Item label="数据库状态">
                          <Badge status="success" text="SQLite 连接正常" />
                        </Descriptions.Item>
                        <Descriptions.Item label="前端技术" span={2}>
                          <Space>
                            <Tag color="cyan">React 18.2</Tag>
                            <Tag color="blue">Ant Design 5.0</Tag>
                          </Space>
                        </Descriptions.Item>
                        <Descriptions.Item label="后端技术" span={2}>
                          <Space>
                            <Tag color="green">FastAPI 0.104</Tag>
                            <Tag color="orange">Python 3.9</Tag>
                            <Tag color="purple">Rasa 3.6</Tag>
                          </Space>
                        </Descriptions.Item>
                      </Descriptions>
                    </Card>

                    <Card title="开源许可与支持" style={{ borderRadius: '12px' }}>
                      <Paragraph style={{ fontSize: '16px', lineHeight: '1.6' }}>
                        智能对话训练平台采用 <Text strong>MIT 开源许可证</Text>，
                        您可以自由使用、修改和分发本软件。
                      </Paragraph>
                      <Space>
                        <Button type="primary" icon={<InfoCircleOutlined />}>
                          查看许可证
                        </Button>
                        <Button icon={<GlobalOutlined />}>
                          访问官网
                        </Button>
                        <Button icon={<StarOutlined />}>
                          GitHub Stars
                        </Button>
                      </Space>
                    </Card>
                  </div>
                )
              }
            ]}
          />
        </div>

        {/* 底部操作栏 */}
        <div style={{ 
          padding: '24px 32px', 
          borderTop: '1px solid #f0f0f0',
          background: 'linear-gradient(135deg, #f6f9fc 0%, #e9ecef 100%)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Space size="middle">
            <Button 
              type="primary" 
              icon={<SaveOutlined />} 
              size="large"
              loading={loading}
              onClick={handleSaveSettings}
              style={{
                background: 'linear-gradient(135deg, #1890ff, #722ed1)',
                border: 'none',
                borderRadius: '8px',
                height: '42px'
              }}
            >
              保存设置
            </Button>
            <Button 
              icon={<ReloadOutlined />} 
              size="large"
              onClick={handleResetSettings}
              style={{ borderRadius: '8px', height: '42px' }}
            >
              恢复默认
            </Button>
          </Space>
          
          <Space>
            <Button 
              icon={<ExportOutlined />} 
              size="large"
              style={{ borderRadius: '8px', height: '42px' }}
            >
              导出配置
            </Button>
            <Badge dot status="success">
              <Text type="secondary">自动保存</Text>
            </Badge>
          </Space>
        </div>
      </div>
    </div>
  );
};

export default SettingsV2; 