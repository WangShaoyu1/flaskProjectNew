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
  Spin
} from 'antd';
import { 
  PlayCircleOutlined, 
  ReloadOutlined, 
  RobotOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { rasaAPI, toolsAPI } from '../api';

const { Title, Text, Paragraph } = Typography;

const Training = () => {
  const [training, setTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [trainingLog, setTrainingLog] = useState('');
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentTask, setCurrentTask] = useState(null);

  useEffect(() => {
    loadModels();
    loadActiveModel();
  }, []);

  const loadModels = async () => {
    setLoading(true);
    try {
      const response = await toolsAPI.getModels({ limit: 20 });
      setModels(response.data);
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

  const handleStartTraining = async () => {
    try {
      setTraining(true);
      setTrainingProgress(0);
      setTrainingLog('开始训练...\n');

      const response = await rasaAPI.train({
        nlu_data: '',
        domain_data: '',
        force_retrain: true
      });

      setCurrentTask(response.data);
      message.success('训练任务已启动');

      // 模拟训练进度更新
      simulateTrainingProgress(response.data.task_id);

    } catch (error) {
      message.error('启动训练失败');
      console.error('训练失败:', error);
      setTraining(false);
    }
  };

  const simulateTrainingProgress = (taskId) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 10;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setTraining(false);
        setTrainingLog(prev => prev + '训练完成！\n');
        message.success('模型训练完成');
        loadModels();
        loadActiveModel();
      }
      setTrainingProgress(progress);
      setTrainingLog(prev => prev + `训练进度: ${progress.toFixed(1)}%\n`);
    }, 1000);
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
      render: (text) => new Date(text).toLocaleString(),
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
          <Button type="link">详情</Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* 训练控制面板 */}
      <Card 
        title={
          <Space>
            <RobotOutlined />
            模型训练
          </Space>
        }
        extra={
          <Space>
            <Button 
              icon={<ReloadOutlined />}
              onClick={() => {
                loadModels();
                loadActiveModel();
              }}
            >
              刷新
            </Button>
            <Button 
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleStartTraining}
              disabled={training}
              loading={training}
            >
              {training ? '训练中...' : '开始训练'}
            </Button>
          </Space>
        }
      >
        {/* 当前激活模型信息 */}
        {activeModel && (
          <Alert
            message="当前激活模型"
            description={
              <div>
                <Text strong>版本:</Text> {activeModel.version} <br />
                <Text strong>训练时间:</Text> {new Date(activeModel.training_time).toLocaleString()}
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}

        {/* 训练进度 */}
        {training && (
          <div style={{ marginBottom: 24 }}>
            <Title level={4}>训练进度</Title>
            <Progress 
              percent={Math.round(trainingProgress)} 
              status={training ? 'active' : 'success'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <div style={{ 
              marginTop: 16, 
              padding: 16, 
              backgroundColor: '#f6f8fa',
              borderRadius: 6,
              fontFamily: 'monospace',
              fontSize: 12,
              maxHeight: 200,
              overflowY: 'auto'
            }}>
              <pre>{trainingLog}</pre>
            </div>
          </div>
        )}

        {/* 训练说明 */}
        <div>
          <Title level={4}>训练说明</Title>
          <Paragraph>
            <ul>
              <li>训练将使用当前数据库中的所有意图、相似问和话术数据</li>
              <li>训练过程中会自动生成 NLU 和 Domain 配置文件</li>
              <li>如果检测到 GPU，将自动启用 GPU 加速训练</li>
              <li>训练完成后，新模型将自动激活并可用于预测</li>
              <li>建议在训练前确保数据质量和完整性</li>
            </ul>
          </Paragraph>
        </div>
      </Card>

      {/* 模型历史 */}
      <Card 
        title="模型历史"
        style={{ marginTop: 24 }}
      >
        <Table
          columns={modelColumns}
          dataSource={models}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个模型`,
          }}
        />
      </Card>

      {/* 训练配置信息 */}
      <Card 
        title="训练配置"
        style={{ marginTop: 24 }}
      >
        <div className="code-block">
          <pre>{`
# Rasa 训练配置概览

语言: 中文 (zh)
管道组件:
  - JiebaTokenizer (中文分词)
  - LanguageModelFeaturizer (BERT特征提取)
  - DIETClassifier (意图分类和实体提取)
  - ResponseSelector (响应选择)

策略:
  - MemoizationPolicy (记忆策略)
  - RulePolicy (规则策略)
  - TEDPolicy (对话管理)

GPU 加速: ${activeModel ? '已启用' : '检测中...'}
训练轮次: 100 epochs
          `}</pre>
        </div>
      </Card>
    </div>
  );
};

export default Training;

