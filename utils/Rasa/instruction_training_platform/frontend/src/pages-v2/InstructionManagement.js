import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Form, Input, Select, App,
  Popconfirm, Tag, Space, Tooltip, Row, Col, Statistic, 
  Upload, Divider, List, Badge, Switch, Tabs, Collapse, Alert
} from 'antd';
import {
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  MessageOutlined,
  UploadOutlined,
  DownloadOutlined,
  EyeOutlined,
  CopyOutlined,
  ExclamationCircleOutlined,
  TagsOutlined,
  SearchOutlined,
  ReloadOutlined,
  ExperimentOutlined,
  RobotOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { instructionAPI, slotAPI, apiUtils, trainingAPI } from '../api-v2';
import { formatLocalTime } from '../utils/timeUtils';

// 导入子组件
import InstructionTab from '../components/InstructionTab';
import SlotTab from '../components/SlotTab';
import TestingTab from '../components/TestingTab';
import TrainingTab from '../components/TrainingTab';

const { Option } = Select;
const { TextArea } = Input;
const { Panel } = Collapse;

const InstructionManagement = ({ currentLibrary }) => {
  const { message } = App.useApp();
  const [instructions, setInstructions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [similarQuestionsModalVisible, setSimilarQuestionsModalVisible] = useState(false);
  const [batchImportModalVisible, setBatchImportModalVisible] = useState(false);
  const [editingInstruction, setEditingInstruction] = useState(null);
  const [currentInstruction, setCurrentInstruction] = useState(null);
  const [similarQuestions, setSimilarQuestions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [searchParams, setSearchParams] = useState({});
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [activeTab, setActiveTab] = useState('instructions');
  
  // 流程状态数据
  const [libraryStats, setLibraryStats] = useState({
    instruction_count: 0,
    slot_count: 0,
    enabled_instruction_count: 0,
    similar_question_count: 0
  });
  
  const [form] = Form.useForm();
  const [similarQuestionForm] = Form.useForm();
  const [completedTrainingRecords, setCompletedTrainingRecords] = useState([]);

  // 指令分类选项
  const instructionCategories = [
    { value: '智能家居', label: '智能家居' },
    { value: '音乐控制', label: '音乐控制' },
    { value: '天气查询', label: '天气查询' },
    { value: '时间查询', label: '时间查询' },
    { value: '设备控制', label: '设备控制' },
    { value: '信息查询', label: '信息查询' },
    { value: '娱乐功能', label: '娱乐功能' },
    { value: '其他', label: '其他' },
  ];

  // 检查是否选择了指令库
  if (!currentLibrary) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <MessageOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
          <h3>请先选择指令库</h3>
          <p style={{ color: '#666' }}>在开始管理指令数据之前，请先在指令库管理页面选择一个指令库。</p>
        </div>
      </Card>
    );
  }

  // 获取指令列表
  const fetchInstructions = async (params = {}) => {
    setLoading(true);
    try {
      const queryParams = {
        library_id: currentLibrary.id,
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        ...searchParams,
        ...params
      };
      
      const response = await instructionAPI.getInstructions(apiUtils.buildParams(queryParams));
      // 适配新的标准响应格式
      const responseData = response.data.data || response.data;
      const instructionList = responseData.instructions || response.data;
      const total = responseData.total || instructionList.length;
      
      setInstructions(instructionList || []);
      setPagination(prev => ({ ...prev, total }));
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取指令列表失败'));
    } finally {
      setLoading(false);
    }
  };

  // 获取指令分类
  const fetchCategories = async () => {
    try {
      const response = await instructionAPI.getCategories(currentLibrary.id);
      // 适配新的标准响应格式
      const responseData = response.data.data || response.data;
      setCategories(responseData.categories || []);
    } catch (error) {
      console.error('获取分类失败:', error);
    }
  };

  // 获取流程状态统计
  const fetchLibraryStats = async () => {
    if (!currentLibrary) return;
    
    try {
      const [instructionResponse, slotResponse] = await Promise.all([
        instructionAPI.getInstructions({ library_id: currentLibrary.id, limit: 9999 }),
        slotAPI.getSlots({ library_id: currentLibrary.id })
      ]);
      
      const instructionData = instructionResponse.data.data || instructionResponse.data;
      const slotData = slotResponse.data.data || slotResponse.data;
      
      const instructions = instructionData.instructions || [];
      const slots = slotData.slots || [];
      
      const similarQuestionCount = instructions.reduce((total, inst) => {
        return total + (inst.similar_questions?.length || 0);
      }, 0);
      
      const enabledInstructionCount = instructions.filter(inst => inst.is_enabled).length;
      
      setLibraryStats({
        instruction_count: instructions.length,
        slot_count: slots.length,
        enabled_instruction_count: enabledInstructionCount,
        similar_question_count: similarQuestionCount
      });
    } catch (error) {
      console.error('获取指令库统计失败:', error);
    }
  };

  // 获取已完成的训练记录
  const fetchCompletedTrainingRecords = async () => {
    if (!currentLibrary) return;
    
    try {
      const response = await trainingAPI.getTrainingRecords({
        library_id: currentLibrary.id,
        limit: 50
      });
      
      const data = response.data.data || response.data;
      const records = data.records || data.training_records || [];
      
      // 过滤出已完成的训练记录
      const completedRecords = records.filter(record => 
        record.training_status === 'completed' || record.status === 'completed'
      );
      
      setCompletedTrainingRecords(completedRecords);
      console.log('🎯 已完成的训练记录:', completedRecords);
    } catch (error) {
      console.error('获取训练记录失败:', error);
      setCompletedTrainingRecords([]);
    }
  };

  useEffect(() => {
    if (currentLibrary) {
      fetchInstructions();
      fetchCategories();
      fetchLibraryStats();
      fetchCompletedTrainingRecords();
    }
  }, [currentLibrary, pagination.current, pagination.pageSize]);

  // 搜索处理
  const handleSearch = (values) => {
    setSearchParams(values);
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchInstructions({ ...values, skip: 0 });
  };

  // 重置搜索
  const handleResetSearch = () => {
    setSearchParams({});
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchInstructions({ skip: 0 });
  };

  // 打开创建/编辑模态框
  const openModal = (instruction = null) => {
    setEditingInstruction(instruction);
    setModalVisible(true);
    
    if (instruction) {
      form.setFieldsValue({
        ...instruction,
        related_slot_ids: instruction.related_slot_ids ? 
          (typeof instruction.related_slot_ids === 'string' ? 
            JSON.parse(instruction.related_slot_ids) : instruction.related_slot_ids) : []
      });
    } else {
      form.resetFields();
    }
  };

  // 关闭模态框
  const closeModal = () => {
    setModalVisible(false);
    setEditingInstruction(null);
    form.resetFields();
  };

  // 保存指令
  const handleSave = async (values) => {
    try {
      const data = {
        ...values,
        library_id: currentLibrary.id,
        related_slot_ids: values.related_slot_ids ? JSON.stringify(values.related_slot_ids) : null
      };
      
      if (editingInstruction) {
        await instructionAPI.updateInstruction(editingInstruction.id, data);
        message.success('指令更新成功');
      } else {
        await instructionAPI.createInstruction(data);
        message.success('指令创建成功');
      }
      
      closeModal();
      fetchInstructions();
      fetchCategories(); // 刷新分类列表
    } catch (error) {
      message.error(apiUtils.handleError(error, '保存指令失败'));
    }
  };

  // 删除指令
  const handleDelete = async (instructionId) => {
    try {
      await instructionAPI.deleteInstruction(instructionId);
      message.success('指令删除成功');
      fetchInstructions();
    } catch (error) {
      message.error(apiUtils.handleError(error, '删除指令失败'));
    }
  };

  // 复制指令
  const handleCopy = (instruction) => {
    const newInstruction = {
      ...instruction,
      instruction_name: `${instruction.instruction_name}_副本`,
      instruction_code: `${instruction.instruction_code}_copy`
    };
    openModal(newInstruction);
  };

  // 管理相似问
  const manageSimilarQuestions = async (instruction) => {
    setCurrentInstruction(instruction);
    try {
      const response = await instructionAPI.getSimilarQuestions(instruction.id);
      setSimilarQuestions(response.data.similar_questions || []);
      setSimilarQuestionsModalVisible(true);
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取相似问失败'));
    }
  };

  // 添加相似问
  const handleAddSimilarQuestion = async (values) => {
    try {
      await instructionAPI.addSimilarQuestion(currentInstruction.id, values);
      message.success('相似问添加成功');
      similarQuestionForm.resetFields();
      
      // 刷新相似问列表
      const response = await instructionAPI.getSimilarQuestions(currentInstruction.id);
      setSimilarQuestions(response.data.similar_questions || []);
    } catch (error) {
      message.error(apiUtils.handleError(error, '添加相似问失败'));
    }
  };

  // 删除相似问
  const handleDeleteSimilarQuestion = async (questionId) => {
    try {
      await instructionAPI.deleteSimilarQuestion(currentInstruction.id, questionId);
      message.success('相似问删除成功');
      
      // 刷新相似问列表
      const response = await instructionAPI.getSimilarQuestions(currentInstruction.id);
      setSimilarQuestions(response.data.similar_questions || []);
    } catch (error) {
      message.error(apiUtils.handleError(error, '删除相似问失败'));
    }
  };

  // 批量导入
  const handleBatchImport = async (formData) => {
    try {
      const response = await instructionAPI.batchImport(formData);
      message.success(`批量导入成功：${response.data.success_count} 条记录`);
      setBatchImportModalVisible(false);
      fetchInstructions();
    } catch (error) {
      message.error(apiUtils.handleError(error, '批量导入失败'));
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '指令名称',
      dataIndex: 'instruction_name',
      key: 'instruction_name',
      width: 200,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            编码: {record.instruction_code}
          </div>
        </div>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category) => (
        <Tag color="blue">{category || '未分类'}</Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'instruction_desc',
      key: 'instruction_desc',
      width: 200,
      ellipsis: { showTitle: false },
      render: (desc) => (
        <Tooltip title={desc}>
          {desc || '-'}
        </Tooltip>
      ),
    },
    {
      title: '词槽关联',
      dataIndex: 'is_slot_related',
      key: 'is_slot_related',
      width: 100,
      render: (isRelated) => (
        <Tag color={isRelated ? 'green' : 'gray'}>
          {isRelated ? '已关联' : '未关联'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      width: 80,
      render: (enabled) => (
        <Badge 
          status={enabled ? 'success' : 'default'} 
          text={enabled ? '启用' : '禁用'} 
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_time',
      key: 'created_time',
      width: 150,
      render: (time) => formatLocalTime(time),
    },
    {
      title: '操作',
      key: 'actions',
      width: 250,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => manageSimilarQuestions(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => openModal(record)}
            />
          </Tooltip>
          <Tooltip title="复制">
            <Button
              type="text"
              icon={<CopyOutlined />}
              onClick={() => handleCopy(record)}
            />
          </Tooltip>
          <Tooltip title="相似问">
            <Button
              type="text"
              icon={<MessageOutlined />}
              onClick={() => manageSimilarQuestions(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个指令吗？"
            description="删除后将无法恢复。"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 分页处理
  const handleTableChange = (pagination) => {
    setPagination(pagination);
  };

  // Tab切换处理
  const handleTabChange = (key) => {
    setActiveTab(key);
    // 切换Tab时刷新统计数据
    setTimeout(() => {
      fetchLibraryStats();
      fetchCompletedTrainingRecords();
    }, 100);
  };

  // 检查流程状态
  const getProcessStatus = () => {
    const hasInstructions = libraryStats.instruction_count > 0;
    const hasSlots = libraryStats.slot_count > 0;
    const hasMinimumData = libraryStats.instruction_count >= 2;
    const hasCompletedTraining = completedTrainingRecords.length > 0;
    
    return {
      step1_instructions: hasInstructions,
      step2_slots: hasSlots,
      step3_training_ready: hasMinimumData,
      step4_testing_ready: hasCompletedTraining // 基于实际的训练完成状态
    };
  };

  // 渲染流程状态指示器
  const renderProcessIndicator = () => {
    const status = getProcessStatus();
    
    return (
      <Card style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
            📋 训练流程状态
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            {/* 步骤1：指令管理 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {status.step1_instructions ? (
                <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
              ) : (
                <ClockCircleOutlined style={{ color: '#faad14', fontSize: '16px' }} />
              )}
              <span style={{ color: status.step1_instructions ? '#52c41a' : '#faad14' }}>
                ① 指令数据 ({libraryStats.instruction_count})
              </span>
            </div>

            {/* 步骤2：词槽管理 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {status.step2_slots ? (
                <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
              ) : (
                <ClockCircleOutlined style={{ color: '#faad14', fontSize: '16px' }} />
              )}
              <span style={{ color: status.step2_slots ? '#52c41a' : '#faad14' }}>
                ② 词槽数据 ({libraryStats.slot_count})
              </span>
            </div>

            {/* 步骤3：模型训练 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {status.step3_training_ready ? (
                <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
              ) : (
                <ExclamationCircleOutlined style={{ color: '#ff4d4f', fontSize: '16px' }} />
              )}
              <span style={{ color: status.step3_training_ready ? '#52c41a' : '#ff4d4f' }}>
                ③ 训练就绪 {status.step3_training_ready ? '✓' : '(需≥2个指令)'}
              </span>
            </div>

            {/* 步骤4：指令测试 */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {status.step4_testing_ready ? (
                <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '16px' }} />
              ) : (
                <ClockCircleOutlined style={{ color: '#d9d9d9', fontSize: '16px' }} />
              )}
              <span style={{ color: status.step4_testing_ready ? '#52c41a' : '#d9d9d9' }}>
                ④ 测试就绪 {status.step4_testing_ready ? `(${completedTrainingRecords.length}个可用版本)` : '(需要训练版本)'}
              </span>
            </div>
          </div>
        </div>
      </Card>
    );
  };

  // Tab项配置 - 按业务流程排序，包含权限控制
  const getTabItems = () => {
    const status = getProcessStatus();
    
    return [
      {
        key: 'instructions',
        label: (
          <span>
            <MessageOutlined />
            指令管理
            <span style={{ fontSize: '12px', color: '#1890ff', marginLeft: '4px' }}>①</span>
            {status.step1_instructions && (
              <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '12px', marginLeft: '4px' }} />
            )}
          </span>
        ),
        children: <InstructionTab currentLibrary={currentLibrary} />
      },
      {
        key: 'slots',
        label: (
          <span>
            <TagsOutlined />
            词槽管理
            <span style={{ fontSize: '12px', color: '#1890ff', marginLeft: '4px' }}>②</span>
            {status.step2_slots && (
              <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '12px', marginLeft: '4px' }} />
            )}
          </span>
        ),
        children: <SlotTab currentLibrary={currentLibrary} />
      },
      {
        key: 'training',
        label: (
          <span>
            <RobotOutlined />
            模型训练
            <span style={{ fontSize: '12px', color: '#1890ff', marginLeft: '4px' }}>③</span>
            {!status.step3_training_ready && (
              <ExclamationCircleOutlined style={{ color: '#ff4d4f', fontSize: '12px', marginLeft: '4px' }} />
            )}
          </span>
        ),
        children: status.step3_training_ready ? (
          <TrainingTab currentLibrary={currentLibrary} />
        ) : (
          <Card>
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <ExclamationCircleOutlined style={{ fontSize: '64px', color: '#ff4d4f', marginBottom: '16px' }} />
              <h3>训练条件不满足</h3>
              <p style={{ color: '#666', marginBottom: '16px' }}>
                开始模型训练需要满足以下条件：
              </p>
              <div style={{ textAlign: 'left', maxWidth: '400px', margin: '0 auto' }}>
                <div style={{ marginBottom: '8px' }}>
                  {status.step1_instructions ? (
                    <span style={{ color: '#52c41a' }}>✓ 至少有1个指令数据</span>
                  ) : (
                    <span style={{ color: '#ff4d4f' }}>✗ 至少有1个指令数据</span>
                  )}
                </div>
                <div style={{ marginBottom: '8px' }}>
                  <span style={{ color: libraryStats.instruction_count >= 2 ? '#52c41a' : '#ff4d4f' }}>
                    {libraryStats.instruction_count >= 2 ? '✓' : '✗'} 至少有2个不同的指令（当前: {libraryStats.instruction_count}）
                  </span>
                </div>
                <div>
                  {status.step2_slots ? (
                    <span style={{ color: '#52c41a' }}>✓ 建议配置词槽数据（可选）</span>
                  ) : (
                    <span style={{ color: '#faad14' }}>⚠ 建议配置词槽数据（可选）</span>
                  )}
                </div>
              </div>
              <div style={{ marginTop: '24px' }}>
                <Button 
                  type="primary" 
                  onClick={() => setActiveTab('instructions')}
                >
                  去添加指令数据
                </Button>
              </div>
            </div>
          </Card>
        )
      },
      {
        key: 'testing',
        label: (
          <span>
            <ExperimentOutlined />
            指令测试
            <span style={{ fontSize: '12px', color: '#1890ff', marginLeft: '4px' }}>④</span>
            {status.step4_testing_ready ? (
              <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '12px', marginLeft: '4px' }} />
            ) : (
              <ClockCircleOutlined style={{ color: '#d9d9d9', fontSize: '12px', marginLeft: '4px' }} />
            )}
          </span>
        ),
        children: status.step4_testing_ready ? (
          <TestingTab 
            currentLibrary={currentLibrary} 
            availableModels={completedTrainingRecords}
          />
        ) : (
          <Card>
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <ClockCircleOutlined style={{ fontSize: '64px', color: '#d9d9d9', marginBottom: '16px' }} />
              <h3>等待训练完成</h3>
              <p style={{ color: '#666', marginBottom: '16px' }}>
                指令测试需要先完成模型训练并生成可用版本
              </p>
              <div style={{ textAlign: 'left', maxWidth: '400px', margin: '0 auto' }}>
                <div style={{ marginBottom: '8px' }}>
                  {status.step1_instructions ? (
                    <span style={{ color: '#52c41a' }}>✓ 指令数据准备完成</span>
                  ) : (
                    <span style={{ color: '#ff4d4f' }}>✗ 指令数据准备</span>
                  )}
                </div>
                <div style={{ marginBottom: '8px' }}>
                  {status.step2_slots ? (
                    <span style={{ color: '#52c41a' }}>✓ 词槽数据准备完成</span>
                  ) : (
                    <span style={{ color: '#faad14' }}>⚠ 词槽数据准备（可选）</span>
                  )}
                </div>
                <div style={{ marginBottom: '8px' }}>
                  {status.step3_training_ready ? (
                    <span style={{ color: '#52c41a' }}>✓ 训练条件满足</span>
                  ) : (
                    <span style={{ color: '#ff4d4f' }}>✗ 训练条件不满足</span>
                  )}
                </div>
                <div>
                  {status.step4_testing_ready ? (
                    <span style={{ color: '#52c41a' }}>✓ 训练已完成</span>
                  ) : (
                    <span style={{ color: '#d9d9d9' }}>⏳ 等待训练完成</span>
                  )}
                </div>
              </div>
              <div style={{ marginTop: '24px' }}>
                <Button 
                  type="primary" 
                  onClick={() => setActiveTab(status.step3_training_ready ? 'training' : 'instructions')}
                >
                  {status.step3_training_ready ? '去开始训练' : '去完善数据'}
                </Button>
              </div>
            </div>
          </Card>
        )
      }
    ];
  };

  return (
    <div className="instruction-management-v2">
      {/* 流程状态指示器 */}
      {renderProcessIndicator()}
      
      {/* Tab导航 */}
      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={handleTabChange}
          type="card"
          tabPosition="top"
          items={getTabItems()}
        />
      </Card>
    </div>
  );
};

export default InstructionManagement; 