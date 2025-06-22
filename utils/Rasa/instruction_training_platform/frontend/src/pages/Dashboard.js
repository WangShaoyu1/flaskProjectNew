import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, List, Typography, Spin, Alert, Modal, Table, Tag, Collapse, Input } from 'antd';
import { 
  BulbOutlined, 
  RobotOutlined, 
  CheckCircleOutlined, 
  ClockCircleOutlined,
  TrophyOutlined,
  ApiOutlined,
  EyeOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { intentAPI, toolsAPI, rasaAPI } from '../api';
import CustomLoading from '../components/CustomLoading';

const { Title, Text } = Typography;

const Dashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalIntents: 0,
    totalUtterances: 0,
    totalModels: 0,
    activeModel: null,
    recentActivities: []
  });
  const [systemInfo, setSystemInfo] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [detailModalData, setDetailModalData] = useState({ type: '', title: '', data: [], loading: false });
  const [searchText, setSearchText] = useState('');
  const [filteredData, setFilteredData] = useState([]);
  
  // 添加分页状态管理
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 5,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['5', '10', '20', '50']
  });

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // 并行加载数据
      const [intentsRes, utterancesRes, modelsRes, systemRes] = await Promise.allSettled([
        intentAPI.getIntents(),
        intentAPI.getAllUtterances(), // 使用新的接口获取所有相似问
        toolsAPI.getModels({ limit: 10 }),
        toolsAPI.getSystemInfo()
      ]);

      // 处理意图数据
      if (intentsRes.status === 'fulfilled' && intentsRes.value?.data) {
        const intents = intentsRes.value.data;
        setStats(prev => ({
          ...prev,
          totalIntents: intents.length
        }));
      } else {
        // 设置默认值或模拟数据
        setStats(prev => ({
          ...prev,
          totalIntents: 0
        }));
      }

      // 处理相似问数据
      if (utterancesRes.status === 'fulfilled' && utterancesRes.value?.data) {
        const allUtterances = utterancesRes.value.data;
        setStats(prev => ({
          ...prev,
          totalUtterances: allUtterances.length
        }));
      } else {
        setStats(prev => ({
          ...prev,
          totalUtterances: 0
        }));
      }

      // 处理模型数据
      if (modelsRes.status === 'fulfilled' && modelsRes.value?.data) {
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
      } else {
        // 如果API调用失败，设置空数据而不是默认数据
        setStats(prev => ({
          ...prev,
          totalModels: 0,
          activeModel: null,
          recentActivities: []
        }));
      }

      // 处理系统信息
      if (systemRes.status === 'fulfilled' && systemRes.value?.data) {
        setSystemInfo(systemRes.value.data);
      } else {
        // 设置默认系统信息
        setSystemInfo({
          cpu_count: navigator.hardwareConcurrency || 8,
          memory_total: 16 * 1024 * 1024 * 1024, // 16GB
          memory_available: 8 * 1024 * 1024 * 1024, // 8GB available
          memory_usage: 50,
          gpu_available: false,
          gpu_count: 0
        });
      }

    } catch (error) {
      console.error('加载仪表板数据失败:', error);
      // 只有在完全失败时才设置默认数据，并使用实际的API数据
      try {
        // 尝试单独加载模型数据
        const modelsRes = await toolsAPI.getModels({ limit: 10 });
        const models = modelsRes.data || [];
        const activeModel = models.find(model => model.is_active);
        
        // 尝试单独加载相似问数据
        const utterancesRes = await intentAPI.getAllUtterances();
        const totalUtterances = utterancesRes.data?.length || 0;
        
        setStats({
          totalIntents: 0,
          totalUtterances,
          totalModels: models.length, // 使用实际的模型数量
          activeModel,
          recentActivities: models.slice(0, 5).map(model => ({
            title: `模型 ${model.version}`,
            description: `训练时间: ${new Date(model.training_time).toLocaleString()}`,
            status: model.status,
            time: model.training_time
          }))
        });
      } catch (modelError) {
        // 如果连模型数据都无法获取，则设置为0
        setStats({
          totalIntents: 0,
          totalUtterances: 0,
          totalModels: 0,
          activeModel: null,
          recentActivities: []
        });
      }
      
      setSystemInfo({
        cpu_count: navigator.hardwareConcurrency || 8,
        memory_total: 16 * 1024 * 1024 * 1024,
        memory_available: 8 * 1024 * 1024 * 1024,
        memory_usage: 50,
        gpu_available: false,
        gpu_count: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const renderSystemStatus = () => {
    // 使用默认值确保总是有数据显示
    const systemData = systemInfo || {
      cpu_count: navigator.hardwareConcurrency || 8,
      memory_total: 16 * 1024 * 1024 * 1024,
      memory_available: 8 * 1024 * 1024 * 1024,
      memory_usage: 50,
      gpu_available: false,
      gpu_count: 0
    };

    // 计算内存使用率 - 修复NaN问题
    let memoryUsage = 0;
    if (systemData.memory_total && systemData.memory_available) {
      memoryUsage = ((systemData.memory_total - systemData.memory_available) / systemData.memory_total * 100).toFixed(1);
    } else if (systemData.memory_usage) {
      memoryUsage = parseFloat(systemData.memory_usage).toFixed(1);
    } else {
      memoryUsage = 50; // 默认值
    }

    // CPU核心数 - 修复显示为0的问题
    const cpuCount = systemData.cpu_count || systemData.cpu_cores || navigator.hardwareConcurrency || 8;
    
    return (
      <Card title="系统状态" style={{ height: '100%' }}>
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Statistic
              title="CPU 核心数"
              value={cpuCount}
              suffix={typeof cpuCount === 'number' ? '核' : ''}
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
              percent={parseFloat(memoryUsage) || 0} 
              status={memoryUsage > 80 ? 'exception' : 'normal'}
              format={percent => `${percent}%`}
            />
          </Col>
          <Col span={24}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>GPU 状态</Text>
            </div>
            {systemData.gpu_available ? (
              <Alert
                message="GPU 可用"
                description={`检测到 ${systemData.gpu_devices?.length || systemData.gpu_count || 1} 个 GPU 设备`}
                type="success"
                showIcon
              />
            ) : (
              <Alert
                message="GPU 不可用"
                description="未检测到可用的 GPU 设备，将使用 CPU 进行训练"
                type="warning"
                showIcon
              />
            )}
          </Col>
        </Row>
      </Card>
    );
  };

  // 显示详情弹窗
  const showDetailModal = async (type) => {
    // 先显示弹窗，然后在弹窗内加载数据
    setDetailModalData({ type, title: '加载中...', data: [], loading: true });
    setDetailModalVisible(true);
    
    // 重置搜索和分页状态
    setSearchText('');
    setPagination(prev => ({ ...prev, current: 1 }));
    
    try {
      let data = [];
      let title = '';
      
      switch (type) {
        case 'intents':
          const intentsRes = await intentAPI.getIntents();
          data = intentsRes.data || [];
          title = '意图详情列表';
          break;
        case 'utterances':
          // 使用新的一次性获取所有相似问的接口
          const allUtterancesRes = await intentAPI.getAllUtterances();
          const allUtterances = allUtterancesRes.data || [];
          
          // 按意图分组
          const groupedData = {};
          allUtterances.forEach(utterance => {
            const intentName = utterance.intent_name;
            if (!groupedData[intentName]) {
              groupedData[intentName] = {
                intent_id: utterance.intent_id,
                intent_name: intentName,
                intent_description: utterance.intent_description,
                utterances: []
              };
            }
            groupedData[intentName].utterances.push(utterance);
          });
          
          data = Object.values(groupedData);
          title = '相似问详情列表';
          break;
        case 'models':
          const modelsRes = await toolsAPI.getModels();
          data = modelsRes.data || [];
          title = '模型详情列表';
          break;
        default:
          break;
      }
      
      setDetailModalData({ type, title, data, loading: false });
      setFilteredData(data); // 初始化过滤数据
    } catch (error) {
      console.error('获取详情数据失败:', error);
      setDetailModalData({ type, title: '加载失败', data: [], loading: false });
      setFilteredData([]);
    }
  };

  // 搜索过滤函数
  const handleSearch = (value) => {
    setSearchText(value);
    
    // 重置分页到第一页
    setPagination(prev => ({ ...prev, current: 1 }));
    
    if (!value.trim()) {
      setFilteredData(detailModalData.data);
      return;
    }

    const { type, data } = detailModalData;
    if (type === 'utterances') {
      // 相似问搜索：搜索意图名称、描述和相似问内容
      const filtered = data.filter(intentGroup => {
        // 搜索意图名称和描述
        const intentMatch = 
          intentGroup.intent_name.toLowerCase().includes(value.toLowerCase()) ||
          (intentGroup.intent_description && intentGroup.intent_description.toLowerCase().includes(value.toLowerCase()));
        
        // 搜索相似问内容
        const utteranceMatch = intentGroup.utterances.some(utterance =>
          utterance.text.toLowerCase().includes(value.toLowerCase())
        );

        return intentMatch || utteranceMatch;
      }).map(intentGroup => {
        // 如果匹配的是相似问内容，则高亮显示匹配的相似问
        const filteredUtterances = intentGroup.utterances.filter(utterance =>
          utterance.text.toLowerCase().includes(value.toLowerCase())
        );

        // 如果意图名称或描述匹配，显示所有相似问；否则只显示匹配的相似问
        const shouldShowAll = 
          intentGroup.intent_name.toLowerCase().includes(value.toLowerCase()) ||
          (intentGroup.intent_description && intentGroup.intent_description.toLowerCase().includes(value.toLowerCase()));

        return {
          ...intentGroup,
          utterances: shouldShowAll ? intentGroup.utterances : filteredUtterances
        };
      });
      
      setFilteredData(filtered);
    } else if (type === 'intents') {
      // 意图搜索：搜索意图名称和意图编码
      const filtered = data.filter(item => {
        const matchName = item.description?.toLowerCase().includes(value.toLowerCase());
        const matchCode = item.intent_name?.toLowerCase().includes(value.toLowerCase());
        return matchName || matchCode;
      });
      setFilteredData(filtered);
    } else {
      // 其他类型的搜索保持原有逻辑
      const filtered = data.filter(item => {
        return Object.values(item).some(val => 
          val && val.toString().toLowerCase().includes(value.toLowerCase())
        );
      });
      setFilteredData(filtered);
    }
  };

  // 渲染详情表格
  const renderDetailTable = () => {
    const { type } = detailModalData;
    const data = filteredData; // 使用过滤后的数据
    
    if (type === 'utterances') {
      // 专门为相似问设计的分组展示
      return (
        <div>
          {data.map((intentGroup, index) => (
            <Card 
              key={intentGroup.intent_id} 
              style={{ marginBottom: 16 }}
              size="small"
            >
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                padding: '8px 0'
              }}>
                <div>
                  <Text strong style={{ fontSize: 16, color: '#1890ff' }}>
                    {intentGroup.intent_name}
                  </Text>
                  {intentGroup.intent_description && (
                    <div style={{ marginTop: 4 }}>
                      <Text type="secondary" style={{ fontSize: 13 }}>
                        {intentGroup.intent_description}
                      </Text>
                    </div>
                  )}
                </div>
                <Tag color="blue">
                  {intentGroup.utterances.length} 个相似问
                </Tag>
              </div>
              
              <Collapse 
                ghost 
                size="small"
                items={[
                  {
                    key: intentGroup.intent_id,
                    label: (
                      <Text style={{ color: '#666' }}>
                        展开查看相似问内容
                      </Text>
                    ),
                    children: (
                      <div style={{ 
                        maxHeight: 300, 
                        overflowY: 'auto',
                        padding: '8px 0'
                      }}>
                        {intentGroup.utterances.map((utterance, idx) => (
                          <div 
                            key={utterance.id}
                            style={{ 
                              padding: '6px 12px',
                              margin: '4px 0',
                              backgroundColor: '#f8f9fa',
                              borderRadius: '4px',
                              borderLeft: '3px solid #1890ff'
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <Text style={{ flex: 1 }}>
                                {utterance.text}
                              </Text>
                              <Text type="secondary" style={{ fontSize: 12, marginLeft: 12 }}>
                                #{idx + 1}
                              </Text>
                            </div>
                            {utterance.entities && utterance.entities !== '[]' && utterance.entities !== '' && (
                              <div style={{ marginTop: 4 }}>
                                <Text type="secondary" style={{ fontSize: 11 }}>
                                  实体: {utterance.entities}
                                </Text>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )
                  }
                ]}
              />
            </Card>
          ))}
          
          {data.length === 0 && (
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Text type="secondary">暂无相似问数据</Text>
            </div>
          )}
        </div>
      );
    }
    
    // 其他类型的表格展示保持原样
    let columns = [];
    switch (type) {
      case 'intents':
        columns = [
          { title: '意图名称', dataIndex: 'description', key: 'description' },
          { title: '意图编码', dataIndex: 'intent_name', key: 'intent_name' },
          { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
          { 
            title: '创建时间', 
            dataIndex: 'created_at', 
            key: 'created_at',
            render: (text) => text ? new Date(text).toLocaleString() : '-'
          }
        ];
        break;
      case 'models':
        columns = [
          { title: '模型版本', dataIndex: 'version', key: 'version' },
          { 
            title: '状态', 
            dataIndex: 'status', 
            key: 'status',
            render: (status) => (
              <Tag color={status === 'success' ? 'green' : status === 'training' ? 'blue' : 'red'}>
                {status === 'success' ? '成功' : status === 'training' ? '训练中' : '失败'}
              </Tag>
            )
          },
          { 
            title: '是否激活', 
            dataIndex: 'is_active', 
            key: 'is_active',
            render: (isActive) => (
              <Tag color={isActive ? 'green' : 'default'}>
                {isActive ? '已激活' : '未激活'}
              </Tag>
            )
          },
          { 
            title: '训练时间', 
            dataIndex: 'training_time', 
            key: 'training_time',
            render: (text) => text ? new Date(text).toLocaleString() : '-'
          }
        ];
        break;
      default:
        break;
    }

    return (
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        scroll={undefined} // 移除固定的滚动条设置，让表格根据内容自适应
        pagination={{
          ...pagination,
          total: data.length,
          showTotal: (total) => `共 ${total} 条记录`,
          onChange: (page, pageSize) => {
            setPagination(prev => ({ ...prev, current: page, pageSize }));
          },
          onShowSizeChange: (current, size) => {
            setPagination(prev => ({ ...prev, current: 1, pageSize: size }));
          }
        }}
      />
    );
  };

  if (loading) {
    return (
      <CustomLoading 
        visible={loading} 
        text="正在加载仪表板数据" 
        description="正在获取最新的统计信息..."
        size="large"
      />
    );
  }

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => showDetailModal('intents')} style={{ cursor: 'pointer' }}>
            <Statistic
              title={
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  总意图数
                  <EyeOutlined style={{ color: '#999', fontSize: 14 }} />
                </div>
              }
              value={stats.totalIntents}
              prefix={<BulbOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => showDetailModal('utterances')} style={{ cursor: 'pointer' }}>
            <Statistic
              title={
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  总相似问数
                  <EyeOutlined style={{ color: '#999', fontSize: 14 }} />
                </div>
              }
              value={stats.totalUtterances}
              prefix={<ApiOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => showDetailModal('models')} style={{ cursor: 'pointer' }}>
            <Statistic
              title={
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  模型总数
                  <EyeOutlined style={{ color: '#999', fontSize: 14 }} />
                </div>
              }
              value={stats.totalModels}
              prefix={<RobotOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable onClick={() => showDetailModal('models')} style={{ cursor: 'pointer' }}>
            <Statistic
              title={
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  当前模型
                  <EyeOutlined style={{ color: '#999', fontSize: 14 }} />
                </div>
              }
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
            {stats.recentActivities && stats.recentActivities.length > 0 ? (
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
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '60px 0', color: '#999' }}>
                <ClockCircleOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>暂无活动记录</div>
                <div style={{ fontSize: 12, marginTop: 8 }}>开始训练模型后这里将显示最近的活动</div>
              </div>
            )}
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
                  onClick={() => navigate('/intents')}
                  style={{ 
                    textAlign: 'center', 
                    cursor: 'pointer',
                    minHeight: 140,
                    background: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
                    color: '#2c3e50',
                    border: 'none',
                    boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)'
                  }}
                  styles={{ body: { padding: '24px 16px' } }}
                >
                  <BulbOutlined style={{ fontSize: 40, color: '#3498db', marginBottom: 12 }} />
                  <div>
                    <Title level={4} style={{ color: '#2c3e50', marginBottom: 8 }}>管理意图</Title>
                    <Text style={{ color: '#34495e', opacity: 0.8 }}>创建和编辑训练意图</Text>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card 
                  hoverable 
                  onClick={() => navigate('/training')}
                  style={{ 
                    textAlign: 'center', 
                    cursor: 'pointer',
                    minHeight: 140,
                    background: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
                    color: '#2c3e50',
                    border: 'none',
                    boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)'
                  }}
                  styles={{ body: { padding: '24px 16px' } }}
                >
                  <RobotOutlined style={{ fontSize: 40, color: '#e67e22', marginBottom: 12 }} />
                  <div>
                    <Title level={4} style={{ color: '#2c3e50', marginBottom: 8 }}>训练模型</Title>
                    <Text style={{ color: '#34495e', opacity: 0.8 }}>开始新的模型训练</Text>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card 
                  hoverable 
                  onClick={() => navigate('/testing')}
                  style={{ 
                    textAlign: 'center', 
                    cursor: 'pointer',
                    minHeight: 140,
                    background: 'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)',
                    color: '#2c3e50',
                    border: 'none',
                    boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)'
                  }}
                  styles={{ body: { padding: '24px 16px' } }}
                >
                  <ApiOutlined style={{ fontSize: 40, color: '#9b59b6', marginBottom: 12 }} />
                  <div>
                    <Title level={4} style={{ color: '#2c3e50', marginBottom: 8 }}>测试模型</Title>
                    <Text style={{ color: '#34495e', opacity: 0.8 }}>验证模型性能</Text>
                  </div>
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* 详情弹窗 */}
      <Modal
        title={detailModalData.title}
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setSearchText('');
          setFilteredData([]);
          setPagination(prev => ({ ...prev, current: 1 }));
        }}
        footer={null}
        width={900}
        destroyOnClose
        style={{ top: 60 }}
        styles={{ 
          body: {
            maxHeight: 'calc(100vh - 200px)', 
            overflowY: 'auto',
            padding: '16px 24px'
          }
        }}
      >
        {detailModalData.loading ? (
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center',
            minHeight: '500px', // 固定最小高度，与内容区域一致
            padding: '40px 0'
          }}>
            <div style={{
              width: 40,
              height: 40,
              border: '3px solid #f3f3f3',
              borderTop: '3px solid #1890ff',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              marginBottom: 16
            }} />
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: '#1890ff', marginBottom: 8 }}>
                正在加载详情数据...
              </div>
              <div style={{ fontSize: 14, color: '#666' }}>
                请稍候，正在获取最新数据
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* 搜索框 - 在意图详情和相似问详情时都显示 */}
            {(detailModalData.type === 'utterances' || detailModalData.type === 'intents') && (
              <div style={{ marginBottom: 16 }}>
                <Input.Search
                  placeholder={
                    detailModalData.type === 'intents' 
                      ? "搜索意图名称、意图编码..." 
                      : "搜索意图名称、描述或相似问内容..."
                  }
                  allowClear
                  enterButton={<SearchOutlined />}
                  size="large"
                  value={searchText}
                  onChange={(e) => handleSearch(e.target.value)}
                  onSearch={handleSearch}
                  style={{ width: '100%' }}
                />
                {searchText && (
                  <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
                    找到 {filteredData.length} 个匹配的{detailModalData.type === 'intents' ? '意图' : '意图组'}
                  </div>
                )}
              </div>
            )}
            
            {/* 内容区域 */}
            <div style={{ 
              maxHeight: detailModalData.type === 'utterances' ? '500px' : '600px', 
              overflowY: 'auto',
              paddingRight: '8px'
            }}>
              {renderDetailTable()}
            </div>
          </>
        )}
      </Modal>
    </div>
  );
};

export default Dashboard;

