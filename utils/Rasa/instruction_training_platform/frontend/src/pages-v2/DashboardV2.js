import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Card, Row, Col, Statistic, List, Button, Tag, Space, Alert, Spin, Dropdown, App 
} from 'antd';
import {
  CheckCircleOutlined,
  DatabaseOutlined,
  MessageOutlined,
  TagsOutlined,
  ExperimentOutlined,
  RobotOutlined,
  BranchesOutlined,
  UploadOutlined,
  DownOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { libraryAPI, systemAPI } from '../api-v2';
import { safeTableDataSource } from '../utils/dataSourceUtils';
import PerformanceMonitor from '../components/PerformanceMonitor';
import BatchOperations from '../components/BatchOperations';

const DashboardV2 = () => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [systemInfo, setSystemInfo] = useState(null);
  const [libraries, setLibraries] = useState([]);
  const [error, setError] = useState(null);
  const [batchOperationVisible, setBatchOperationVisible] = useState(false);
  const [batchOperationType, setBatchOperationType] = useState('import');
  const [batchDataType, setBatchDataType] = useState('instructions');

  // 获取系统信息
  const fetchSystemInfo = async () => {
    try {
      const [systemResponse, versionResponse] = await Promise.all([
        systemAPI.getSystemStatus(),
        systemAPI.getVersion()
      ]);
      
      setSystemInfo({
        status: systemResponse.data,
        version: versionResponse.data
      });
    } catch (error) {
      console.error('获取系统信息失败:', error);
      setError('获取系统信息失败');
    }
  };

  // 获取指令库统计
  const fetchLibraries = async () => {
    try {
      const response = await libraryAPI.getLibraries({ page: 1, size: 5 });
      // 后端直接返回数组，不是包含libraries字段的对象
      setLibraries(response.data || []);
    } catch (error) {
      console.error('获取指令库列表失败:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchSystemInfo(),
        fetchLibraries()
      ]);
      setLoading(false);
    };

    loadData();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="正在加载仪表板数据...">
          <div style={{ minHeight: '200px' }} />
        </Spin>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="数据加载失败"
        description={error}
        type="error"
        showIcon
        action={
          <Button onClick={() => window.location.reload()}>
            重新加载
          </Button>
        }
      />
    );
  }

  const quickActionsExtra = [
    <Space key="actions">
      <Dropdown
        menu={{
          items: [
            {
              key: 'import-instructions',
              label: '批量导入指令',
              onClick: () => {
                setBatchOperationType('import');
                setBatchDataType('instructions');
                setBatchOperationVisible(true);
              }
            },
            {
              key: 'import-slots',
              label: '批量导入词槽',
              onClick: () => {
                setBatchOperationType('import');
                setBatchDataType('slots');
                setBatchOperationVisible(true);
              }
            },
            {
              key: 'export-data',
              label: '批量导出数据',
              onClick: () => {
                setBatchOperationType('export');
                setBatchDataType('instructions');
                setBatchOperationVisible(true);
              }
            }
          ]
        }}
      >
        <Button icon={<UploadOutlined />}>
          批量操作 <DownOutlined />
        </Button>
      </Dropdown>
      <Button type="primary" icon={<RobotOutlined />} onClick={() => navigate('/training')}>
        快速训练
      </Button>
    </Space>
  ];

  return (
    <div className="dashboard-v2">
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>
          欢迎使用智能对话训练平台 v2.0.0
        </h1>
        <p style={{ color: '#666', margin: '8px 0 0 0' }}>
          基于RASA的智能对话模型训练和管理平台
        </p>
      </div>

      {/* 系统状态卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="系统状态"
              value="运行中"
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平台版本"
              value="v2.0.0"
              prefix={<RobotOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="指令库数量"
              value={libraries.length}
              prefix={<DatabaseOutlined style={{ color: '#fa8c16' }} />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="API端点"
              value="37"
              prefix={<BranchesOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 功能模块状态 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="功能模块状态" extra={<Tag color="green">全部就绪</Tag>}>
            <List
              dataSource={[
                { 
                  name: '指令库管理', 
                  status: 'ready', 
                  description: '4个API端点',
                  icon: <DatabaseOutlined style={{ color: '#1890ff' }} />
                },
                { 
                  name: '指令数据管理', 
                  status: 'ready', 
                  description: '7个API端点',
                  icon: <MessageOutlined style={{ color: '#52c41a' }} />
                },
                { 
                  name: '词槽管理', 
                  status: 'ready', 
                  description: '11个API端点',
                  icon: <TagsOutlined style={{ color: '#fa8c16' }} />
                },
                { 
                  name: '指令测试', 
                  status: 'ready', 
                  description: '7个API端点',
                  icon: <ExperimentOutlined style={{ color: '#722ed1' }} />
                },
                { 
                  name: '模型训练', 
                  status: 'ready', 
                  description: '5个API端点',
                  icon: <RobotOutlined style={{ color: '#eb2f96' }} />
                },
                { 
                  name: '版本管理', 
                  status: 'ready', 
                  description: '7个API端点',
                  icon: <BranchesOutlined style={{ color: '#13c2c2' }} />
                },
                { 
                  name: '系统监控', 
                  status: 'ready', 
                  description: '3个API端点',
                  icon: <ReloadOutlined style={{ color: '#fa541c' }} />
                }
              ]}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={item.icon}
                    title={
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {item.name}
                        <Tag color={item.status === 'ready' ? 'green' : 'orange'}>
                          {item.status === 'ready' ? '就绪' : '开发中'}
                        </Tag>
                      </div>
                    }
                    description={item.description}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="指令库概览" extra={<Button type="link" onClick={() => navigate('/libraries')}>查看全部</Button>}>
            {libraries.length > 0 ? (
              <List
                dataSource={safeTableDataSource(libraries)}
                renderItem={library => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={<DatabaseOutlined style={{ color: '#1890ff', fontSize: '18px' }} />}
                      title={library.name}
                      description={
                        <div>
                          <div style={{ marginBottom: 4 }}>
                            语言: {library.language} | 业务编码: {library.business_code || '无'}
                          </div>
                          <div style={{ display: 'flex', gap: 8 }}>
                            <Tag color="blue">指令: {library.instruction_count || 0}</Tag>
                            <Tag color="green">词槽: {library.slot_count || 0}</Tag>
                            <Tag color="orange">版本: v{library.latest_version || 0}</Tag>
                          </div>
                        </div>
                      }
                    />
                  </List.Item>
                )}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                <DatabaseOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>暂无指令库</div>
                <Button 
                  type="primary" 
                  style={{ marginTop: '16px' }}
                  onClick={() => navigate('/libraries')}
                >
                  创建第一个指令库
                </Button>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* 快速操作 */}
      <Card title="快速操作" extra={quickActionsExtra}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card
              hoverable
              style={{ textAlign: 'center', cursor: 'pointer' }}
              styles={{ body: { padding: '24px 16px' } }}
              onClick={() => navigate('/libraries')}
            >
              <DatabaseOutlined style={{ fontSize: '32px', color: '#1890ff', marginBottom: '16px' }} />
              <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>
                管理指令库
              </div>
              <div style={{ color: '#666', fontSize: '14px' }}>
                创建和管理指令库
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card
              hoverable
              style={{ textAlign: 'center', cursor: 'pointer' }}
              styles={{ body: { padding: '24px 16px' } }}
              onClick={() => navigate('/instructions')}
            >
              <MessageOutlined style={{ fontSize: '32px', color: '#52c41a', marginBottom: '16px' }} />
              <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>
                录入指令
              </div>
              <div style={{ color: '#666', fontSize: '14px' }}>
                添加训练数据
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card
              hoverable
              style={{ textAlign: 'center', cursor: 'pointer' }}
              styles={{ body: { padding: '24px 16px' } }}
              onClick={() => navigate('/training')}
            >
              <RobotOutlined style={{ fontSize: '32px', color: '#fa8c16', marginBottom: '16px' }} />
              <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>
                开始训练
              </div>
              <div style={{ color: '#666', fontSize: '14px' }}>
                训练RASA模型
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card
              hoverable
              style={{ textAlign: 'center', cursor: 'pointer' }}
              styles={{ body: { padding: '24px 16px' } }}
              onClick={() => navigate('/testing')}
            >
              <ExperimentOutlined style={{ fontSize: '32px', color: '#722ed1', marginBottom: '16px' }} />
              <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '8px' }}>
                测试模型
              </div>
              <div style={{ color: '#666', fontSize: '14px' }}>
                验证模型效果
              </div>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* 系统性能监控 */}
      <Card
        title="系统性能监控"
        style={{ marginTop: 24 }}
        extra={
          <Space>
            <Tag color="green">实时监控</Tag>
            <Button size="small" icon={<ReloadOutlined />}>
              刷新
            </Button>
          </Space>
        }
      >
        <PerformanceMonitor
          autoRefresh={true}
          refreshInterval={10000}
          onAlert={(alerts) => {
            alerts.forEach(alert => {
              if (alert.type === 'error') {
                message.error(alert.title);
              } else if (alert.type === 'warning') {
                message.warning(alert.title);
              }
            });
          }}
        />
      </Card>

      {/* 批量操作模态框 */}
      <BatchOperations
        visible={batchOperationVisible}
        onCancel={() => setBatchOperationVisible(false)}
        onSuccess={(result) => {
          message.success(`操作完成，成功处理 ${result.success} 条记录`);
          // 刷新相关数据
          fetchLibraries();
        }}
        operationType={batchOperationType}
        dataType={batchDataType}
      />
    </div>
  );
};

export default DashboardV2; 