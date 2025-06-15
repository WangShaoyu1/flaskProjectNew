import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, List, Typography, Spin, Alert } from 'antd';
import { 
  BulbOutlined, 
  RobotOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined,
  TrophyOutlined,
  ApiOutlined
} from '@ant-design/icons';
import { intentAPI, toolsAPI, rasaAPI } from '../api';

const { Title, Text } = Typography;

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalIntents: 0,
    totalUtterances: 0,
    totalModels: 0,
    activeModel: null,
    recentActivities: []
  });
  const [systemInfo, setSystemInfo] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // 并行加载数据
      const [intentsRes, modelsRes, systemRes] = await Promise.allSettled([
        intentAPI.getIntents(),
        toolsAPI.getModels({ limit: 10 }),
        toolsAPI.getSystemInfo()
      ]);

      // 处理意图数据
      if (intentsRes.status === 'fulfilled') {
        const intents = intentsRes.value.data;
        let totalUtterances = 0;
        
        // 计算总相似问数量
        for (const intent of intents) {
          try {
            const utterancesRes = await intentAPI.getUtterances(intent.id);
            totalUtterances += utterancesRes.data.length;
          } catch (error) {
            console.error(`获取意图 ${intent.id} 的相似问失败:`, error);
          }
        }

        setStats(prev => ({
          ...prev,
          totalIntents: intents.length,
          totalUtterances
        }));
      }

      // 处理模型数据
      if (modelsRes.status === 'fulfilled') {
        const models = modelsRes.value.data;
        const activeModel = models.find(model => model.is_active);
        
        setStats(prev => ({
          ...prev,
          totalModels: models.length,
          activeModel,
          recentActivities: models.slice(0, 5).map(model => ({
            title: `模型 ${model.version}`,
            description: `训练时间: ${new Date(model.training_time).toLocaleString()}`,
            status: model.status,
            time: model.training_time
          }))
        }));
      }

      // 处理系统信息
      if (systemRes.status === 'fulfilled') {
        setSystemInfo(systemRes.value.data);
      }

    } catch (error) {
      console.error('加载仪表板数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderSystemStatus = () => {
    if (!systemInfo) return null;

    const memoryUsage = ((systemInfo.memory_total - systemInfo.memory_available) / systemInfo.memory_total * 100).toFixed(1);
    
    return (
      <Card title="系统状态" style={{ height: '100%' }}>
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Statistic
              title="CPU 核心数"
              value={systemInfo.cpu_count}
              suffix="核"
              prefix={<ApiOutlined />}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="内存使用率"
              value={memoryUsage}
              suffix="%"
              prefix={<ClockCircleOutlined />}
            />
          </Col>
          <Col span={24}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>内存使用情况</Text>
            </div>
            <Progress 
              percent={parseFloat(memoryUsage)} 
              status={memoryUsage > 80 ? 'exception' : 'normal'}
              format={percent => `${percent}%`}
            />
          </Col>
          <Col span={24}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>GPU 状态</Text>
            </div>
            {systemInfo.gpu_available ? (
              <Alert
                message="GPU 可用"
                description={`检测到 ${systemInfo.gpu_devices?.length || 0} 个 GPU 设备`}
                type="success"
                showIcon
              />
            ) : (
              <Alert
                message="GPU 不可用"
                description="未检测到可用的 GPU 设备"
                type="warning"
                showIcon
              />
            )}
          </Col>
        </Row>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" tip="正在加载仪表板数据..." />
      </div>
    );
  }

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总意图数"
              value={stats.totalIntents}
              prefix={<BulbOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总相似问数"
              value={stats.totalUtterances}
              prefix={<ApiOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="模型总数"
              value={stats.totalModels}
              prefix={<RobotOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="当前模型"
              value={stats.activeModel ? stats.activeModel.version : '无'}
              prefix={<TrophyOutlined style={{ color: '#fa8c16' }} />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[24, 24]}>
        {/* 最近活动 */}
        <Col xs={24} lg={12}>
          <Card title="最近活动" style={{ height: 400 }}>
            <List
              dataSource={stats.recentActivities}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      item.status === 'success' ? 
                        <CheckCircleOutlined style={{ color: '#52c41a' }} /> :
                        <ClockCircleOutlined style={{ color: '#1890ff' }} />
                    }
                    title={item.title}
                    description={item.description}
                  />
                </List.Item>
              )}
              locale={{ emptyText: '暂无活动记录' }}
            />
          </Card>
        </Col>

        {/* 系统状态 */}
        <Col xs={24} lg={12}>
          {renderSystemStatus()}
        </Col>
      </Row>

      {/* 快速操作 */}
      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title="快速操作">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={8}>
                <Card 
                  hoverable 
                  onClick={() => window.history.pushState(null, '', '/intents')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <BulbOutlined style={{ fontSize: 32, color: '#1890ff', marginBottom: 16 }} />
                  <div>
                    <Title level={4}>管理意图</Title>
                    <Text type="secondary">创建和编辑训练意图</Text>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card 
                  hoverable 
                  onClick={() => window.history.pushState(null, '', '/training')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <RobotOutlined style={{ fontSize: 32, color: '#52c41a', marginBottom: 16 }} />
                  <div>
                    <Title level={4}>训练模型</Title>
                    <Text type="secondary">开始新的模型训练</Text>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card 
                  hoverable 
                  onClick={() => window.history.pushState(null, '', '/testing')}
                  style={{ textAlign: 'center', cursor: 'pointer' }}
                >
                  <ApiOutlined style={{ fontSize: 32, color: '#722ed1', marginBottom: 16 }} />
                  <div>
                    <Title level={4}>测试模型</Title>
                    <Text type="secondary">验证模型性能</Text>
                  </div>
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;

