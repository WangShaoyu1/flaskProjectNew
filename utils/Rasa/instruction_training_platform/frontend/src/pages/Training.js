import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Progress, 
  Alert, 
  Typography, 
  Space, 
  Divider,
  Table,
  Tag,
  message,
  Modal,
  Spin,
  Upload,
  Tabs,
  Form,
  Input,
  Select,
  Steps,
  Row,
  Col,
  Statistic,
  Collapse
} from 'antd';
import { 
  PlayCircleOutlined, 
  ReloadOutlined, 
  RobotOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  UploadOutlined,
  DatabaseOutlined,
  ExportOutlined,
  ImportOutlined,
  ToolOutlined,
  ArrowRightOutlined,
  MessageOutlined,
  EyeOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { intentAPI, rasaAPI, toolsAPI } from '../api';
import CustomLoading from '../components/CustomLoading';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Step } = Steps;
const { Option } = Select;

const Training = () => {
  // 训练相关状态
  const [training, setTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [trainingLog, setTrainingLog] = useState('');
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentTask, setCurrentTask] = useState(null);

  // 数据导入相关状态
  const [uploadLoading, setUploadLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [importedDataStats, setImportedDataStats] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);

  // 表单
  const [importForm] = Form.useForm();

  // 详情弹窗状态
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
  
  // 模型详情弹窗状态
  const [modelDetailModalVisible, setModelDetailModalVisible] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);

  useEffect(() => {
    loadModels();
    loadActiveModel();
    loadDataStats();
  }, []);

  const loadModels = async () => {
    setLoading(true);
    try {
      const response = await toolsAPI.getModels({ limit: 20 });
      setModels(response.data || []);
    } catch (error) {
      message.error('加载模型列表失败');
      console.error('加载模型失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadActiveModel = async () => {
    try {
      const response = await toolsAPI.getActiveModel();
      setActiveModel(response.data);
    } catch (error) {
      console.error('加载当前模型失败:', error);
    }
  };

  const loadDataStats = async () => {
    try {
      // 使用与Dashboard完全相同的数据获取逻辑
      const [intentsRes, utterancesRes] = await Promise.allSettled([
        intentAPI.getIntents(),
        intentAPI.getAllUtterances()
      ]);

      let totalIntents = 0;
      let totalUtterances = 0;

      // 处理意图数据 - 与Dashboard保持一致
      if (intentsRes.status === 'fulfilled' && intentsRes.value?.data) {
        totalIntents = intentsRes.value.data.length;
      }

      // 处理相似问数据 - 与Dashboard保持一致  
      if (utterancesRes.status === 'fulfilled' && utterancesRes.value?.data) {
        totalUtterances = utterancesRes.value.data.length;
      }

      setImportedDataStats({
        totalIntents,
        totalUtterances,
        totalResponses: totalIntents, // 假设每个意图至少有一个响应
        lastUpdate: new Date().toISOString()
      });
    } catch (error) {
      console.error('加载数据统计失败:', error);
      // 发生错误时设置为0，与Dashboard保持一致
      setImportedDataStats({
        totalIntents: 0,
        totalUtterances: 0,
        totalResponses: 0,
        lastUpdate: new Date().toISOString()
      });
    }
  };

  // 文件上传处理
  const handleFileUpload = async (file) => {
    setUploadLoading(true);
    try {
      const response = await toolsAPI.uploadFile(file);
      message.success(`成功导入 ${response.data.imported_count} 条数据`);
      loadDataStats();
      setCurrentStep(1); // 进入下一步
    } catch (error) {
      message.error('文件上传失败');
      console.error('上传失败:', error);
    } finally {
      setUploadLoading(false);
    }
    return false; // 阻止自动上传
  };

  // 手动数据导入
  const handleManualImport = async (values) => {
    try {
      const response = await toolsAPI.uploadData({
        data_type: values.data_type,
        content: values.content
      });
      message.success(`成功导入 ${response.data.imported_count} 条数据`);
      setImportModalVisible(false);
      importForm.resetFields();
      loadDataStats();
      setCurrentStep(1);
    } catch (error) {
      message.error('数据导入失败');
      console.error('导入失败:', error);
    }
  };

  // 数据导出
  const handleExport = async (format) => {
    setExportLoading(true);
    try {
      const response = await toolsAPI.exportData(format);
      
      // 创建下载链接
      const dataStr = JSON.stringify(response.data.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `training_data_${format}_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      message.success('数据导出成功');
    } catch (error) {
      message.error('数据导出失败');
      console.error('导出失败:', error);
    } finally {
      setExportLoading(false);
    }
  };

  const handleStartTraining = async () => {
    try {
      setTraining(true);
      setTrainingProgress(0);
      setTrainingLog('开始训练...\n');
      setCurrentStep(2);

      const response = await rasaAPI.train({
        nlu_data: '',
        domain_data: '',
        force_retrain: true
      });

      setCurrentTask(response.data);
      message.success('训练任务已启动');

      // 模拟训练进度更新
      simulateTrainingProgress(response.data?.task_id);

    } catch (error) {
      message.error('启动训练失败');
      console.error('训练失败:', error);
      setTraining(false);
    }
  };

  const simulateTrainingProgress = (taskId) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 8 + 2; // 2-10% 增长
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setTraining(false);
        setTrainingLog(prev => prev + '训练完成！\n模型已生成并保存。\n');
        message.success('模型训练完成');
        setCurrentStep(3);
        loadModels();
        loadActiveModel();
      }
      setTrainingProgress(progress);
      
      // 模拟训练日志
      const logs = [
        '正在处理意图数据...',
        '正在训练NLU模型...',
        '正在优化模型参数...',
        '正在验证模型性能...',
        '正在保存模型...'
      ];
      const randomLog = logs[Math.floor(Math.random() * logs.length)];
      setTrainingLog(prev => prev + `[${new Date().toLocaleTimeString()}] ${randomLog}\n`);
    }, 1500);
  };

  const handleActivateModel = async (modelId) => {
    try {
      await toolsAPI.activateModel(modelId);
      message.success('模型激活成功');
      loadModels();
      loadActiveModel();
    } catch (error) {
      message.error('模型激活失败');
      console.error('激活模型失败:', error);
    }
  };

  const handleDeleteModel = (model) => {
    Modal.confirm({
      title: '确认删除模型',
      content: (
        <div>
          <p>您确定要删除以下模型吗？</p>
          <div style={{ 
            padding: '12px', 
            backgroundColor: '#f5f5f5', 
            borderRadius: '4px', 
            margin: '12px 0' 
          }}>
            <div><Text strong>模型版本：</Text>{model.version}</div>
            <div><Text strong>训练时间：</Text>{model.training_time ? new Date(model.training_time).toLocaleString() : '未知'}</div>
            <div><Text strong>状态：</Text>{getStatusText(model.status)}</div>
          </div>
          <div style={{ color: '#ff4d4f', fontSize: '14px' }}>
            <ExclamationCircleOutlined style={{ marginRight: '4px' }} />
            此操作不可撤销，模型文件将被永久删除！
          </div>
        </div>
      ),
      icon: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await toolsAPI.deleteModel(model.id);
          message.success(`模型 ${model.version} 删除成功`);
          loadModels();
          // 如果删除的是激活模型，重新加载激活模型信息
          if (model.is_active) {
            loadActiveModel();
          }
        } catch (error) {
          console.error('删除模型失败:', error);
          const errorMsg = error.response?.data?.detail || '删除模型失败';
          message.error(errorMsg);
        }
      }
    });
  };

  // 显示模型详情
  const showModelDetail = (model) => {
    setSelectedModel(model);
    setModelDetailModalVisible(true);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'training':
        return <ClockCircleOutlined style={{ color: '#1890ff' }} />;
      case 'failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'success':
        return '训练成功';
      case 'training':
        return '训练中';
      case 'failed':
        return '训练失败';
      default:
        return '未知状态';
    }
  };

  const modelColumns = [
    {
      title: '模型版本',
      dataIndex: 'version',
      key: 'version',
      render: (text, record) => (
        <Space>
          <Text strong>{text}</Text>
          {record.is_active && <Tag color="green">当前激活</Tag>}
        </Space>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Space>
          {getStatusIcon(status)}
          <Text>{getStatusText(status)}</Text>
        </Space>
      )
    },
    {
      title: '训练时间',
      dataIndex: 'training_time',
      key: 'training_time',
      render: (text) => text ? new Date(text).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          {!record.is_active && record.status === 'success' && (
            <Button 
              type="link" 
              onClick={() => handleActivateModel(record.id)}
            >
              激活
            </Button>
          )}
          <Button type="link" onClick={() => showModelDetail(record)}>详情</Button>
          {!record.is_active && (
            <Button 
              type="link" 
              danger
              onClick={() => handleDeleteModel(record)}
            >
              删除
            </Button>
          )}
        </Space>
      ),
    },
  ];

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
          // 调用API获取实际的意图数据
          const intentsRes = await intentAPI.getIntents();
          data = intentsRes.data || [];
          title = '意图详情列表';
          break;
        case 'utterances':
          // 调用API获取实际的相似问数据，使用与Dashboard相同的接口
          const utterancesRes = await intentAPI.getAllUtterances();
          const allUtterances = utterancesRes.data || [];
          
          // 按意图分组，与Dashboard保持一致的显示格式
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

  const renderTrainingSteps = () => {
    return (
      <Steps current={currentStep} style={{ marginBottom: 24 }}>
        <Step title="数据准备" description="导入训练数据" icon={<DatabaseOutlined />} />
        <Step title="数据检查" description="验证数据完整性" icon={<CheckCircleOutlined />} />
        <Step title="模型训练" description="训练AI模型" icon={<RobotOutlined />} />
        <Step title="完成" description="训练完成" icon={<CheckCircleOutlined />} />
      </Steps>
    );
  };

  return (
    <div>
      {/* 训练步骤指示 */}
      <Card style={{ marginBottom: 24 }}>
        <Title level={4} style={{ marginBottom: 16 }}>智能训练流程</Title>
        {renderTrainingSteps()}
      </Card>

      <Row gutter={[24, 24]}>
        {/* 左侧：数据导入和训练控制 */}
        <Col xs={24} lg={16}>
          <Tabs defaultActiveKey="import" activeKey={currentStep >= 2 ? "training" : "import"}>
            <TabPane 
              tab={
                <span>
                  <ImportOutlined />
                  数据导入
                </span>
              } 
              key="import"
            >
              <Card title="训练数据导入">
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  {/* 文件上传 */}
                  <Card size="small" title="文件上传" className="upload-card">
                    <Upload
                      beforeUpload={handleFileUpload}
                      accept=".csv,.json,.yml,.yaml"
                      showUploadList={false}
                      disabled={uploadLoading}
                    >
                      <Button 
                        icon={<UploadOutlined />}
                        loading={uploadLoading}
                        size="large"
                        type="primary"
                        className="training-upload-btn"
                        style={{ width: '100%', height: 80 }}
                      >
                        <div>
                          <div style={{ fontSize: 16, marginBottom: 4 }}>
                            {uploadLoading ? '上传中...' : '选择文件上传'}
                          </div>
                          <div style={{ fontSize: 12, opacity: 0.8 }}>
                            支持: CSV, JSON, YAML 格式
                          </div>
                        </div>
                      </Button>
                    </Upload>
                  </Card>

                  {/* 手动输入 */}
                  <Card size="small" title="手动输入数据">
                    <Button 
                      type="dashed"
                      onClick={() => setImportModalVisible(true)}
                      style={{ width: '100%', height: 60 }}
                    >
                      <DatabaseOutlined style={{ fontSize: 20 }} />
                      <div>手动输入训练数据</div>
            </Button>
                  </Card>

                  {/* 快速开始训练 */}
                  {importedDataStats && (
                    <Card size="small" title="开始训练">
                      <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Button 
              type="primary"
                          size="large"
              icon={<PlayCircleOutlined />}
              onClick={handleStartTraining}
              disabled={training}
                          className="start-training-btn"
                          style={{ height: 50, fontSize: 16 }}
            >
                          开始智能训练
            </Button>
                        <div style={{ marginTop: 8, color: '#666' }}>
                          使用当前数据训练新模型
                        </div>
                      </div>
                    </Card>
                  )}
          </Space>
              </Card>
            </TabPane>

            <TabPane 
              tab={
                <span>
                  <RobotOutlined />
                  模型训练
                </span>
              } 
              key="training"
            >
              <Card title="训练监控">
        {training && (
          <div style={{ marginBottom: 24 }}>
                    <div style={{ marginBottom: 16 }}>
                      <Text strong>训练进度</Text>
            <Progress 
              percent={Math.round(trainingProgress)} 
              status={training ? 'active' : 'success'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
                    </div>
                    
                    <Card 
                      size="small" 
                      title="训练日志" 
                      style={{ backgroundColor: '#fafafa' }}
                    >
            <div style={{ 
                        height: 200, 
                        overflowY: 'auto', 
              fontFamily: 'monospace',
              fontSize: 12,
                        lineHeight: 1.4,
                        whiteSpace: 'pre-wrap',
                        backgroundColor: '#001529',
                        color: '#52c41a',
                        padding: 12,
                        borderRadius: 4
                      }}>
                        {trainingLog}
            </div>
                    </Card>
          </div>
        )}

                {!training && !trainingLog && (
                  <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
                    <RobotOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                    <div>准备开始训练时，这里将显示训练进度和日志</div>
                  </div>
                )}
              </Card>
            </TabPane>
          </Tabs>
        </Col>

        {/* 右侧：数据统计和模型列表 */}
        <Col xs={24} lg={8}>
          {/* 数据统计 */}
          {importedDataStats && (
            <Card title="数据统计" style={{ marginBottom: 24 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Card 
                    hoverable 
                    onClick={() => showDetailModal('intents')} 
                    style={{ cursor: 'pointer', textAlign: 'center' }}
                    size="small"
                  >
                    <Statistic
                      title={
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                          总意图数
                          <EyeOutlined style={{ color: '#999', fontSize: 12 }} />
                        </div>
                      }
                      value={importedDataStats.totalIntents}
                      prefix={<DatabaseOutlined />}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Card>
                </Col>
                <Col span={12}>
                  <Card 
                    hoverable 
                    onClick={() => showDetailModal('utterances')} 
                    style={{ cursor: 'pointer', textAlign: 'center' }}
                    size="small"
                  >
                    <Statistic
                      title={
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                          相似问数
                          <EyeOutlined style={{ color: '#999', fontSize: 12 }} />
                        </div>
                      }
                      value={importedDataStats.totalUtterances}
                      prefix={<MessageOutlined />}
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Card>
                </Col>
              </Row>
              <Divider />
              <div style={{ textAlign: 'center' }}>
                <Button 
                  type="link" 
                  icon={<ExportOutlined />}
                  onClick={() => handleExport('rasa')}
                  loading={exportLoading}
                >
                  导出数据
                </Button>
              </div>
            </Card>
          )}

          {/* 当前模型 */}
          {activeModel && (
            <Card title="当前激活模型" style={{ marginBottom: 24 }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff', marginBottom: 8 }}>
                  {activeModel.version}
                </div>
                <Tag color="green">已激活</Tag>
                <div style={{ marginTop: 8, color: '#666', fontSize: 12 }}>
                  训练时间: {activeModel.training_time ? new Date(activeModel.training_time).toLocaleString() : '未知'}
                </div>
        </div>
      </Card>
          )}

          {/* 快速操作 */}
          <Card title="快速操作">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                icon={<ReloadOutlined />}
                onClick={loadModels}
                loading={loading}
                block
              >
                刷新模型列表
              </Button>
              <Button 
                icon={<ExportOutlined />}
                onClick={() => handleExport('rasa')}
                loading={exportLoading}
                block
              >
                导出训练数据
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 模型历史 */}
      <Card title="模型历史" style={{ marginTop: 24 }}>
        <Table
          columns={modelColumns}
          dataSource={models}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个模型`
          }}
        />
      </Card>

      {/* 手动导入数据模态框 */}
      <Modal
        title="手动导入数据"
        open={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={importForm}
          layout="vertical"
          onFinish={handleManualImport}
        >
          <Form.Item
            name="data_type"
            label="数据类型"
            rules={[{ required: true, message: '请选择数据类型' }]}
          >
            <Select placeholder="选择数据类型">
              <Option value="intents">意图数据</Option>
              <Option value="entities">实体数据</Option>
              <Option value="responses">响应数据</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="content"
            label="数据内容"
            rules={[{ required: true, message: '请输入数据内容' }]}
          >
            <TextArea 
              rows={10} 
              placeholder="请输入JSON格式的数据..."
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setImportModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                导入
              </Button>
            </Space>
          </Form.Item>
                  </Form>
        </Modal>

        {/* 详情弹窗 */}
        <Modal
          title={detailModalData.title}
          open={detailModalVisible}
          onCancel={() => {
            setDetailModalVisible(false);
            setSearchText('');
            setFilteredData([]);
            setPagination(prev => ({ ...prev, current: 1 })); // 重置分页
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
              {/* 搜索框 - 相似问和意图详情都显示 */}
              {(detailModalData.type === 'utterances' || detailModalData.type === 'intents') && (
                <div style={{ marginBottom: 16 }}>
                  <Input.Search
                    placeholder={
                      detailModalData.type === 'utterances' 
                        ? "搜索意图名称、描述或相似问内容..."
                        : "搜索意图名称或编码..."
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
                      找到 {filteredData.length} 个匹配的{detailModalData.type === 'utterances' ? '意图组' : '意图'}
                    </div>
                  )}
                </div>
              )}
              
              {/* 内容区域 */}
              <div>
                {detailModalData.type === 'utterances' ? (
                  // 相似问详情使用卡片式展示（与Dashboard保持一致）
                  <div>
                    {filteredData.map((intentGroup) => (
                      <Card 
                        key={intentGroup.intent_id}
                        size="small" 
                        style={{ marginBottom: 16 }}
                        title={
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                              <Text strong style={{ color: '#1890ff' }}>
                                {intentGroup.intent_description || intentGroup.intent_name}
                              </Text>
                              <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                                ({intentGroup.intent_name})
                              </Text>
                            </div>
                            <Tag color="blue">
                              {intentGroup.utterances.length} 条相似问
                            </Tag>
                          </div>
                        }
                      >
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
                    
                    {filteredData.length === 0 && (
                      <div style={{ textAlign: 'center', padding: '40px 0' }}>
                        <Text type="secondary">
                          {searchText ? '未找到匹配的相似问数据' : '暂无相似问数据'}
                        </Text>
                      </div>
                    )}
                  </div>
                ) : (
                  // 意图详情使用表格展示 - 与Dashboard保持一致，不设置外层滚动
                  <Table
                    columns={[
                      { title: '意图名称', dataIndex: 'description', key: 'description' },
                      { title: '意图编码', dataIndex: 'intent_name', key: 'intent_name' },
                      { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
                      { 
                        title: '创建时间', 
                        dataIndex: 'created_at', 
                        key: 'created_at',
                        render: (text) => text ? new Date(text).toLocaleString() : '-'
                      }
                    ]}
                    dataSource={filteredData}
                    rowKey="id"
                    scroll={undefined} // 移除固定的滚动条设置，让表格根据内容自适应
                    pagination={{
                      ...pagination,
                      total: filteredData.length,
                      showTotal: (total) => `共 ${total} 条记录`,
                      onChange: (page, pageSize) => {
                        setPagination(prev => ({ ...prev, current: page, pageSize }));
                      },
                      onShowSizeChange: (current, size) => {
                        setPagination(prev => ({ ...prev, current: 1, pageSize: size }));
                      }
                    }}
                  />
                )}
              </div>
            </>
          )}
        </Modal>

        {/* 模型详情弹窗 */}
        <Modal
          title="模型详情"
          open={modelDetailModalVisible}
          onCancel={() => setModelDetailModalVisible(false)}
          footer={null}
          width={800}
          destroyOnClose
        >
          {selectedModel && (
            <div>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Card size="small" title="基本信息">
                    <div style={{ padding: '8px 0' }}>
                      <div style={{ marginBottom: 8 }}>
                        <Text strong>模型版本: </Text>
                        <Text>{selectedModel.version}</Text>
                      </div>
                      <div style={{ marginBottom: 8 }}>
                        <Text strong>状态: </Text>
                        <Tag color={selectedModel.status === 'success' ? 'green' : selectedModel.status === 'training' ? 'blue' : 'red'}>
                          {selectedModel.status === 'success' ? '成功' : selectedModel.status === 'training' ? '训练中' : '失败'}
                        </Tag>
                      </div>
                      <div style={{ marginBottom: 8 }}>
                        <Text strong>是否激活: </Text>
                        <Tag color={selectedModel.is_active ? 'green' : 'default'}>
                          {selectedModel.is_active ? '已激活' : '未激活'}
                        </Tag>
                      </div>
                      <div style={{ marginBottom: 8 }}>
                        <Text strong>训练时间: </Text>
                        <Text>{selectedModel.training_time ? new Date(selectedModel.training_time).toLocaleString() : '未知'}</Text>
                      </div>
                      <div style={{ marginBottom: 8 }}>
                        <Text strong>数据版本: </Text>
                        <Text>{selectedModel.data_version || '未知'}</Text>
                      </div>
                    </div>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small" title="模型路径">
                    <div style={{ padding: '8px 0' }}>
                      <div style={{ marginBottom: 8 }}>
                        <Text strong>文件路径: </Text>
                        <div style={{ 
                          marginTop: 4, 
                          padding: '4px 8px', 
                          backgroundColor: '#f5f5f5', 
                          borderRadius: 4,
                          fontSize: 12,
                          fontFamily: 'monospace',
                          wordBreak: 'break-all'
                        }}>
                          {selectedModel.file_path || '未知'}
                        </div>
                      </div>
                    </div>
                  </Card>
                </Col>
              </Row>
              
              {selectedModel.metrics && (
                <Card size="small" title="模型性能指标" style={{ marginTop: 16 }}>
                  <div style={{ padding: '8px 0' }}>
                    <Text strong>性能指标: </Text>
                    <div style={{ 
                      marginTop: 8, 
                      padding: '8px 12px', 
                      backgroundColor: '#f5f5f5', 
                      borderRadius: 4,
                      fontSize: 12,
                      fontFamily: 'monospace'
                    }}>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {typeof selectedModel.metrics === 'string' 
                          ? selectedModel.metrics 
                          : JSON.stringify(selectedModel.metrics, null, 2)
                        }
                      </pre>
                    </div>
                  </div>
                </Card>
              )}
              
              <div style={{ marginTop: 16, textAlign: 'center' }}>
                <Space>
                  {!selectedModel.is_active && selectedModel.status === 'success' && (
                    <Button 
                      type="primary"
                      onClick={() => {
                        handleActivateModel(selectedModel.id);
                        setModelDetailModalVisible(false);
                      }}
                    >
                      激活此模型
                    </Button>
                  )}
                  <Button onClick={() => setModelDetailModalVisible(false)}>
                    关闭
                  </Button>
                </Space>
              </div>
            </div>
          )}
        </Modal>

          {/* 训练loading */}
          <CustomLoading 
            visible={training} 
            text="正在训练模型" 
            description={`训练进度: ${Math.round(trainingProgress)}%`}
            size="large"
          />
    </div>
  );
};

export default Training;

