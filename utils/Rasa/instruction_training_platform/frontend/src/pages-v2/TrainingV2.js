import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Form, Input, Select, message, 
  Row, Col, Statistic, Progress, List, Badge, Tabs, Alert,
  Tag, Space, Tooltip, Steps, Timeline, Descriptions, LoadingOutlined
} from 'antd';
import {
  RobotOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  SettingOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  BarChartOutlined,
  FileTextOutlined,
  WarningOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { trainingAPI, versionAPI, apiUtils } from '../api-v2';
import { formatLocalTime } from '../utils/timeUtils';
import { safeTableDataSource } from '../utils/dataSourceUtils';

const { TextArea } = Input;
const { TabPane } = Tabs;
const { Step } = Steps;

const TrainingV2 = ({ currentLibrary }) => {
  const [loading, setLoading] = useState(false);
  const [trainingRecords, setTrainingRecords] = useState([]);
  const [currentTraining, setCurrentTraining] = useState(null);
  const [trainingStatus, setTrainingStatus] = useState(null);
  const [trainingSummary, setTrainingSummary] = useState(null);
  
  // 模态框状态
  const [startTrainingModalVisible, setStartTrainingModalVisible] = useState(false);
  const [trainingDetailModalVisible, setTrainingDetailModalVisible] = useState(false);
  const [configModalVisible, setConfigModalVisible] = useState(false);
  
  const [trainingForm] = Form.useForm();

  // 默认训练参数
  const defaultTrainingParams = {
    epochs: 5,
    batch_size: 32,
    learning_rate: 0.001,
    dropout_rate: 0.2,
    validation_split: 0.2,
    early_stopping: true,
    patience: 10
  };

  // 检查是否选择了指令库
  if (!currentLibrary) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <RobotOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
          <h3>请先选择指令库</h3>
          <p style={{ color: '#666' }}>在开始模型训练之前，请先在指令库管理页面选择一个指令库。</p>
        </div>
      </Card>
    );
  }

  // 获取训练汇总
  const fetchTrainingSummary = async () => {
    try {
      const response = await trainingAPI.getTrainingSummary(currentLibrary.id);
      setTrainingSummary(response.data);
    } catch (error) {
      console.error('获取训练汇总失败:', error);
    }
  };

  // 获取训练记录
  const fetchTrainingRecords = async () => {
    setLoading(true);
    try {
      const response = await trainingAPI.getTrainingRecords({ library_id: currentLibrary.id });
      setTrainingRecords(response.data.training_records || []);
      
      // 查找正在进行的训练
      const runningTraining = response.data.training_records?.find(r => r.training_status === 'running');
      if (runningTraining) {
        setCurrentTraining(runningTraining);
        // 开始监控训练状态
        startTrainingMonitor(runningTraining.id);
      }
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取训练记录失败'));
    } finally {
      setLoading(false);
    }
  };

  // 启动训练监控 - 优化版本
  const startTrainingMonitor = (trainingId) => {
    console.log('🔍 [监控] 启动训练监控，training_id:', trainingId);
    
    // 清除之前的监控
    if (window.trainingMonitor) {
      clearInterval(window.trainingMonitor);
    }
    
    // 监控状态
    window.trainingMonitorState = {
      errorCount: 0,
      consecutiveCompleted: 0,
      lastStatus: null,
      pollInterval: 6000, // 初始轮询间隔6秒
      maxInterval: 10000, // 最大轮询间隔10秒
      minInterval: 1000   // 最小轮询间隔1秒
    };
    
    const fetchStatus = async () => {
      try {
        console.log('📊 [监控] 获取训练状态...');
        const response = await trainingAPI.getTrainingStatus(trainingId);
        const statusData = response.data;
        
        console.log('📥 [监控] 收到状态数据:', statusData);
        
        // 状态映射：后端返回的状态 -> 前端显示状态
        const statusMap = {
          'pending': 'pending',
          'running': 'running',
          'completed': 'completed',
          'failed': 'failed'
        };
        
        const mappedStatus = statusMap[statusData.training_status] || statusData.training_status;
        console.log('🔄 [监控] 状态映射:', statusData.training_status, '->', mappedStatus);
        
        // 更新当前训练记录
        setCurrentTraining(prev => ({
          ...prev,
          training_status: mappedStatus,
          progress: statusData.progress,
          current_step: statusData.current_step,
          elapsed_time: statusData.elapsed_time,
          estimated_remaining: statusData.estimated_remaining,
          end_time: statusData.end_time,
          complete_time: statusData.end_time,
          error_message: statusData.error_message
        }));
        
        // 更新训练状态
        setTrainingStatus({
          training_status: mappedStatus,
          progress: statusData.progress || 0,
          current_step: statusData.current_step || '处理中...',
          elapsed_time: statusData.elapsed_time || 0,
          estimated_remaining: statusData.estimated_remaining || 0,
          start_time: statusData.start_time,
          end_time: statusData.end_time,
          error_message: statusData.error_message,
          logs: statusData.logs || []
        });
        
        console.log('✅ [监控] 状态更新完成 - 进度:', statusData.progress + '%', '状态:', mappedStatus);
        
        // 重置错误计数
        window.trainingMonitorState.errorCount = 0;
        
        // 智能调整轮询间隔
        adjustPollingInterval(mappedStatus, statusData.progress);
        
        // 检查是否需要停止监控
        if (['completed', 'failed', 'cancelled'].includes(mappedStatus)) {
          window.trainingMonitorState.consecutiveCompleted++;
          
          // 连续2次获得完成状态才停止监控，避免状态波动
          if (window.trainingMonitorState.consecutiveCompleted >= 2) {
            console.log('🏁 [监控] 训练已结束，停止监控');
            stopTrainingMonitor();
            
            // 最终状态提示
            if (mappedStatus === 'completed') {
              message.success('训练已完成！');
            } else if (mappedStatus === 'failed') {
              message.error('训练失败，请查看错误信息');
            }
            
            // 刷新训练记录和摘要
            fetchTrainingRecords();
            fetchTrainingSummary();
            return;
          }
        } else {
          window.trainingMonitorState.consecutiveCompleted = 0;
        }
        
        // 更新最后状态
        window.trainingMonitorState.lastStatus = mappedStatus;
        
        // 设置下次轮询
        scheduleNextPoll();
        
      } catch (error) {
        console.error('❌ [监控] 获取状态失败:', error);
        
        // 错误计数
        window.trainingMonitorState.errorCount++;
        
        // 根据错误类型决定处理策略
        if (error.response?.status === 404) {
          // 训练记录不存在，立即停止监控
          console.error('💥 [监控] 训练记录不存在，停止监控');
          stopTrainingMonitor();
          setCurrentTraining(null);
          setTrainingStatus(null);
          message.error('训练记录不存在');
          return;
        }
        
        // 如果连续错误超过3次，停止监控
        if (window.trainingMonitorState.errorCount >= 3) {
          console.error('💥 [监控] 连续错误过多，停止监控');
          stopTrainingMonitor();
          setCurrentTraining(null);
          setTrainingStatus(null);
          message.error('训练状态监控失败，请手动刷新查看结果');
          return;
        }
        
        // 错误时增加轮询间隔
        window.trainingMonitorState.pollInterval = Math.min(
          window.trainingMonitorState.pollInterval * 1.5,
          window.trainingMonitorState.maxInterval
        );
        
        // 设置下次轮询
        scheduleNextPoll();
      }
    };
    
    // 智能调整轮询间隔
    const adjustPollingInterval = (status, progress) => {
      const state = window.trainingMonitorState;
      
      if (status === 'pending') {
        // 准备阶段，较快轮询
        state.pollInterval = 6000;
      } else if (status === 'running') {
        // 根据进度调整间隔
        if (progress < 20) {
          // 初期阶段，较快轮询
          state.pollInterval = 6000;
        } else if (progress < 80) {
          // 中期阶段，中等轮询
          state.pollInterval = 6000;
        } else {
          // 后期阶段，较快轮询（接近完成）
          state.pollInterval = 6000;
        }
      } else if (['completed', 'failed'].includes(status)) {
        // 已完成，快速确认后停止
        state.pollInterval = 3000;
      }
      
      // 确保在合理范围内
      state.pollInterval = Math.max(state.minInterval, 
        Math.min(state.pollInterval, state.maxInterval));
      
      console.log(`⏰ [监控] 调整轮询间隔: ${state.pollInterval}ms (状态: ${status}, 进度: ${progress}%)`);
    };
    
    // 计划下次轮询
    const scheduleNextPoll = () => {
      const interval = window.trainingMonitorState.pollInterval;
      console.log(`⏳ [监控] 计划${interval}ms后进行下次轮询`);
      
      window.trainingMonitor = setTimeout(fetchStatus, interval);
    };
    
    // 停止训练监控
    const stopTrainingMonitor = () => {
      if (window.trainingMonitor) {
        clearTimeout(window.trainingMonitor);
        window.trainingMonitor = null;
      }
      window.trainingMonitorState = null;
      console.log('🛑 [监控] 训练监控已停止');
    };
    
    // 保存停止函数到window以便外部调用
    window.stopTrainingMonitor = stopTrainingMonitor;
    
    // 立即执行第一次
    console.log('⚡ [监控] 立即执行第一次状态检查');
    fetchStatus();
  };

  useEffect(() => {
    if (currentLibrary) {
      fetchTrainingSummary();
      fetchTrainingRecords();
    }

    // 清理监控器 - 组件卸载时
    return () => {
      console.log('🧹 [清理] 组件卸载，清理训练监控');
      if (window.trainingMonitor) {
        clearTimeout(window.trainingMonitor);
        window.trainingMonitor = null;
      }
      if (window.stopTrainingMonitor) {
        window.stopTrainingMonitor();
      }
      if (window.logMonitor) {
        clearInterval(window.logMonitor);
        window.logMonitor = null;
      }
      // 清理监控状态
      window.trainingMonitorState = null;
      console.log('✅ [清理] 所有监控器已清理');
    };
  }, [currentLibrary]);

  // 页面可见性变化时的处理
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // 页面隐藏时，暂停监控以节省资源
        if (window.trainingMonitorState) {
          console.log('👁️ [可见性] 页面隐藏，暂停训练监控');
          window.trainingMonitorState.paused = true;
          if (window.trainingMonitor) {
            clearTimeout(window.trainingMonitor);
            window.trainingMonitor = null;
          }
        }
      } else {
        // 页面显示时，恢复监控
        if (window.trainingMonitorState && window.trainingMonitorState.paused) {
          console.log('👁️ [可见性] 页面显示，恢复训练监控');
          window.trainingMonitorState.paused = false;
          // 如果有正在进行的训练，恢复监控
          if (currentTraining && ['pending', 'running'].includes(currentTraining.training_status)) {
            startTrainingMonitor(currentTraining.id);
          }
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [currentTraining]);

  // 开始训练
  const handleStartTraining = async (values) => {
    console.log('🚀 [训练] 开始训练函数被调用');
    console.log('📝 [训练] 训练参数:', values);
    console.log('🏗️ [训练] 当前状态 - loading:', loading, 'currentTraining:', currentTraining);
    
    // 防止重复点击
    if (loading || currentTraining) {
      console.warn('⚠️ [训练] 重复点击被阻止 - loading:', loading, 'currentTraining:', currentTraining);
      message.warning('训练正在进行中，请勿重复点击');
      return;
    }
    
    try {
      console.log('📤 [训练] 开始设置loading状态');
      setLoading(true);
      
      // 立即设置当前训练状态，防止重复点击
      console.log('🔄 [训练] 设置临时训练状态');
      setCurrentTraining({
        id: 'pending',
        status: 'pending',
        training_status: 'pending'
      });
      
      const requestData = {
        library_id: currentLibrary.id,
        training_params: values.training_params || defaultTrainingParams,
        description: values.description
      };
      
      console.log('📡 [训练] 准备发送API请求:', requestData);
      console.log('🌐 [训练] API URL: /api/v2/training/start');
      
      const response = await trainingAPI.startTraining(requestData);
      
      console.log('✅ [训练] API请求成功');
      console.log('📥 [训练] 响应数据:', response.data);
      
      // 更新当前训练状态
      console.log('🔄 [训练] 更新训练状态');
      setCurrentTraining(response.data.training_record);
      
      // 立即设置初始训练状态
      const initialStatus = {
        training_status: 'pending',
        progress: 0,
        current_step: '准备启动训练...',
        elapsed_time: 0,
        estimated_remaining: 0,
        start_time: response.data.training_record.start_time,
        end_time: null,
        error_message: null,
        logs: ['训练任务已创建，准备开始...']
      };
      
      console.log('📊 [训练] 设置初始状态:', initialStatus);
      setTrainingStatus(initialStatus);
      
      message.success('训练已启动');
      setStartTrainingModalVisible(false);
      
      console.log('🔍 [训练] 准备启动状态监控 - training_id:', response.data.training_record.id);
      
      // 立即开始监控
      startTrainingMonitor(response.data.training_record.id);
      
      // 刷新记录
      console.log('🔄 [训练] 刷新训练记录列表');
      fetchTrainingRecords();
    } catch (error) {
      console.error('❌ [训练] API请求失败:', error);
      console.error('📄 [训练] 错误详情:', error.response?.data);
      console.error('🔢 [训练] 错误状态码:', error.response?.status);
      
      // 如果启动失败，清除当前训练状态
      console.log('🧹 [训练] 清除训练状态');
      setCurrentTraining(null);
      setTrainingStatus(null);
      message.error(apiUtils.handleError(error, '启动训练失败'));
    } finally {
      console.log('🏁 [训练] 设置loading为false');
      setLoading(false);
    }
  };

  // 查看训练详情
  const viewTrainingDetail = async (record) => {
    try {
      const response = await trainingAPI.getTrainingRecordDetail(record.id);
      setCurrentTraining(response.data);
      setTrainingDetailModalVisible(true);
      
      // 如果训练正在进行，启动日志监控
      if (record.training_status === 'running' || record.training_status === 'pending') {
        startLogMonitor(record.id);
      }
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取训练详情失败'));
    }
  };

  // 启动日志监控 - 优化版本
  const startLogMonitor = (trainingId) => {
    console.log('📋 [日志监控] 启动日志监控，training_id:', trainingId);
    
    // 清除之前的监控
    if (window.logMonitor) {
      clearInterval(window.logMonitor);
      window.logMonitor = null;
    }
    
    let errorCount = 0;
    const maxErrors = 3;
    
    const monitor = setInterval(async () => {
      try {
        console.log('📋 [日志监控] 获取训练日志...');
        const response = await trainingAPI.getTrainingStatus(trainingId);
        const statusData = response.data;
        
        // 更新当前训练记录的日志
        setCurrentTraining(prev => ({
          ...prev,
          training_log: statusData.logs ? statusData.logs.join('\n') : prev.training_log,
          training_status: statusData.training_status,
          progress: statusData.progress
        }));
        
        // 重置错误计数
        errorCount = 0;
        
        // 如果训练完成，停止监控
        if (['completed', 'failed', 'cancelled'].includes(statusData.training_status)) {
          console.log('🏁 [日志监控] 训练已结束，停止日志监控');
          clearInterval(monitor);
          window.logMonitor = null;
        }
      } catch (error) {
        console.error('❌ [日志监控] 获取日志失败:', error);
        errorCount++;
        
        // 如果连续错误超过限制，停止监控
        if (errorCount >= maxErrors) {
          console.error('💥 [日志监控] 连续错误过多，停止日志监控');
          clearInterval(monitor);
          window.logMonitor = null;
        }
      }
    }, 6000); // 每6秒检查一次日志
    
    window.logMonitor = monitor;
  };

  // 停止日志监控
  const stopLogMonitor = () => {
    if (window.logMonitor) {
      console.log('🛑 [日志监控] 停止日志监控');
      clearInterval(window.logMonitor);
      window.logMonitor = null;
    }
  };

  // 删除训练记录
  const handleDeleteTrainingRecord = async (recordId) => {
    try {
      await trainingAPI.deleteTrainingRecord(recordId);
      message.success('训练记录删除成功');
      fetchTrainingRecords();
      fetchTrainingSummary();
    } catch (error) {
      message.error(apiUtils.handleError(error, '删除训练记录失败'));
    }
  };

  // 渲染训练进度
  const renderTrainingProgress = () => {
    if (!currentTraining || !trainingStatus) return null;

    const { training_status, progress, current_step, elapsed_time, estimated_remaining } = trainingStatus;
    
    return (
      <Card 
        title="训练进度" 
        style={{ marginBottom: 24 }}
        extra={
          <Tag color={training_status === 'running' ? 'processing' : training_status === 'completed' ? 'success' : 'error'}>
            {training_status === 'running' ? '训练中' : training_status === 'completed' ? '训练完成' : '训练失败'}
          </Tag>
        }
      >
        <Steps
          current={progress >= 100 ? 4 : Math.floor(progress / 25)}
          status={training_status === 'failed' ? 'error' : 'process'}
          style={{ marginBottom: 24 }}
        >
          <Step title="数据准备" description="准备训练数据" />
          <Step title="模型初始化" description="初始化模型参数" />
          <Step title="训练执行" description="执行模型训练" />
          <Step title="模型验证" description="验证模型性能" />
          <Step title="训练完成" description="保存训练结果" />
        </Steps>

        <Row gutter={[16, 16]}>
          <Col span={8}>
            <Statistic
              title="训练进度"
              value={progress || 0}
              suffix="%"
              prefix={<BarChartOutlined />}
            />
            <Progress percent={progress || 0} status={training_status === 'failed' ? 'exception' : 'active'} />
          </Col>
          <Col span={8}>
            <Statistic
              title="已用时间"
              value={elapsed_time || 0}
              suffix="分钟"
              prefix={<ClockCircleOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="预计剩余"
              value={estimated_remaining || 0}
              suffix="分钟"
              prefix={<ClockCircleOutlined />}
            />
          </Col>
        </Row>

        {current_step && (
          <Alert
            message={`当前步骤: ${current_step}`}
            type="info"
            style={{ marginTop: 16 }}
          />
        )}
      </Card>
    );
  };

  // 训练记录表格列定义
  const trainingRecordColumns = [
    {
      title: '版本',
      dataIndex: 'version_number',
      key: 'version_number',
      width: 80,
      render: (version) => <Tag color="blue">v{version}</Tag>,
    },
    {
      title: '训练状态',
      dataIndex: 'training_status',
      key: 'training_status',
      width: 120,
      render: (status) => {
        const statusConfig = {
          'pending': { color: 'processing', text: '准备中', icon: <ClockCircleOutlined /> },
          'running': { color: 'processing', text: '训练中', icon: <RobotOutlined /> },
          'completed': { color: 'success', text: '成功', icon: <CheckCircleOutlined /> },
          'failed': { color: 'error', text: '失败', icon: <CloseCircleOutlined /> }
        };
        const config = statusConfig[status] || { color: 'default', text: status, icon: <QuestionCircleOutlined /> };
        return (
          <Badge 
            status={config.color} 
            text={
              <span>
                {config.icon} {config.text}
              </span>
            }
          />
        );
      },
    },
    {
      title: '训练数据',
      key: 'training_data',
      width: 200,
      render: (_, record) => (
        <div>
          <div>意图: {record.intent_count || 0} 个</div>
          <div>词槽: {record.slot_count || 0} 个</div>
          <div>训练样本: {record.training_data_count || 0} 条</div>
        </div>
      ),
    },
    {
      title: '训练时间',
      key: 'training_time',
      width: 200,
      render: (_, record) => (
        <div>
          <div>开始: {formatLocalTime(record.start_time) || '未开始'}</div>
          <div>完成: {formatLocalTime(record.complete_time) || '进行中'}</div>
          {record.start_time && record.complete_time && (
            <div>耗时: {Math.round((new Date(record.complete_time) - new Date(record.start_time)) / 60000)} 分钟</div>
          )}
        </div>
      ),
    },
    {
      title: '激活状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive) => (
        <Badge 
          status={isActive ? 'success' : 'default'} 
          text={isActive ? '已激活' : '未激活'} 
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => viewTrainingDetail(record)}
            />
          </Tooltip>
          {record.training_status === 'completed' && !record.is_active && (
            <Tooltip title="激活版本">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                onClick={() => {/* 激活版本逻辑 */}}
              />
            </Tooltip>
          )}
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteTrainingRecord(record.id)}
              disabled={record.is_active}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="training-v2">
      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="总训练次数"
              value={trainingRecords.length}
              prefix={<RobotOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="成功训练"
              value={trainingRecords.filter(r => r.training_status === 'success').length}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="平均成功率"
              value={trainingSummary?.success_rate || 0}
              suffix="%"
              prefix={<BarChartOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="当前版本"
              value={trainingSummary?.latest_version || 0}
              prefix={<FileTextOutlined style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 数据准备检查 */}
      {trainingSummary && (
        <Alert
          message="训练数据状态"
          description={
            <div>
              指令数量: {trainingSummary.intent_count} 个 | 
              词槽数量: {trainingSummary.slot_count} 个 | 
              训练样本: {trainingSummary.training_data_count} 条
              {trainingSummary.intent_count < 2 && (
                <div style={{ color: '#ff4d4f' }}>
                  ⚠️ 指令数量不足，建议至少包含2个不同的指令才能进行有效训练
                </div>
              )}
            </div>
          }
          type={trainingSummary.intent_count >= 2 ? 'success' : 'warning'}
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 训练进度显示 */}
      {renderTrainingProgress()}

      <Row gutter={[16, 16]}>
        {/* 训练配置区域 */}
        <Col xs={24} lg={8}>
          <Card
            title="快速开始训练"
            extra={
              <Button
                type="link"
                icon={<SettingOutlined />}
                onClick={() => setConfigModalVisible(true)}
              >
                高级配置
              </Button>
            }
          >
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <RobotOutlined style={{ fontSize: '48px', color: '#1890ff', marginBottom: '16px' }} />
              <h3>开始模型训练</h3>
              <p style={{ color: '#666', marginBottom: '24px' }}>
                使用默认参数快速开始训练
              </p>
              
              {/* 添加训练状态提示 */}
              {currentTraining && trainingStatus && (
                <div style={{ marginBottom: '20px', padding: '15px', background: '#f0f9ff', borderRadius: '8px', border: '1px solid #91d5ff' }}>
                  <div style={{ marginBottom: '10px' }}>
                    <Badge status="processing" text={`训练进行中 - ${trainingStatus.progress || 0}%`} />
                  </div>
                  <Progress 
                    percent={trainingStatus.progress || 0} 
                    size="small" 
                    status="active"
                    strokeColor={{
                      '0%': '#108ee9',
                      '100%': '#87d068',
                    }}
                  />
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                    {trainingStatus.current_step || '准备中...'}
                  </div>
                  {trainingStatus.elapsed_time > 0 && (
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      已用时间: {trainingStatus.elapsed_time.toFixed(1)}分钟
                      {trainingStatus.estimated_remaining > 0 && ` | 预计剩余: ${trainingStatus.estimated_remaining.toFixed(1)}分钟`}
                    </div>
                  )}
                </div>
              )}
              
              <Button
                type="primary"
                size="large"
                onClick={() => setStartTrainingModalVisible(true)}
                disabled={loading || currentTraining || (trainingSummary?.intent_count < 2)}
                loading={loading || (currentTraining && ['pending', 'running'].includes(trainingStatus?.training_status))}
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
                ) : currentTraining ? (
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
              
              {/* 添加取消训练按钮 */}
              {currentTraining && trainingStatus?.training_status === 'running' && (
                <Button
                  style={{ marginLeft: '10px' }}
                  onClick={() => {
                    if (window.trainingMonitor) {
                      clearInterval(window.trainingMonitor);
                    }
                    setCurrentTraining(null);
                    setTrainingStatus(null);
                    message.info('已停止监控训练进度');
                  }}
                >
                  停止监控
                </Button>
              )}
            </div>

            {trainingSummary && (
              <div style={{ marginTop: 20, padding: 16, background: '#fafafa', borderRadius: 6 }}>
                <h4>训练参数预览:</h4>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  <div>训练轮数: {defaultTrainingParams.epochs}</div>
                  <div>批次大小: {defaultTrainingParams.batch_size}</div>
                  <div>学习率: {defaultTrainingParams.learning_rate}</div>
                  <div>验证比例: {defaultTrainingParams.validation_split}</div>
                </div>
              </div>
            )}
          </Card>
        </Col>

        {/* 训练历史 */}
        <Col xs={24} lg={16}>
          <Card
            title="最近训练记录"
            extra={
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchTrainingRecords}
              >
                刷新
              </Button>
            }
          >
            <Timeline>
              {trainingRecords.slice(0, 5).map((record, index) => (
                <Timeline.Item
                  key={record.id}
                  color={record.training_status === 'success' ? 'green' : 
                         record.training_status === 'failed' ? 'red' : 'blue'}
                  dot={record.training_status === 'success' ? <CheckCircleOutlined /> :
                       record.training_status === 'failed' ? <CloseCircleOutlined /> :
                       <ClockCircleOutlined />}
                >
                  <div>
                    <strong>v{record.version_number}</strong> - {record.training_status === 'success' ? '训练成功' : 
                                                                record.training_status === 'failed' ? '训练失败' : '训练中'}
                    {record.is_active && <Tag color="green" style={{ marginLeft: 8 }}>当前激活</Tag>}
                  </div>
                                      <div style={{ fontSize: '12px', color: '#666' }}>
                      {formatLocalTime(record.start_time) || '未开始'}
                    </div>
                  {record.intent_count && (
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      意图: {record.intent_count} | 词槽: {record.slot_count} | 样本: {record.training_data_count}
                    </div>
                  )}
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Col>
      </Row>

      {/* 训练记录表格 */}
      <Card 
        title="全部训练记录" 
        style={{ marginTop: 24 }}
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchTrainingRecords}
          >
            刷新
          </Button>
        }
      >
        <Table
          columns={trainingRecordColumns}
          dataSource={safeTableDataSource(trainingRecords)}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
        />
      </Card>

      {/* 开始训练模态框 */}
      <Modal
        title="开始训练"
        open={startTrainingModalVisible}
        onCancel={() => setStartTrainingModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={trainingForm}
          layout="vertical"
          onFinish={handleStartTraining}
        >
          <Form.Item
            name="description"
            label="训练描述"
          >
            <TextArea
              rows={3}
              placeholder="请输入本次训练的描述信息（可选）"
            />
          </Form.Item>

          <Alert
            message="训练信息"
            description={
              <div>
                <div>将使用默认训练参数进行训练</div>
                <div>预计训练时间: 10-30分钟（取决于数据量）</div>
                <div>训练完成后将自动生成新的模型版本</div>
              </div>
            }
            type="info"
            style={{ marginBottom: 16 }}
          />

          <Form.Item>
            <Space>
              <Button onClick={() => setStartTrainingModalVisible(false)}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<PlayCircleOutlined />}
              >
                开始训练
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 训练详情模态框 */}
      <Modal
        title={`训练详情 - v${currentTraining?.version_number || 'N/A'}`}
        open={trainingDetailModalVisible}
        onCancel={() => {
          setTrainingDetailModalVisible(false);
          stopLogMonitor(); // 关闭模态框时停止日志监控
        }}
        footer={null}
        width={900}
      >
        {currentTraining && (
          <Tabs defaultActiveKey="1">
            <TabPane tab="基本信息" key="1">
              <Descriptions bordered column={2}>
                <Descriptions.Item label="训练ID">{currentTraining.id}</Descriptions.Item>
                <Descriptions.Item label="训练状态">
                  <Badge 
                    status={currentTraining.training_status === 'running' ? 'processing' : 
                           currentTraining.training_status === 'completed' ? 'success' : 'error'} 
                    text={currentTraining.training_status === 'running' ? '训练中' : 
                          currentTraining.training_status === 'completed' ? '训练完成' : '训练失败'} 
                  />
                </Descriptions.Item>
                <Descriptions.Item label="进度">
                  {currentTraining.progress || 0}%
                  <Progress 
                    percent={currentTraining.progress || 0} 
                    size="small" 
                    style={{ marginTop: 4 }}
                    status={currentTraining.training_status === 'failed' ? 'exception' : 'active'}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="指令库">{currentTraining.library_name}</Descriptions.Item>
                <Descriptions.Item label="开始时间">
                  {formatLocalTime(currentTraining.start_time)}
                </Descriptions.Item>
                <Descriptions.Item label="完成时间">
                  {formatLocalTime(currentTraining.end_time) || '进行中'}
                </Descriptions.Item>
                <Descriptions.Item label="描述" span={2}>
                  {currentTraining.description || '无描述'}
                </Descriptions.Item>
              </Descriptions>
            </TabPane>
            
            <TabPane tab="训练参数" key="2">
              <div style={{ padding: '20px', background: '#fafafa', borderRadius: 6 }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                  {currentTraining.training_params || '暂无参数信息'}
                </pre>
              </div>
            </TabPane>
            
            <TabPane 
              tab={
                <span>
                  <FileTextOutlined />
                  训练日志
                  {currentTraining.training_status === 'running' && (
                    <Badge status="processing" style={{ marginLeft: 8 }} />
                  )}
                </span>
              } 
              key="3"
            >
              <div style={{ marginBottom: 16 }}>
                <Space>
                  <Button 
                    icon={<ReloadOutlined />}
                    onClick={() => {
                      if (currentTraining.training_status === 'running') {
                        startLogMonitor(currentTraining.id);
                        message.success('已开启实时日志监控');
                      } else {
                        viewTrainingDetail(currentTraining);
                        message.info('已刷新日志');
                      }
                    }}
                  >
                    {currentTraining.training_status === 'running' ? '开启实时监控' : '刷新日志'}
                  </Button>
                  
                  {window.logMonitor && (
                    <Button 
                      icon={<PauseCircleOutlined />}
                      onClick={() => {
                        stopLogMonitor();
                        message.info('已停止实时监控');
                      }}
                    >
                      停止监控
                    </Button>
                  )}
                  
                  <Tag color={currentTraining.training_status === 'running' ? 'processing' : 'default'}>
                    {window.logMonitor ? '实时监控中' : '静态查看'}
                  </Tag>
                </Space>
              </div>
              
              <div style={{ 
                padding: '16px', 
                background: '#f6f6f6', 
                borderRadius: 6, 
                maxHeight: '400px', 
                overflow: 'auto',
                fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
                fontSize: '12px',
                lineHeight: '1.4',
                border: '1px solid #d9d9d9'
              }}>
                {currentTraining.training_log ? (
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {currentTraining.training_log}
                  </pre>
                ) : (
                  <div style={{ color: '#999', textAlign: 'center', padding: '20px' }}>
                    <FileTextOutlined style={{ fontSize: '24px', marginBottom: '8px' }} />
                    <div>暂无日志信息</div>
                    {currentTraining.training_status === 'running' && (
                      <div style={{ fontSize: '11px', marginTop: '4px' }}>
                        训练正在进行中，请点击"开启实时监控"查看最新日志
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              {currentTraining.training_status === 'running' && (
                <Alert
                  message="实时日志监控"
                  description="训练正在进行中，日志会每2秒自动更新。您可以随时停止监控或关闭此窗口。"
                  type="info"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              )}
            </TabPane>
          </Tabs>
        )}
      </Modal>

      {/* 高级配置模态框 */}
      <Modal
        title="高级训练配置"
        open={configModalVisible}
        onCancel={() => setConfigModalVisible(false)}
        footer={null}
        width={700}
      >
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <SettingOutlined style={{ fontSize: '48px', color: '#ccc', marginBottom: '16px' }} />
          <h3>高级配置</h3>
          <p style={{ color: '#666' }}>高级训练参数配置功能开发中...</p>
        </div>
      </Modal>
    </div>
  );
};

export default TrainingV2; 