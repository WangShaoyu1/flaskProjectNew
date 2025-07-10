import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Modal, Form, Input, Select, App,
  Popconfirm, Tag, Space, Tooltip, Row, Col, Statistic, 
  Upload, Divider, List, Badge, Switch, Collapse, Drawer, Dropdown
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
  DownOutlined,
  CheckOutlined,
  CloseOutlined,
  SwapOutlined,
  CheckCircleOutlined,
  StopOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { instructionAPI, slotAPI, apiUtils } from '../api-v2';
import { formatLocalTime } from '../utils/timeUtils';
import { safeTableDataSource } from '../utils/dataSourceUtils';

const { Option } = Select;
const { TextArea } = Input;
const { Panel } = Collapse;

const InstructionTab = ({ currentLibrary }) => {
  const { message } = App.useApp();
  const [instructions, setInstructions] = useState([]);
  const [slots, setSlots] = useState([]); // 添加词槽数据
  const [libraryStats, setLibraryStats] = useState({
    total_instructions: 0,
    enabled_instructions: 0,
    disabled_instructions: 0,
    total_similar_questions: 0,
    total_related_slots: 0
  }); // 添加指令库统计信息
  // 解析关联词槽ID的通用函数
  const parseRelatedSlotIds = (relatedSlotIds) => {
    if (!relatedSlotIds) return [];
    
    try {
      if (typeof relatedSlotIds === 'string') {
        const trimmedValue = relatedSlotIds.trim();
        
        if (trimmedValue.startsWith('[') && trimmedValue.endsWith(']')) {
          // 看起来是JSON数组，尝试解
          return JSON.parse(trimmedValue);
        } else if (trimmedValue.startsWith('{') && trimmedValue.endsWith('}')) {
          // 看起来是JSON对象，尝试解
          const parsed = JSON.parse(trimmedValue);
          return Array.isArray(parsed) ? parsed : [];
        } else if (trimmedValue.includes(',')) {
          // 看起来是逗号分隔的字符串，按逗号分割
          return trimmedValue.split(',').map(id => {
            const numId = parseInt(id.trim());
            return isNaN(numId) ? id.trim() : numId;
          }).filter(id => id !== '');
        } else if (trimmedValue !== '') {
          // 单个值，尝试转换为数字或保持字符
          const numId = parseInt(trimmedValue);
          return [isNaN(numId) ? trimmedValue : numId];
        } else {
          return [];
        }
      } else if (Array.isArray(relatedSlotIds)) {
        // 如果已经是数组，直接使用
        return relatedSlotIds;
      } else if (typeof relatedSlotIds === 'number') {
        // 如果是数字，转换为数
        return [relatedSlotIds];
      }
      
      return [];
    } catch (error) {
      console.error('解析关联词槽失败:', error, '原始数据:', relatedSlotIds);
      return [];
    }
  };
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [similarQuestionsDrawerVisible, setSimilarQuestionsDrawerVisible] = useState(false);
  const [batchImportModalVisible, setBatchImportModalVisible] = useState(false);
  const [batchImportLoading, setBatchImportLoading] = useState(false);
  
  // 批量操作相关状态
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [batchDeleteLoading, setBatchDeleteLoading] = useState(false);
  const [editingInstruction, setEditingInstruction] = useState(null);
  const [currentInstruction, setCurrentInstruction] = useState(null);
  const [similarQuestions, setSimilarQuestions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [searchParams, setSearchParams] = useState({});
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [switchLoading, setSwitchLoading] = useState({}); // 添加switch加载状
  const [editingSimilarQuestionId, setEditingSimilarQuestionId] = useState(null);
  const [editingSimilarQuestionText, setEditingSimilarQuestionText] = useState('');
  
  const [form] = Form.useForm();
  const [similarQuestionForm] = Form.useForm();

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
      
      // 直接使用指令列表，相似问数量从后端API返回
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

  // 获取词槽列表
  const fetchSlots = async () => {
    try {
      const response = await slotAPI.getSlots({ library_id: currentLibrary.id });
      // 适配标准响应格式，类似指令列表的处理
      const responseData = response.data.data || response.data;
      const slotsData = Array.isArray(responseData) ? responseData : [];
      console.log('获取到的词槽数据:', slotsData);
      setSlots(slotsData);
    } catch (error) {
      console.error('获取词槽列表失败:', error);
      setSlots([]); // 确保出错时也设置为空数组
    }
  };

  // 获取指令库统计信息
  const fetchLibraryStats = async () => {
    try {
      // 获取所有指令数据（不分页）
      const response = await instructionAPI.getInstructions(apiUtils.buildParams({
        library_id: currentLibrary.id,
        skip: 0,
        limit: 9999 // 获取所有数据
      }));
      
      // 适配新的标准响应格式
      const responseData = response.data.data || response.data;
      const allInstructions = responseData.instructions || responseData || [];
      
      // 计算统计信息
      const totalInstructions = allInstructions.length;
      const enabledInstructions = allInstructions.filter(item => item.is_enabled).length;
      const disabledInstructions = totalInstructions - enabledInstructions;
      const totalSimilarQuestions = allInstructions.reduce((sum, item) => sum + (item.similar_questions_count || 0), 0);
      const totalRelatedSlots = allInstructions.reduce((sum, item) => {
        const relatedSlotIds = item.related_slot_ids ? parseRelatedSlotIds(item.related_slot_ids) : [];
        return sum + relatedSlotIds.length;
      }, 0);
      
      setLibraryStats({
        total_instructions: totalInstructions,
        enabled_instructions: enabledInstructions,
        disabled_instructions: disabledInstructions,
        total_similar_questions: totalSimilarQuestions,
        total_related_slots: totalRelatedSlots
      });
    } catch (error) {
      console.error('获取指令库统计信息失败:', error);
    }
  };

  useEffect(() => {
    if (currentLibrary) {
      fetchInstructions();
      fetchCategories();
      fetchSlots();
      fetchLibraryStats();
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
      // 处理关联词槽的回
      const relatedSlotIds = parseRelatedSlotIds(instruction.related_slot_ids);
      
      form.setFieldsValue({
        ...instruction,
        related_slot_ids: relatedSlotIds
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
      fetchLibraryStats(); // 刷新统计信息
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
      fetchLibraryStats(); // 刷新统计信息
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

  // 管理相似
  const manageSimilarQuestions = async (instruction) => {
    setCurrentInstruction(instruction);
    try {
      const response = await instructionAPI.getSimilarQuestions(instruction.id);
      // 适配新的标准响应格式
      const responseData = response.data.data || response.data;
      setSimilarQuestions(responseData.similar_questions || []);
      setSimilarQuestionsDrawerVisible(true);
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取相似问失败'));
    }
  };

  // 添加相似
  const handleAddSimilarQuestion = async (values) => {
    try {
      await instructionAPI.addSimilarQuestion(currentInstruction.id, values);
      message.success('相似问添加成功');
      similarQuestionForm.resetFields();
      
      // 刷新相似问列表
      const response = await instructionAPI.getSimilarQuestions(currentInstruction.id);
      const responseData = response.data.data || response.data;
      setSimilarQuestions(responseData.similar_questions || []);
      
      // 刷新指令列表以更新相似问数量
      fetchInstructions();
      fetchLibraryStats(); // 刷新统计信息
    } catch (error) {
      message.error(apiUtils.handleError(error, '添加相似问失败'));
    }
  };

  // 删除相似
  const handleDeleteSimilarQuestion = async (questionId) => {
    try {
      await instructionAPI.deleteSimilarQuestion(currentInstruction.id, questionId);
      message.success('相似问删除成功');
      
      // 刷新相似问列表
      const response = await instructionAPI.getSimilarQuestions(currentInstruction.id);
      const responseData = response.data.data || response.data;
      setSimilarQuestions(responseData.similar_questions || []);
      
      // 刷新指令列表以更新相似问数量
      fetchInstructions();
      fetchLibraryStats(); // 刷新统计信息
    } catch (error) {
      message.error(apiUtils.handleError(error, '删除相似问失败'));
    }
  };

  // 开始编辑相似问
  const startEditSimilarQuestion = (question) => {
    setEditingSimilarQuestionId(question.id);
    setEditingSimilarQuestionText(question.question_text);
  };

  // 取消编辑相似
  const cancelEditSimilarQuestion = () => {
    setEditingSimilarQuestionId(null);
    setEditingSimilarQuestionText('');
  };

  // 保存编辑的相似问
  const saveEditSimilarQuestion = async () => {
    if (!editingSimilarQuestionText.trim()) {
      message.error('相似问内容不能为空');
      return;
    }
    
    try {
      await instructionAPI.updateSimilarQuestion(
        currentInstruction.id, 
        editingSimilarQuestionId, 
        { question_text: editingSimilarQuestionText.trim() }
      );
      message.success('相似问更新成功');
      
      // 刷新相似问列表
      const response = await instructionAPI.getSimilarQuestions(currentInstruction.id);
      const responseData = response.data.data || response.data;
      setSimilarQuestions(responseData.similar_questions || []);
      
      // 取消编辑状态
      cancelEditSimilarQuestion();
    } catch (error) {
      message.error(apiUtils.handleError(error, '更新相似问失败'));
    }
  };

  // 下载模板
  const handleDownloadTemplate = async () => {
    try {
      const response = await instructionAPI.downloadTemplate();
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = '指令导入模板.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      message.success('模板下载成功');
    } catch (error) {
      message.error(apiUtils.handleError(error, '模板下载失败'));
    }
  };

  // 批量导入
  const handleBatchImport = async (file) => {
    if (!currentLibrary) {
      message.error('请先选择指令库');
      return;
    }

    setBatchImportLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('library_id', currentLibrary.id);

      const response = await instructionAPI.batchImport(formData);
      
      // 适配新的标准响应格式
      const responseData = response.data.data || response.data;
      const successCount = responseData.success_count || 0;
      const similarQuestionsCount = responseData.similar_questions_count || 0;
      
      message.success(`批量导入成功！指令 ${successCount} 条，相似问 ${similarQuestionsCount} 条`);
      setBatchImportModalVisible(false);
      fetchInstructions();
      fetchLibraryStats(); // 刷新统计信息
    } catch (error) {
      message.error(apiUtils.handleError(error, '批量导入失败'));
    } finally {
      setBatchImportLoading(false);
    }
  };

  // 处理状态变化
  const handleStatusChange = async (instructionId, enabled) => {
    // 设置当前switch为加载状态
    setSwitchLoading(prev => ({ ...prev, [instructionId]: true }));
    
    // 保存原始状态，用于错误恢复
    const originalInstruction = instructions.find(inst => inst.id === instructionId);
    const originalEnabled = originalInstruction?.is_enabled;
    
    try {
      // 乐观更新：先更新UI状态，提供更好的用户体验
      setInstructions(prev => 
        prev.map(instruction => 
          instruction.id === instructionId 
            ? { ...instruction, is_enabled: enabled }
            : instruction
        )
      );
      
      // 调用API更新指令状态
      await instructionAPI.updateInstruction(instructionId, { is_enabled: enabled });
      
      message.success(`指令${enabled ? '启用' : '禁用'}`);
      fetchLibraryStats(); // 刷新统计信息
    } catch (error) {
      message.error(apiUtils.handleError(error, '状态更新失败'));
      
      // 如果更新失败，恢复原始状态
      setInstructions(prev => 
        prev.map(instruction => 
          instruction.id === instructionId 
            ? { ...instruction, is_enabled: originalEnabled }
            : instruction
        )
      );
    } finally {
      // 移除加载状态
      setSwitchLoading(prev => ({ ...prev, [instructionId]: false }));
    }
  };

  // 批量操作函数
  const handleSelectChange = (newSelectedRowKeys) => {
    setSelectedRowKeys(newSelectedRowKeys);
  };

  const handleSelectAll = () => {
    const allKeys = instructions.map(instruction => instruction.id);
    setSelectedRowKeys(allKeys);
  };

  const handleSelectNone = () => {
    setSelectedRowKeys([]);
  };

  const handleSelectInvert = () => {
    const allKeys = instructions.map(instruction => instruction.id);
    const newSelectedKeys = allKeys.filter(key => !selectedRowKeys.includes(key));
    setSelectedRowKeys(newSelectedKeys);
  };

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的指令');
      return;
    }

    setBatchDeleteLoading(true);
    try {
      // 并行删除所有选中的指令
      const deletePromises = selectedRowKeys.map(instructionId => 
        instructionAPI.deleteInstruction(instructionId)
      );
      
      await Promise.all(deletePromises);
      
      message.success(`成功删除 ${selectedRowKeys.length} 个指令`);
      setSelectedRowKeys([]);
      fetchInstructions();
      fetchLibraryStats();
    } catch (error) {
      message.error(apiUtils.handleError(error, '批量删除失败'));
    } finally {
      setBatchDeleteLoading(false);
    }
  };



  // 表格列定义
  const columns = [
    {
      title: '指令名称',
      dataIndex: 'instruction_name',
      key: 'instruction_name',
      width: 150,
      render: (text) => (
        <div style={{ fontWeight: 'bold' }}>{text}</div>
      ),
    },
    {
      title: '指令编码',
      dataIndex: 'instruction_code',
      key: 'instruction_code',
      width: 150,
      render: (code) => (
        <span style={{ fontFamily: 'monospace', fontSize: '12px', color: '#666' }}>
          {code}
        </span>
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
      title: '相似问,',
      key: 'similar_questions',
      width: 100,
      align: 'center',
      render: (_, record) => (
        <Button
          type="text"
          size="small"
          onClick={() => manageSimilarQuestions(record)}
          style={{ 
            color: record.similar_questions_count > 0 ? '#1890ff' : '#999',
            fontWeight: record.similar_questions_count > 0 ? 'bold' : 'normal'
          }}
        >
          {record.similar_questions_count || 0}
        </Button>
      ),
    },
    {
      title: '关联',
      key: 'related_slots',
      width: 200,
      render: (_, record) => {
        let relatedSlotIds = [];
        if (record.related_slot_ids) {
          relatedSlotIds = parseRelatedSlotIds(record.related_slot_ids);
        }
        
        if (relatedSlotIds.length === 0) {
          return <span style={{ color: '#999' }}>无关</span>;
        }
        
        // 根据ID或名称找到对应的词槽名称
        const relatedSlotNames = relatedSlotIds.map(idOrName => {
          // 如果是数字ID，通过ID查找
          if (typeof idOrName === 'number') {
            const slot = (slots || []).find(s => s.id === idOrName);
            return slot ? slot.slot_name : `${idOrName}`;
          }
          // 如果是字符串，可能是词槽名称或ID字符串
          else if (typeof idOrName === 'string') {
            // 先尝试作为ID查找
            const numId = parseInt(idOrName);
            if (!isNaN(numId)) {
              const slot = (slots || []).find(s => s.id === numId);
              if (slot) return slot.slot_name;
            }
            // 如果不是数字ID，直接作为词槽名称返回
            return idOrName;
          }
          return `${idOrName}`;
        });
        
        return (
          <div>
            {relatedSlotNames.map((name, index) => (
              <Tag key={index} color="green" style={{ marginBottom: 2 }}>
                {name}
              </Tag>
            ))}
          </div>
        );
      },
    },
    {
      title: '状态,',
      dataIndex: 'is_enabled',
      key: 'is_enabled',
      width: 100,
      align: 'center',
      render: (enabled, record) => (
        <Switch
          checked={enabled}
          onChange={(checked) => handleStatusChange(record.id, checked)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
          loading={switchLoading[record.id]}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
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
          <Popconfirm
            title="确定要删除这个指令吗？"
            description="删除后将无法恢复"
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

  return (
    <div className="instruction-tab">
      {/* 统计信息 - 精简数值条 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 16px',
        background: 'linear-gradient(90deg, #f6f9fc 0%, #ffffff 100%)',
        borderRadius: '6px',
        border: '1px solid #e8e8e8',
        marginBottom: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <span style={{ fontSize: '14px', color: '#666', fontWeight: '500' }}>📊 数据统计</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <MessageOutlined style={{ color: '#1890ff', fontSize: '14px' }} />
            <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
              {libraryStats.total_instructions}
            </span>
            <span style={{ fontSize: '12px', color: '#999' }}>总指令</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: '14px' }} />
            <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#52c41a' }}>
              {libraryStats.enabled_instructions}
            </span>
            <span style={{ fontSize: '12px', color: '#999' }}>启用</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <StopOutlined style={{ color: '#f5222d', fontSize: '14px' }} />
            <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#f5222d' }}>
              {libraryStats.disabled_instructions}
            </span>
            <span style={{ fontSize: '12px', color: '#999' }}>禁用</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <TagsOutlined style={{ color: '#fa8c16', fontSize: '14px' }} />
            <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#fa8c16' }}>
              {libraryStats.total_related_slots}
            </span>
            <span style={{ fontSize: '12px', color: '#999' }}>词槽</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <QuestionCircleOutlined style={{ color: '#722ed1', fontSize: '14px' }} />
            <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#722ed1' }}>
              {libraryStats.total_similar_questions}
            </span>
            <span style={{ fontSize: '12px', color: '#999' }}>相似问</span>
          </div>
        </div>
        
        <div style={{ fontSize: '12px', color: '#999' }}>
          ⏰ 最后更新: {formatLocalTime(new Date())}
        </div>
      </div>

      {/* 搜索和操作栏 */}
      <div style={{ marginBottom: 24, padding: 16, background: '#fafafa', borderRadius: 6 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 16 }}>
          <Form
            layout="inline"
            onFinish={handleSearch}
            style={{ flex: 1 }}
          >
            <Form.Item name="search" label="搜索">
              <Input placeholder="指令名称或编码" prefix={<SearchOutlined />} autoComplete="off" />
            </Form.Item>
            <Form.Item name="category" label="分类">
              <Select placeholder="选择分类" allowClear style={{ width: 120 }}>
                {instructionCategories.map(cat => (
                  <Option key={cat.value} value={cat.value}>{cat.label}</Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item name="is_enabled" label="状态">
              <Select placeholder="状态" allowClear style={{ width: 100 }}>
                <Option value={true}>启用</Option>
                <Option value={false}>禁用</Option>
              </Select>
            </Form.Item>
            <Form.Item>
              <Space>
                <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
                  搜索
                </Button>
                <Button onClick={handleResetSearch} icon={<ReloadOutlined />}>
                  重置
                </Button>
              </Space>
            </Form.Item>
          </Form>
          
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => openModal()}
            >
              新增指令
            </Button>
            <Button
              icon={<UploadOutlined />}
              onClick={() => setBatchImportModalVisible(true)}
            >
              批量导入
            </Button>
            <Button
              icon={<DownloadOutlined />}
            >
              导出数据
            </Button>
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'selectAll',
                    label: '全选',
                    icon: <CheckOutlined />,
                    disabled: instructions.length === 0,
                    onClick: handleSelectAll,
                  },
                  {
                    key: 'selectNone',
                    label: '取消选择',
                    icon: <CloseOutlined />,
                    disabled: selectedRowKeys.length === 0,
                    onClick: handleSelectNone,
                  },
                  {
                    key: 'selectInvert',
                    label: '反选',
                    icon: <SwapOutlined />,
                    disabled: instructions.length === 0,
                    onClick: handleSelectInvert,
                  },
                  {
                    type: 'divider',
                  },
                  {
                    key: 'batchDelete',
                    label: `批量删除 (${selectedRowKeys.length})`,
                    icon: <DeleteOutlined />,
                    disabled: selectedRowKeys.length === 0,
                    danger: true,
                    onClick: () => {
                      Modal.confirm({
                        title: '确定要删除选中的指令吗？',
                        content: `将删除 ${selectedRowKeys.length} 个指令，此操作不可恢复。`,
                        okText: '确定',
                        cancelText: '取消',
                        onOk: handleBatchDelete,
                      });
                    },
                  },
                ],
              }}
              placement="bottomLeft"
            >
              <Button>
                批量操作 <DownOutlined />
              </Button>
            </Dropdown>
          </Space>
        </div>
      </div>

      {/* 指令列表 */}
      <Table
        columns={columns}
        dataSource={safeTableDataSource(instructions)}
        rowKey="id"
        loading={loading}
        rowSelection={{
          selectedRowKeys,
          onChange: handleSelectChange,
          selections: [
            Table.SELECTION_ALL,
            Table.SELECTION_INVERT,
            Table.SELECTION_NONE,
          ],
        }}
        pagination={{
          ...pagination,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共${total} 条记录`,
        }}
        onChange={handleTableChange}
        scroll={{ x: 1400 }}
      />

      {/* 创建/编辑模态框 */}
      <Modal
        title={editingInstruction ? '编辑指令' : '新增指令'}
        open={modalVisible}
        onCancel={closeModal}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="instruction_name"
                label="指令名称"
                rules={[{ required: true, message: '请输入指令名称' }]}
              >
                <Input placeholder="请输入指令名称" autoComplete="off" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="instruction_code"
                label="指令编码"
                rules={[{ required: true, message: '请输入指令编码' }]}
              >
                <Input placeholder="请输入指令编码" autoComplete="off" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="category" label="指令分类">
                <Select placeholder="选择分类" allowClear>
                  {instructionCategories.map(cat => (
                    <Option key={cat.value} value={cat.value}>{cat.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_enabled" label="启用状态" valuePropName="checked">
                <Switch checkedChildren="启用" unCheckedChildren="禁用" defaultChecked />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="instruction_desc" label="指令描述">
            <TextArea rows={3} placeholder="请输入指令描述" />
          </Form.Item>

          <Form.Item name="is_slot_related" label="是否关联词槽" valuePropName="checked">
            <Switch checkedChildren="是" unCheckedChildren="否" />
          </Form.Item>

          <Form.Item name="related_slot_ids" label="关联词槽">
            <Select
              mode="multiple"
              placeholder="选择关联的词槽"
              allowClear
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {(slots || []).map(slot => (
                <Option key={slot.id} value={slot.id}>
                  {slot.slot_name} ({slot.slot_name_en})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="success_response" label="成功话术">
                <TextArea rows={2} placeholder="执行成功时的回复话术" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="failure_response" label="失败话术">
                <TextArea rows={2} placeholder="执行失败时的回复话术" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={closeModal}>取消</Button>
              <Button type="primary" htmlType="submit">
                {editingInstruction ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 相似问管理抽屉 */}
      <Drawer
        title={`相似问管理- ${currentInstruction?.instruction_name}`}
        placement="right"
        onClose={() => setSimilarQuestionsDrawerVisible(false)}
        open={similarQuestionsDrawerVisible}
        width={600}
        extra={
          <Space>
            <Button 
              type="primary" 
              onClick={() => setSimilarQuestionsDrawerVisible(false)}
            >
              完成
            </Button>
          </Space>
        }
      >
        <Form
          form={similarQuestionForm}
          layout="vertical"
          onFinish={handleAddSimilarQuestion}
          style={{ marginBottom: 24 }}
        >
          <Form.Item
            name="question_text"
            label="添加新相似问"
            rules={[{ required: true, message: '请输入相似问' }]}
          >
            <Input.TextArea 
              placeholder="请输入相似问内容" 
              autoComplete="off"
              autoSize={{ minRows: 2, maxRows: 4 }}
            />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<PlusOutlined />} block>
              添加相似问
            </Button>
          </Form.Item>
        </Form>

        <Divider>相似问列表</Divider>

        <List
          dataSource={similarQuestions}
          renderItem={(item, index) => (
            <List.Item
              style={{ 
                padding: '12px 0',
                borderBottom: '1px solid #f0f0f0'
              }}
            >
              <div style={{ width: '100%' }}>
                <div style={{ 
                  display: 'flex', 
                  justifyContent: 'space-between', 
                  alignItems: 'flex-start',
                  marginBottom: '8px'
                }}>
                  <div style={{ flex: 1, marginRight: '12px' }}>
                    {editingSimilarQuestionId === item.id ? (
                      <Input.TextArea
                        value={editingSimilarQuestionText}
                        onChange={(e) => setEditingSimilarQuestionText(e.target.value)}
                        autoSize={{ minRows: 2, maxRows: 4 }}
                        style={{ marginBottom: '8px' }}
                      />
                    ) : (
                      <div style={{ 
                        padding: '8px 12px',
                        backgroundColor: '#f8f9fa',
                        borderRadius: '6px',
                        border: '1px solid #e9ecef',
                        lineHeight: '1.5'
                      }}>
                        {item.question_text}
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {editingSimilarQuestionId === item.id ? (
                      <>
                        <Button
                          type="primary"
                          size="small"
                          onClick={saveEditSimilarQuestion}
                        >
                          保存
                        </Button>
                        <Button
                          size="small"
                          onClick={cancelEditSimilarQuestion}
                        >
                          取消
                        </Button>
                      </>
                    ) : (
                      <>
                        <Button
                          type="text"
                          size="small"
                          icon={<EditOutlined />}
                          onClick={() => startEditSimilarQuestion(item)}
                        />
                        <Popconfirm
                          title="确定要删除这个相似问吗？"
                          onConfirm={() => handleDeleteSimilarQuestion(item.id)}
                          okText="确定"
                          cancelText="取消"
                        >
                          <Button
                            type="text"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                          />
                        </Popconfirm>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </List.Item>
          )}
          locale={{ emptyText: '暂无相似问，点击上方按钮添加' }}
        />
      </Drawer>

      {/* 批量导入模态框 */}
      <Modal
        title="批量导入指令"
        open={batchImportModalVisible}
        onCancel={() => !batchImportLoading && setBatchImportModalVisible(false)}
        footer={null}
        width={600}
        closable={!batchImportLoading}
        maskClosable={!batchImportLoading}
      >
        <div style={{ textAlign: 'center', padding: '40px' }}>
          {batchImportLoading ? (
            <>
              <div style={{ fontSize: '64px', color: '#1890ff', marginBottom: '16px' }}>
                <span className="anticon anticon-loading anticon-spin">
                  <svg viewBox="0 0 1024 1024" focusable="false" data-icon="loading" width="1em" height="1em" fill="currentColor" aria-hidden="true">
                    <path d="M988 548c-19.9 0-36-16.1-36-36 0-59.4-11.6-117-34.6-171.3a440.45 440.45 0 00-94.3-139.9 437.71 437.71 0 00-139.9-94.3C637 83.6 579.4 72 520 72s-117 11.6-171.3 34.6a440.45 440.45 0 00-139.9 94.3 437.71 437.71 0 00-94.3 139.9C91.6 395 80 452.6 80 512s11.6 117 34.6 171.3a440.45 440.45 0 0094.3 139.9 437.71 437.71 0 00139.9 94.3C395 940.4 452.6 952 512 952s117-11.6 171.3-34.6a440.45 440.45 0 00139.9-94.3 437.71 437.71 0 0094.3-139.9C940.4 629 952 571.4 952 512c0-19.9 16.1-36 36-36s36 16.1 36 36c0 256.1-207.9 464-464 464S48 768.1 48 512 255.9 48 512 48s464 207.9 464 464c0 19.9-16.1 36-36 36z"></path>
                  </svg>
                </span>
              </div>
              <h3>正在导入中...</h3>
              <p style={{ color: '#666', marginBottom: '24px' }}>
                请耐心等待，正在解析和导入Excel文件数据
              </p>
            </>
          ) : (
            <>
              <UploadOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
              <h3>批量导入功能</h3>
              <p style={{ color: '#666', marginBottom: '24px' }}>
                支持Excel格式文件导入，请按照标准模板格式准备数据
              </p>
              <Space direction="vertical" size="large">
                <Upload
                  accept=".xlsx,.xls"
                  beforeUpload={(file) => {
                    handleBatchImport(file);
                    return false;
                  }}
                  showUploadList={false}
                  disabled={batchImportLoading}
                >
                  <Button icon={<UploadOutlined />} size="large" loading={batchImportLoading}>
                    选择Excel文件
                  </Button>
                </Upload>
                <Button type="link" onClick={handleDownloadTemplate} disabled={batchImportLoading}>
                  下载导入模板
                </Button>
              </Space>
            </>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default InstructionTab; 
