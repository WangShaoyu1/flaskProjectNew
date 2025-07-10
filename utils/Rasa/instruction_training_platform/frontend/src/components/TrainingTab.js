import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Form, Input, message, Progress, Modal, Tabs,
  Row, Col, Statistic, Space, Tag, Alert, Steps, Timeline, Descriptions,
  Select, InputNumber, Switch, Divider, Tooltip
} from 'antd';
import {
  RobotOutlined, PlayCircleOutlined, 
  CheckCircleOutlined, ClockCircleOutlined,
  BarChartOutlined, FileTextOutlined, SettingOutlined,
  EyeOutlined, LineChartOutlined, ExclamationCircleOutlined,
  InfoCircleOutlined, WarningOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { formatLocalTime } from '../utils/timeUtils';
import { instructionAPI, slotAPI, trainingAPI } from '../api-v2';

const { Step } = Steps;

const TrainingTab = ({ currentLibrary }) => {
  const [loading, setLoading] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(null);
  const [trainingRecords, setTrainingRecords] = useState([]);
  const [currentTrainingId, setCurrentTrainingId] = useState(null);
  const [selectedLogRecordId, setSelectedLogRecordId] = useState(null);
  const [trainingSummary, setTrainingSummary] = useState(null);
  
  // 数据状态
  const [dataStats, setDataStats] = useState({
    instruction_count: 0,
    slot_count: 0,
    similar_question_count: 0,
    enabled_instruction_count: 0
  });
  
  // 模态框状态
  const [advancedConfigVisible, setAdvancedConfigVisible] = useState(false);
  const [trainingLogVisible, setTrainingLogVisible] = useState(false);
  const [performanceAnalysisVisible, setPerformanceAnalysisVisible] = useState(false);
  const [trainingLogs, setTrainingLogs] = useState([]);
  
  // 高级训练参数
  const [trainingParams, setTrainingParams] = useState({
    epochs: 5,
    batch_size: 32,
    learning_rate: 0.001,
    dropout_rate: 0.2,
    validation_split: 0.2,
    early_stopping: true,
    patience: 10,
    use_attention: true,
    embedding_dimension: 256,
    hidden_units: 128
  });
  
  const [form] = Form.useForm();

  // 获取训练数据统计
  const fetchDataStats = async () => {
    if (!currentLibrary) return;
    
    try {
      // 获取指令统计
      const instructionResponse = await instructionAPI.getInstructions({
        library_id: currentLibrary.id,
        skip: 0,
        limit: 9999
      });
      const instructionData = instructionResponse.data.data || instructionResponse.data;
      const instructions = instructionData.instructions || [];
      
      // 获取词槽统计
      const slotResponse = await slotAPI.getSlots({ library_id: currentLibrary.id });
      const slotData = slotResponse.data.data || slotResponse.data;
      const slots = slotData.slots || [];
      
      // 统计相似问数量
      const similarQuestionCount = instructions.reduce((total, inst) => {
        return total + (inst.similar_questions?.length || 0);
      }, 0);
      
      // 统计启用的指令数量
      const enabledInstructionCount = instructions.filter(inst => inst.is_enabled).length;
      
      setDataStats({
        instruction_count: instructions.length,
        slot_count: slots.length,
        similar_question_count: similarQuestionCount,
        enabled_instruction_count: enabledInstructionCount
      });
    } catch (error) {
      console.error('获取数据统计失败:', error);
    }
  };

  // 获取训练记录
  const fetchTrainingRecords = async () => {
    if (!currentLibrary) return;
    
    try {
      const response = await trainingAPI.getTrainingRecords({
        library_id: currentLibrary.id,
        skip: 0,
        limit: 20
      });
      const data = response.data.data || response.data;
      const records = data.records || [];
      setTrainingRecords(records);
      
      // 检查是否有正在进行的训练
      const activeTraining = records.find(record => 
        record.training_status === 'running' || record.training_status === 'pending'
      );
      
      if (activeTraining) {
        // 如果有正在进行的训练，设置currentTrainingId并开始监控
        if (currentTrainingId !== activeTraining.id) {
          console.log('🔍 [检测] 发现正在进行的训练:', activeTraining.id);
          setCurrentTrainingId(activeTraining.id);
          setTimeout(() => monitorTrainingProgress(activeTraining.id), 6000);
        }
      } else {
        // 如果没有正在进行的训练，清除currentTrainingId
        if (currentTrainingId) {
          console.log('🔍 [检测] 没有正在进行的训练，清除currentTrainingId');
          setCurrentTrainingId(null);
          setTrainingProgress(null);
        }
      }
    } catch (error) {
      console.error('获取训练记录失败:', error);
    }
  };

  // 获取训练汇总
  const fetchTrainingSummary = async () => {
    if (!currentLibrary) return;
    
    try {
      const response = await trainingAPI.getTrainingSummary(currentLibrary.id);
      const data = response.data.data || response.data;
      setTrainingSummary(data);
    } catch (error) {
      console.error('获取训练汇总失败:', error);
    }
  };

  // 监控训练进度
  const monitorTrainingProgress = async (trainingRecordId) => {
    try {
      const response = await trainingAPI.getTrainingStatus(trainingRecordId);
      const data = response.data.data || response.data;
      
      console.log('🔍 [监控] 获取到训练状态:', data);
      
      setTrainingProgress(data);
      
      // 修复状态字段名称不一致的问题
      const trainingStatus = data.training_status || data.status;
      const progress = data.progress || 0;
      
      // 如果训练还在进行中，继续监控
      if ((trainingStatus === 'running' || trainingStatus === 'pending') && progress < 100) {
        console.log(`🔄 [监控] 训练进行中，状态: ${trainingStatus}, 进度: ${progress}%, 2秒后继续监控`);
        setTimeout(() => monitorTrainingProgress(trainingRecordId), 6000);
      } else {
        console.log(`🏁 [监控] 训练结束，状态: ${trainingStatus}, 进度: ${progress}%`);
        
        // 训练完成，刷新记录
        setCurrentTrainingId(null);
        setTrainingProgress(null);
        fetchTrainingRecords();
        fetchTrainingSummary();
        
        if (trainingStatus === 'completed' || trainingStatus === 'success') {
          message.success('模型训练完成！');
        } else if (trainingStatus === 'failed') {
          message.error('模型训练失败，请查看日志了解详情');
        }
      }
    } catch (error) {
      console.error('❌ [监控] 获取训练进度失败:', error);
      
      // 如果是404错误，可能训练记录不存在，停止监控
      if (error.response?.status === 404) {
        console.warn('⚠️ [监控] 训练记录不存在，停止监控');
        setCurrentTrainingId(null);
        setTrainingProgress(null);
        message.warning('训练记录不存在，可能已被删除');
      } else {
        // 其他错误，等待3秒后重试
        console.warn('⚠️ [监控] 网络错误，3秒后重试');
        setTimeout(() => monitorTrainingProgress(trainingRecordId), 3000);
      }
    }
  };

  // 获取训练日志
  const fetchTrainingLogs = async (trainingRecordId) => {
    try {
      const response = await trainingAPI.getTrainingLogs(trainingRecordId);
      const data = response.data.data || response.data;
      setTrainingLogs(data.logs || []);
    } catch (error) {
      console.error('获取训练日志失败:', error);
    }
  };

  useEffect(() => {
    fetchDataStats();
    fetchTrainingRecords();
    fetchTrainingSummary();
  }, [currentLibrary]);

  // 检查是否选择了指令库
  if (!currentLibrary) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <RobotOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
          <h3>请先选择指令库</h3>
          <p style={{ color: '#666' }}>在开始模型训练之前，请先选择一个指令库。</p>
        </div>
      </Card>
    );
  }

  // 获取训练数据状态提示
  const getDataStatusAlert = () => {
    const { instruction_count, slot_count, enabled_instruction_count } = dataStats;
    
    // 检查训练条件
    const hasInstructions = instruction_count > 0;
    const hasMinimumInstructions = instruction_count >= 2;
    const hasEnabledInstructions = enabled_instruction_count > 0;
    const hasSlots = slot_count > 0;
    
    if (!hasInstructions) {
      return {
        type: 'error',
        icon: <ExclamationCircleOutlined />,
        message: '🚫 训练数据不足 - 当前无指令数据，请先到"指令管理"添加指令数据后再进行训练',
        description: null
      };
    }
    
    if (!hasMinimumInstructions) {
      return {
        type: 'warning',
        icon: <WarningOutlined />,
        message: `⚠️ 训练数据不足 - 当前仅有 ${instruction_count} 个指令，建议至少添加 2 个不同指令以获得更好的训练效果`,
        description: null
      };
    }
    
    if (!hasEnabledInstructions) {
      return {
        type: 'warning',
        icon: <WarningOutlined />,
        message: `⚠️ 无启用指令 - 当前有 ${instruction_count} 个指令但均未启用，请到"指令管理"启用指令后再训练`,
        description: null
      };
    }
    
    if (!hasSlots) {
      return {
        type: 'info',
        icon: <InfoCircleOutlined />,
        message: `✅ 训练数据就绪 - 指令数据完整（${enabled_instruction_count} 个启用指令），建议配置词槽数据以提升实体识别能力，现在可以开始训练`,
        description: null
      };
    }
    
    return {
      type: 'success',
      icon: <CheckCircleOutlined />,
      message: `🎯 训练数据完美 - 数据准备完成：${enabled_instruction_count} 个启用指令、${slot_count} 个词槽，训练条件已满足，可以开始高质量训练`,
      description: null
    };
  };

  // 处理训练
  const handleStartTraining = async () => {
    // 验证训练条件
    const alertConfig = getDataStatusAlert();
    if (alertConfig.type === 'error') {
      message.error('训练条件不满足，请先添加指令数据');
      return;
    }
    
    console.log('🚀 [训练] 开始训练函数被调用');
    console.log('📝 [训练] 训练参数:', trainingParams);
    
    // 防止重复点击
    if (loading || currentTrainingId) {
      console.warn('⚠️ [训练] 重复点击被阻止');
      message.warning('训练正在进行中，请勿重复点击');
      return;
    }
    
    setLoading(true);
    
    try {
      console.log('📤 [训练] 显示启动提示');
      message.loading('正在启动训练，请稍候...', 0);
      
      const response = await trainingAPI.startTraining({
        library_id: currentLibrary.id,
        training_params: trainingParams
      });
      
      const data = response.data.data || response.data;
      
      console.log('✅ [训练] API请求成功:', data);
      message.destroy(); // 清除loading消息
      
      if (data.training_record_id || data.training_record?.id) {
        const trainingId = data.training_record_id || data.training_record.id;
        message.success('训练已启动，正在准备数据...');
        setCurrentTrainingId(trainingId);
        
        console.log('🔍 [训练] 准备启动状态监控 - training_id:', trainingId);
        
        // 开始监控进度
        setTimeout(() => monitorTrainingProgress(trainingId), 6000);
      } else {
        console.warn('⚠️ [训练] 响应中未找到training_record_id');
        message.warning('训练启动成功，但无法获取训练ID');
      }
      
    } catch (error) {
      console.error('❌ [训练] 启动训练失败:', error);
      console.error('📄 [训练] 错误详情:', error.response?.data);
      
      message.destroy(); // 清除loading消息
      
      const errorMsg = error.response?.data?.message || error.message || '未知错误';
      message.error(`训练启动失败: ${errorMsg}`);
      
      // 如果是重复训练的错误，提供更友好的提示
      if (errorMsg.includes('正在进行中') || errorMsg.includes('重复')) {
        message.info('检测到正在进行的训练，请等待完成后再试');
      }
    } finally {
      console.log('🏁 [训练] 设置loading为false');
      setLoading(false);
    }
  };

  // 训练记录表格列
  const columns = [
    {
      title: '版本',
      dataIndex: 'version_number',
      key: 'version_number',
      render: (version, record) => (
        <div>
          <Tag color="blue">v{version}</Tag>
          {record.is_active && <Tag color="green">当前激活</Tag>}
        </div>
      ),
    },
    {
      title: '训练状态',
      dataIndex: 'training_status',
      key: 'training_status',
      render: (status) => {
        const statusConfig = {
          'pending': { color: 'processing', text: '准备中' },
          'running': { color: 'processing', text: '训练中' },
          'completed': { color: 'success', text: '完成' },
          'success': { color: 'success', text: '成功' },  // 兼容旧状态
          'failed': { color: 'error', text: '失败' },
          'cancelled': { color: 'default', text: '已取消' }
        };
        const config = statusConfig[status] || { color: 'default', text: status || '未知' };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '训练数据',
      key: 'training_data',
      render: (_, record) => (
        <div>
          <div>意图: {record.intent_count} 个</div>
          <div>词槽: {record.slot_count} 个</div>
          <div>样本: {record.training_data_count} 条</div>
        </div>
      ),
    },
    {
      title: '训练时间',
      key: 'training_time',
      render: (_, record) => (
        <div>
          <div>开始: {formatLocalTime(record.start_time)}</div>
          {record.complete_time && (
            <div>完成: {formatLocalTime(record.complete_time)}</div>
          )}
        </div>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            size="small" 
            onClick={() => {
              // 不设置currentTrainingId，避免影响训练状态
              fetchTrainingLogs(record.id);
              setSelectedLogRecordId(record.id);
              setTrainingLogVisible(true);
            }}
          >
            查看日志
          </Button>
          {(record.training_status === 'completed' || record.training_status === 'success') && !record.is_active && (
            <Button 
              size="small" 
              type="primary"
              onClick={async () => {
                try {
                  await trainingAPI.activateTrainingRecord(record.id);
                  message.success('模型已激活');
                  fetchTrainingRecords();
                  fetchTrainingSummary();
                } catch (error) {
                  message.error('激活失败: ' + error.message);
                }
              }}
            >
              激活
            </Button>
          )}
        </Space>
      ),
    }
  ];

  return (
    <div className="training-tab">
      {/* 统计信息 */}
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={6}>
          <Card size="small" style={{ minHeight: 'auto', padding: '8px 12px' }} bodyStyle={{ padding: '8px 0' }}>
            <Statistic
              title="总训练次数"
              value={trainingSummary?.total_trainings || 0}
              prefix={<RobotOutlined style={{ color: '#1890ff', fontSize: '14px' }} />}
              valueStyle={{ fontSize: '16px', lineHeight: '1.2' }}
              titleStyle={{ fontSize: '12px', marginBottom: '4px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" style={{ minHeight: 'auto', padding: '8px 12px' }} bodyStyle={{ padding: '8px 0' }}>
            <Statistic
              title="成功训练"
              value={trainingSummary?.successful_trainings || 0}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a', fontSize: '14px' }} />}
              valueStyle={{ fontSize: '16px', lineHeight: '1.2' }}
              titleStyle={{ fontSize: '12px', marginBottom: '4px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" style={{ minHeight: 'auto', padding: '8px 12px' }} bodyStyle={{ padding: '8px 0' }}>
            <Statistic
              title="平均成功率"
              value={Math.round(trainingSummary?.success_rate || 0)}
              suffix="%"
              prefix={<BarChartOutlined style={{ color: '#fa8c16', fontSize: '14px' }} />}
              valueStyle={{ fontSize: '16px', lineHeight: '1.2' }}
              titleStyle={{ fontSize: '12px', marginBottom: '4px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card size="small" style={{ minHeight: 'auto', padding: '8px 12px' }} bodyStyle={{ padding: '8px 0' }}>
            <Statistic
              title="当前版本"
              value={trainingSummary?.active_version || "-"}
              prefix={<FileTextOutlined style={{ color: '#722ed1', fontSize: '14px' }} />}
              valueStyle={{ fontSize: '16px', lineHeight: '1.2' }}
              titleStyle={{ fontSize: '12px', marginBottom: '4px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 智能数据状态提示 */}
      {(() => {
        const alertConfig = getDataStatusAlert();
        return (
          <Alert
            message={alertConfig.message}
            description={alertConfig.description}
            type={alertConfig.type}
            showIcon
            icon={alertConfig.icon}
            style={{ marginBottom: 24 }}
          />
        );
      })()}

      {/* 训练进度 */}
      {trainingProgress && (
        <Card title="训练进度" style={{ marginBottom: 24 }}>
          <Steps
            current={Math.floor(trainingProgress.progress / 25)}
            status={trainingProgress.progress === 100 ? 'finish' : 'process'}
            style={{ marginBottom: 24 }}
          >
            <Step title="数据准备" description="准备训练数据" />
            <Step title="模型训练" description="执行模型训练" />
            <Step title="模型验证" description="验证模型性能" />
            <Step title="训练完成" description="保存训练结果" />
          </Steps>
          
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <div>
                <div style={{ marginBottom: 8 }}>
                  <span>训练进度: {trainingProgress.progress}%</span>
                </div>
                <Progress 
                  percent={trainingProgress.progress} 
                  status={trainingProgress.progress === 100 ? 'success' : 'active'}
                />
              </div>
            </Col>
            <Col span={12}>
              <Statistic
                title="当前步骤"
                value={trainingProgress.step}
                prefix={<ClockCircleOutlined />}
              />
            </Col>
          </Row>
        </Card>
      )}

      <Row gutter={[16, 16]}>
        {/* 训练控制 */}
        <Col xs={24} lg={8}>
          <Card 
            title="快速开始训练"
            extra={
              <Space>
                <Tooltip title="高级训练参数配置">
                  <Button 
                    type="text" 
                    icon={<SettingOutlined />}
                    onClick={() => setAdvancedConfigVisible(true)}
                  />
                </Tooltip>
                <Tooltip title="查看训练日志">
                  <Button 
                    type="text" 
                    icon={<EyeOutlined />}
                    onClick={() => setTrainingLogVisible(true)}
                    disabled={!currentTrainingId}
                  />
                </Tooltip>
                <Tooltip title="模型性能分析">
                  <Button 
                    type="text" 
                    icon={<LineChartOutlined />}
                    onClick={() => setPerformanceAnalysisVisible(true)}
                  />
                </Tooltip>
              </Space>
            }
          >
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <RobotOutlined style={{ fontSize: '48px', color: '#1890ff', marginBottom: '16px' }} />
              <h3>开始模型训练</h3>
              <p style={{ color: '#666', marginBottom: '24px' }}>
                使用当前配置参数开始训练
              </p>
              <Button
                type="primary"
                size="large"
                onClick={handleStartTraining}
                disabled={loading || !!currentTrainingId}
                loading={loading}
                style={{ 
                  minWidth: '140px',
                  height: '48px',
                  fontSize: '16px',
                  borderRadius: '8px',
                  boxShadow: loading ? 'none' : '0 2px 8px rgba(24, 144, 255, 0.2)'
                }}
              >
                {loading ? (
                  <span>
                    <LoadingOutlined style={{ marginRight: 8 }} />
                    启动中...
                  </span>
                ) : currentTrainingId ? (
                  <span>
                    <RobotOutlined style={{ marginRight: 8 }} />
                    训练进行中...
                  </span>
                ) : (
                  <span>
                    <PlayCircleOutlined style={{ marginRight: 8 }} />
                    开始训练
                  </span>
                )}
              </Button>
            </div>

            <div style={{ marginTop: 20, padding: 16, background: '#fafafa', borderRadius: 6 }}>
              <h4>当前训练参数:</h4>
              <div style={{ fontSize: '12px', color: '#666' }}>
                <div>训练轮数: {trainingParams.epochs}</div>
                <div>批次大小: {trainingParams.batch_size}</div>
                <div>学习率: {trainingParams.learning_rate}</div>
                <div>验证比例: {trainingParams.validation_split}</div>
                <div>早停机制: {trainingParams.early_stopping ? '启用' : '禁用'}</div>
                <div>注意力机制: {trainingParams.use_attention ? '启用' : '禁用'}</div>
              </div>
              <Button 
                type="link" 
                size="small" 
                onClick={() => setAdvancedConfigVisible(true)}
                style={{ padding: 0, marginTop: 8 }}
              >
                修改参数配置 →
              </Button>
            </div>
          </Card>
        </Col>

        {/* 训练历史 */}
        <Col xs={24} lg={16}>
          <Card title="最近训练记录">
            {trainingRecords.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>暂无训练记录</div>
                <div style={{ fontSize: '12px', marginTop: '8px' }}>开始第一次模型训练吧</div>
              </div>
            ) : (
              <Timeline>
                {trainingRecords.slice(0, 5).map((record, index) => (
                  <Timeline.Item
                    key={record.id}
                    color={
                      (record.training_status === 'completed' || record.training_status === 'success') ? 'green' : 
                      record.training_status === 'failed' ? 'red' : 
                      'blue'
                    }
                    dot={
                      (record.training_status === 'completed' || record.training_status === 'success') ? 
                      <CheckCircleOutlined /> : 
                      <ClockCircleOutlined />
                    }
                  >
                    <div>
                      <strong>v{record.version_number}</strong> - {
                        (record.training_status === 'completed' || record.training_status === 'success') ? '训练成功' : 
                        record.training_status === 'failed' ? '训练失败' : 
                        record.training_status === 'running' ? '训练中' : 
                        record.training_status === 'pending' ? '准备中' : '未知状态'
                      }
                      {record.is_active && <Tag color="green" style={{ marginLeft: 8 }}>当前激活</Tag>}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      {formatLocalTime(record.start_time)}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      意图: {record.intent_count} | 词槽: {record.slot_count} | 样本: {record.training_data_count}
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            )}
          </Card>
        </Col>
      </Row>

      {/* 训练记录表格 */}
      <Card 
        title="全部训练记录" 
        style={{ marginTop: 24 }}
      >
        <Table
          columns={columns}
          dataSource={trainingRecords}
          rowKey="id"
          locale={{
            emptyText: (
              <div style={{ padding: '40px', color: '#999' }}>
                <RobotOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <div>暂无训练记录</div>
              </div>
            )
          }}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      {/* 高级训练参数配置模态框 */}
      <Modal
        title="高级训练参数配置"
        open={advancedConfigVisible}
        onCancel={() => setAdvancedConfigVisible(false)}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => setAdvancedConfigVisible(false)}>
            取消
          </Button>,
          <Button 
            key="reset" 
            onClick={() => {
              setTrainingParams({
                epochs: 5,
                batch_size: 32,
                learning_rate: 0.001,
                dropout_rate: 0.2,
                validation_split: 0.2,
                early_stopping: true,
                patience: 10,
                use_attention: true,
                embedding_dimension: 256,
                hidden_units: 128
              });
              message.success('参数已重置为默认值');
            }}
          >
            重置默认
          </Button>,
          <Button 
            key="save" 
            type="primary"
            onClick={() => {
              setAdvancedConfigVisible(false);
              message.success('训练参数配置已保存');
            }}
          >
            保存配置
          </Button>
        ]}
      >
        <Form layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="训练轮数 (Epochs)">
                <InputNumber
                  min={1}
                  max={1000}
                  value={trainingParams.epochs}
                  onChange={(value) => setTrainingParams({...trainingParams, epochs: value})}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="批次大小 (Batch Size)">
                <InputNumber
                  min={1}
                  max={256}
                  value={trainingParams.batch_size}
                  onChange={(value) => setTrainingParams({...trainingParams, batch_size: value})}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="学习率 (Learning Rate)">
                <InputNumber
                  min={0.0001}
                  max={1}
                  step={0.0001}
                  value={trainingParams.learning_rate}
                  onChange={(value) => setTrainingParams({...trainingParams, learning_rate: value})}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Dropout率">
                <InputNumber
                  min={0}
                  max={1}
                  step={0.1}
                  value={trainingParams.dropout_rate}
                  onChange={(value) => setTrainingParams({...trainingParams, dropout_rate: value})}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="验证集比例">
                <InputNumber
                  min={0.1}
                  max={0.5}
                  step={0.1}
                  value={trainingParams.validation_split}
                  onChange={(value) => setTrainingParams({...trainingParams, validation_split: value})}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="早停耐心值">
                <InputNumber
                  min={1}
                  max={50}
                  value={trainingParams.patience}
                  onChange={(value) => setTrainingParams({...trainingParams, patience: value})}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="嵌入维度">
                <InputNumber
                  min={64}
                  max={1024}
                  step={64}
                  value={trainingParams.embedding_dimension}
                  onChange={(value) => setTrainingParams({...trainingParams, embedding_dimension: value})}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="隐藏单元数">
                <InputNumber
                  min={32}
                  max={512}
                  step={32}
                  value={trainingParams.hidden_units}
                  onChange={(value) => setTrainingParams({...trainingParams, hidden_units: value})}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="早停机制">
                <Switch
                  checked={trainingParams.early_stopping}
                  onChange={(checked) => setTrainingParams({...trainingParams, early_stopping: checked})}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="注意力机制">
                <Switch
                  checked={trainingParams.use_attention}
                  onChange={(checked) => setTrainingParams({...trainingParams, use_attention: checked})}
                />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 训练日志模态框 */}
      <Modal
        title="训练日志"
        open={trainingLogVisible}
        onCancel={() => setTrainingLogVisible(false)}
        width={800}
        footer={[
          <Button key="refresh" onClick={() => selectedLogRecordId && fetchTrainingLogs(selectedLogRecordId)}>
            刷新日志
          </Button>,
          <Button key="close" onClick={() => setTrainingLogVisible(false)}>
            关闭
          </Button>
        ]}
      >
        <div style={{ 
          maxHeight: '400px', 
          overflowY: 'auto', 
          backgroundColor: '#000', 
          color: '#fff', 
          padding: '12px', 
          borderRadius: '4px',
          fontFamily: 'monospace'
        }}>
          {trainingLogs.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#666' }}>暂无日志</div>
          ) : (
            trainingLogs.map((log, index) => (
              <div key={index} style={{ marginBottom: '4px' }}>
                <span style={{ color: '#888' }}>[{String(index + 1).padStart(3, '0')}]</span> {log}
              </div>
            ))
          )}
        </div>
      </Modal>

      {/* 性能分析模态框 */}
      <Modal
        title="模型性能分析"
        open={performanceAnalysisVisible}
        onCancel={() => setPerformanceAnalysisVisible(false)}
        width={1000}
        footer={[
          <Button key="close" onClick={() => setPerformanceAnalysisVisible(false)}>
            关闭
          </Button>
        ]}
      >
        <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
          <LineChartOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
          <div>模型性能分析功能开发中</div>
          <div style={{ fontSize: '12px', marginTop: '8px' }}>将包含准确率、召回率、F1分数等指标</div>
        </div>
      </Modal>
    </div>
  );
};

export default TrainingTab; 