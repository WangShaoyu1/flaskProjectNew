import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Form, Input, Select, App,
  Popconfirm, Tag, Space, Tooltip, Row, Col, Statistic, 
  Upload, Divider, List, Badge, Switch, Tabs, Collapse, Progress,
  Drawer, Dropdown
} from 'antd';
import {
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  TagsOutlined,
  UploadOutlined,
  DownloadOutlined,
  EyeOutlined,
  SettingOutlined,
  SearchOutlined,
  ReloadOutlined,
  LinkOutlined,
  UnorderedListOutlined,
  DownOutlined,
  CheckOutlined,
  CloseOutlined,
  SwapOutlined,
  UserOutlined
} from '@ant-design/icons';
import { slotAPI, apiUtils } from '../api-v2';
import { formatLocalTime } from '../utils/timeUtils';
import { safeTableDataSource } from '../utils/dataSourceUtils';

const { Option } = Select;
const { TextArea } = Input;
const { Panel } = Collapse;

const SlotTab = ({ currentLibrary }) => {
  const { message } = App.useApp();
  const [slots, setSlots] = useState([]);
  const [slotTypes, setSlotTypes] = useState([]);
  const [slotValues, setSlotValues] = useState([]);
  const [relatedInstructions, setRelatedInstructions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [slotValuesLoading, setSlotValuesLoading] = useState(false);
  
  // 批量操作相关状态
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [batchDeleteLoading, setBatchDeleteLoading] = useState(false);
  
  // 模态框状态
  const [slotModalVisible, setSlotModalVisible] = useState(false);
  const [slotValuesModalVisible, setSlotValuesModalVisible] = useState(false);
  const [batchImportModalVisible, setBatchImportModalVisible] = useState(false);
  const [batchImportLoading, setBatchImportLoading] = useState(false);
  const [relatedInstructionsModalVisible, setRelatedInstructionsModalVisible] = useState(false);
  
  // 实体抽屉状态
  const [entitiesDrawerVisible, setEntitiesDrawerVisible] = useState(false);
  const [entitiesLoading, setEntitiesLoading] = useState(false);
  const [entities, setEntities] = useState([]);
  const [editingEntity, setEditingEntity] = useState(null);
  
  const [editingSlot, setEditingSlot] = useState(null);
  const [currentSlot, setCurrentSlot] = useState(null);
  const [searchParams, setSearchParams] = useState({});
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  
  const [slotForm] = Form.useForm();
  const [slotValueForm] = Form.useForm();
  const [entityForm] = Form.useForm();

  // 下载模板
  const handleDownloadTemplate = async () => {
    try {
      const response = await slotAPI.downloadTemplate();
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = '词槽导入模板.xlsx';
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

      const response = await slotAPI.batchImport(formData);
      
      // 适配新的标准响应格式
      const responseData = response.data.data || response.data;
      const slotsSuccessCount = responseData.slots_success_count || responseData.success_count || 0;
      const valuesSuccessCount = responseData.total_values_count || responseData.values_success_count || 0;
      
      if (valuesSuccessCount > 0) {
        message.success(`批量导入成功！词槽 ${slotsSuccessCount} 个，词槽值 ${valuesSuccessCount} 条`);
      } else {
        message.success(`批量导入成功！共导入 ${slotsSuccessCount} 个词槽`);
      }
      setBatchImportModalVisible(false);
      fetchSlots();
    } catch (error) {
      message.error(apiUtils.handleError(error, '批量导入失败'));
    } finally {
      setBatchImportLoading(false);
    }
  };

  // 检查是否选择了指令库
  if (!currentLibrary) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <TagsOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
          <h3>请先选择指令库</h3>
          <p style={{ color: '#666' }}>在开始管理词槽之前，请先在指令库管理页面选择一个指令库。</p>
        </div>
      </Card>
    );
  }

  // 获取词槽类型
  const fetchSlotTypes = async () => {
    try {
      const response = await slotAPI.getSlotTypes();
      setSlotTypes(response.data.slot_types || []);
    } catch (error) {
      console.error('获取词槽类型失败:', error);
    }
  };

  // 获取词槽列表
  const fetchSlots = async (params = {}) => {
    setLoading(true);
    try {
      const queryParams = {
        library_id: currentLibrary.id,
        page: pagination.current,
        size: pagination.pageSize,
        ...searchParams,
        ...params
      };
      
      const response = await slotAPI.getSlots(apiUtils.buildParams(queryParams));
      const responseData = response.data?.data || {};
      const { slots: slotList, total } = responseData;
      
      setSlots(slotList || []);
      setPagination(prev => ({ ...prev, total: total || 0 }));
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取词槽列表失败'));
    } finally {
      setLoading(false);
    }
  };

  // 获取词槽值列表
  const fetchSlotValues = async (slotId) => {
    setSlotValuesLoading(true);
    try {
      const response = await slotAPI.getSlotValues(slotId);
      setSlotValues(response.data.slot_values || []);
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取词槽值失败'));
    } finally {
      setSlotValuesLoading(false);
    }
  };

  // 获取关联指令
  const fetchRelatedInstructions = async (slotId) => {
    try {
      const response = await slotAPI.getRelatedInstructions(slotId);
      setRelatedInstructions(response.data.instructions || []);
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取关联指令失败'));
    }
  };

  useEffect(() => {
    if (currentLibrary) {
      fetchSlots();
      fetchSlotTypes();
    }
  }, [currentLibrary, pagination.current, pagination.pageSize]);

  // 搜索处理
  const handleSearch = (values) => {
    setSearchParams(values);
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchSlots({ ...values, page: 1 });
  };

  // 重置搜索
  const handleResetSearch = () => {
    setSearchParams({});
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchSlots({ page: 1 });
  };

  // 打开词槽创建/编辑模态框
  const openSlotModal = (slot = null) => {
    setEditingSlot(slot);
    setSlotModalVisible(true);
    
    if (slot) {
      slotForm.setFieldsValue(slot);
    } else {
      slotForm.resetFields();
    }
  };

  // 关闭词槽模态框
  const closeSlotModal = () => {
    setSlotModalVisible(false);
    setEditingSlot(null);
    slotForm.resetFields();
  };

  // 保存词槽
  const handleSaveSlot = async (values) => {
    try {
      const data = {
        ...values,
        library_id: currentLibrary.id
      };
      
      if (editingSlot) {
        await slotAPI.updateSlot(editingSlot.id, data);
        message.success('词槽更新成功');
      } else {
        await slotAPI.createSlot(data);
        message.success('词槽创建成功');
      }
      
      closeSlotModal();
      fetchSlots();
    } catch (error) {
      message.error(apiUtils.handleError(error, '保存词槽失败'));
    }
  };

  // 删除词槽
  const handleDeleteSlot = async (slotId) => {
    try {
      await slotAPI.deleteSlot(slotId);
      message.success('词槽删除成功');
      fetchSlots();
    } catch (error) {
      message.error(apiUtils.handleError(error, '删除词槽失败'));
    }
  };

  // 管理词槽值
  const manageSlotValues = async (slot) => {
    setCurrentSlot(slot);
    await fetchSlotValues(slot.id);
    setSlotValuesModalVisible(true);
  };

  // 添加词槽值
  const handleAddSlotValue = async (values) => {
    try {
      await slotAPI.addSlotValue(currentSlot.id, values);
      message.success('词槽值添加成功');
      slotValueForm.resetFields();
      await fetchSlotValues(currentSlot.id);
    } catch (error) {
      message.error(apiUtils.handleError(error, '添加词槽值失败'));
    }
  };

  // 删除词槽值
  const handleDeleteSlotValue = async (valueId) => {
    try {
      await slotAPI.deleteSlotValue(currentSlot.id, valueId);
      message.success('词槽值删除成功');
      await fetchSlotValues(currentSlot.id);
    } catch (error) {
      message.error(apiUtils.handleError(error, '删除词槽值失败'));
    }
  };

  // 查看关联指令
  const viewRelatedInstructions = async (slot) => {
    setCurrentSlot(slot);
    await fetchRelatedInstructions(slot.id);
    setRelatedInstructionsModalVisible(true);
  };

  // 打开实体抽屉
  const openEntitiesDrawer = async (slot) => {
    setCurrentSlot(slot);
    setEntitiesDrawerVisible(true);
    await fetchEntities(slot.id);
  };

  // 关闭实体抽屉
  const closeEntitiesDrawer = () => {
    setEntitiesDrawerVisible(false);
    setCurrentSlot(null);
    setEntities([]);
    setEditingEntity(null);
    entityForm.resetFields();
  };

  // 获取实体列表
  const fetchEntities = async (slotId) => {
    setEntitiesLoading(true);
    try {
      const response = await slotAPI.getSlotValues(slotId);
      
      // 根据后端API测试结果，数据路径是 response.data.data.slot_values
      const entitiesData = response.data?.data?.slot_values || [];
      
      setEntities(entitiesData);
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取实体列表失败'));
    } finally {
      setEntitiesLoading(false);
    }
  };

  // 添加实体
  const handleAddEntity = async (values) => {
    try {
      await slotAPI.addSlotValue(currentSlot.id, values);
      message.success('实体添加成功');
      setEditingEntity(null);
      entityForm.resetFields();
      await fetchEntities(currentSlot.id);
      await fetchSlots(); // 刷新词槽列表以更新实体数量
    } catch (error) {
      message.error(apiUtils.handleError(error, '添加实体失败'));
    }
  };

  // 编辑实体
  const handleEditEntity = (entity) => {
    // 立即设置编辑状态，提高响应速度
    setEditingEntity({ ...entity, isNew: false });
    
    // 使用 nextTick 确保模态框完全渲染后再设置表单值
    setTimeout(() => {
      entityForm.setFieldsValue({
        standard_value: entity.standard_value,
        aliases: entity.aliases || '',
        description: entity.description || ''
      });
    }, 100);
  };

  // 保存实体编辑
  const handleSaveEntity = async (values) => {
    try {
      await slotAPI.updateSlotValue(currentSlot.id, editingEntity.id, values);
      message.success('实体更新成功');
      setEditingEntity(null);
      entityForm.resetFields();
      await fetchEntities(currentSlot.id);
      await fetchSlots(); // 刷新词槽列表
    } catch (error) {
      message.error(apiUtils.handleError(error, '更新实体失败'));
    }
  };

  // 取消编辑实体
  const handleCancelEditEntity = () => {
    setEditingEntity(null);
    entityForm.resetFields();
  };

  // 删除实体
  const handleDeleteEntity = async (entityId) => {
    try {
      await slotAPI.deleteSlotValue(currentSlot.id, entityId);
      message.success('实体删除成功');
      await fetchEntities(currentSlot.id);
      await fetchSlots(); // 刷新词槽列表以更新实体数量
    } catch (error) {
      message.error(apiUtils.handleError(error, '删除实体失败'));
    }
  };

  // 更新实体别名
  const handleUpdateEntityAliases = async (entityId, aliases) => {
    try {
      const entity = entities.find(e => e.id === entityId);
      if (!entity) return;

      await slotAPI.updateSlotValue(currentSlot.id, entityId, {
        ...entity,
        aliases: aliases
      });
      message.success('别名更新成功');
      await fetchEntities(currentSlot.id);
    } catch (error) {
      message.error(apiUtils.handleError(error, '更新别名失败'));
    }
  };

  // 切换词槽状态
  const handleToggleSlotStatus = async (slot, checked) => {
    try {
      await slotAPI.updateSlot(slot.id, {
        ...slot,
        is_active: checked
      });
      message.success('词槽状态更新成功');
      await fetchSlots(); // 刷新词槽列表
    } catch (error) {
      message.error(apiUtils.handleError(error, '更新词槽状态失败'));
    }
  };

  // 切换实体状态
  const handleToggleEntityStatus = async (entity, checked) => {
    try {
      await slotAPI.updateSlotValue(currentSlot.id, entity.id, {
        ...entity,
        is_active: checked
      });
      message.success('实体状态更新成功');
      await fetchEntities(currentSlot.id);
      await fetchSlots(); // 刷新词槽列表
    } catch (error) {
      message.error(apiUtils.handleError(error, '更新实体状态失败'));
    }
  };

  // 批量操作函数
  const handleSelectChange = (newSelectedRowKeys) => {
    setSelectedRowKeys(newSelectedRowKeys);
  };

  const handleSelectAll = () => {
    const allKeys = slots.map(slot => slot.id);
    setSelectedRowKeys(allKeys);
  };

  const handleSelectNone = () => {
    setSelectedRowKeys([]);
  };

  const handleSelectInvert = () => {
    const allKeys = slots.map(slot => slot.id);
    const newSelectedKeys = allKeys.filter(key => !selectedRowKeys.includes(key));
    setSelectedRowKeys(newSelectedKeys);
  };

  const handleBatchDelete = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请先选择要删除的词槽');
      return;
    }

    setBatchDeleteLoading(true);
    try {
      // 并行删除所有选中的词槽
      const deletePromises = selectedRowKeys.map(slotId => 
        slotAPI.deleteSlot(slotId)
      );
      
      await Promise.all(deletePromises);
      
      message.success(`成功删除 ${selectedRowKeys.length} 个词槽`);
      setSelectedRowKeys([]);
      fetchSlots();
    } catch (error) {
      message.error(apiUtils.handleError(error, '批量删除失败'));
    } finally {
      setBatchDeleteLoading(false);
    }
  };

  // 初始化系统词槽
  const handleInitSystemSlots = async () => {
    try {
      const response = await slotAPI.initSystemSlots(currentLibrary.id);
      
      if (response.data.code === '000000') {
        const { created_count, updated_count } = response.data.data;
        message.success(`系统词槽初始化完成：新增 ${created_count} 个，更新 ${updated_count} 个`);
        fetchSlots(); // 刷新词槽列表
      } else {
        message.error(response.data.msg || '初始化系统词槽失败');
      }
    } catch (error) {
      console.error('初始化系统词槽失败:', error);
      message.error('初始化系统词槽失败');
    }
  };

  // 词槽表格列定义
  const slotColumns = [
    {
      title: '词槽名称',
      dataIndex: 'slot_name',
      key: 'slot_name',
      width: 150,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{text}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            英文名: {record.slot_name_en}
          </div>
        </div>
      ),
    },
    {
      title: '词槽类型',
      dataIndex: 'slot_type',
      key: 'slot_type',
      width: 120,
      render: (type) => {
        const typeConfig = {
          'categorical': { color: 'blue', text: '分类型' },
          'text': { color: 'green', text: '文本型' },
          'float': { color: 'orange', text: '数值型' },
          'bool': { color: 'purple', text: '布尔型' },
          'list': { color: 'cyan', text: '列表型' }
        };
        const config = typeConfig[type] || { color: 'default', text: type };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '词槽分类',
      dataIndex: 'is_system',
      key: 'is_system',
      width: 110,
      render: (isSystem) => (
        <Tag color={isSystem ? 'blue' : 'green'} style={{ fontWeight: 'bold' }}>
          {isSystem ? '系统词槽' : '自定义词槽'}
        </Tag>
      ),
    },
    {
      title: '必填',
      dataIndex: 'is_required',
      key: 'is_required',
      width: 80,
      render: (required) => (
        <Badge 
          status={required ? 'warning' : 'default'} 
          text={required ? '是' : '否'} 
        />
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active, record) => (
        <Switch
          checked={active}
          onChange={(checked) => handleToggleSlotStatus(record, checked)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      ),
    },
    {
      title: '实体',
      key: 'values_count',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          style={{ padding: 0, color: '#1890ff' }}
          onClick={() => openEntitiesDrawer(record)}
        >
          {record.values_count || 0} 个
        </Button>
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
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="关联指令">
            <Button
              type="text"
              icon={<LinkOutlined />}
              onClick={() => viewRelatedInstructions(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => openSlotModal(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个词槽吗？"
            description="删除后将无法恢复，同时会影响关联的指令。"
            onConfirm={() => handleDeleteSlot(record.id)}
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

  // 词槽值表格列定义
  const slotValueColumns = [
    {
      title: '标准值',
      dataIndex: 'standard_value',
      key: 'standard_value',
      width: 150,
      render: (text) => <span style={{ fontWeight: 'bold' }}>{text}</span>,
    },
    {
      title: '别名',
      dataIndex: 'aliases',
      key: 'aliases',
      render: (aliases) => {
        if (!aliases) return '-';
        const aliasArray = aliases.split('==').filter(alias => alias.trim());
        return (
          <div>
            {aliasArray.map((alias, index) => (
              <Tag key={index} color="geekblue" style={{ marginBottom: 4 }}>
                {alias.trim()}
              </Tag>
            ))}
          </div>
        );
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 150,
      ellipsis: { showTitle: false },
      render: (desc) => (
        <Tooltip title={desc}>
          {desc || '-'}
        </Tooltip>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active) => (
        <Badge 
          status={active ? 'success' : 'default'} 
          text={active ? '启用' : '禁用'} 
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              size="small"
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个词槽值吗？"
            onConfirm={() => handleDeleteSlotValue(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                size="small"
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 实体表格列定义
  const entityColumns = [
    {
      title: '标准名',
      dataIndex: 'standard_value',
      key: 'standard_value',
      width: 150,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{text}</div>
          {record.description && (
            <div style={{ fontSize: '12px', color: '#666', marginTop: 2 }}>
              {record.description}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '别名',
      dataIndex: 'aliases',
      key: 'aliases',
      render: (aliases) => {
        if (!aliases) return <span style={{ color: '#ccc' }}>无</span>;
        
        const aliasList = aliases.split('==').filter(alias => alias.trim());
        if (aliasList.length === 0) return <span style={{ color: '#ccc' }}>无</span>;
        
        return (
          <div>
            {aliasList.map((alias, index) => (
              <Tag key={index} style={{ marginBottom: 2 }}>
                {alias.trim()}
              </Tag>
            ))}
          </div>
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active, record) => (
        <Switch
          checked={active}
          size="small"
          onChange={(checked) => handleToggleEntityStatus(record, checked)}
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditEntity(record)}
            size="small"
          />
          <Popconfirm
            title="确定要删除这个实体吗？"
            onConfirm={() => handleDeleteEntity(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              size="small"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 分页处理
  const handleTableChange = (pagination) => {
    setPagination(pagination);
  };

  // 检查是否选择了指令库
  if (!currentLibrary) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <TagsOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
          <h3>请先选择指令库</h3>
          <p style={{ color: '#666' }}>在开始词槽管理之前，请先选择一个指令库。</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="slot-tab">
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
          <span style={{ fontSize: '14px', color: '#666', fontWeight: '500' }}>🏷️ 词槽统计</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <TagsOutlined style={{ color: '#1890ff', fontSize: '14px' }} />
            <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#1890ff' }}>
              {pagination.total}
            </span>
            <span style={{ fontSize: '12px', color: '#999' }}>总词槽</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <UserOutlined style={{ color: '#52c41a', fontSize: '14px' }} />
            <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#52c41a' }}>
              {slots.filter(item => !item.is_system).length}
            </span>
            <span style={{ fontSize: '12px', color: '#999' }}>自定义</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <SettingOutlined style={{ color: '#fa8c16', fontSize: '14px' }} />
            <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#fa8c16' }}>
              {slots.filter(item => item.is_system).length}
            </span>
            <span style={{ fontSize: '12px', color: '#999' }}>系统</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <UnorderedListOutlined style={{ color: '#722ed1', fontSize: '14px' }} />
            <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#722ed1' }}>
              {slots.reduce((sum, slot) => sum + (slot.values_count || 0), 0)}
            </span>
            <span style={{ fontSize: '12px', color: '#999' }}>词槽值</span>
          </div>
        </div>
        
        <div style={{ fontSize: '12px', color: '#999' }}>
          ⏰ 最后更新: {formatLocalTime(new Date())}
        </div>
      </div>

      {/* 搜索和操作栏 */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          {/* 左侧：搜索栏 */}
          <div style={{ flex: 1, marginRight: 24 }}>
            <Form
              layout="inline"
              onFinish={handleSearch}
              style={{ width: '100%' }}
            >
              <Form.Item name="search" label="搜索" style={{ marginBottom: 8 }}>
                <Input placeholder="词槽名称" prefix={<SearchOutlined />} autoComplete="off" style={{ width: 200 }} />
              </Form.Item>
              <Form.Item name="slot_type" label="类型" style={{ marginBottom: 8 }}>
                <Select placeholder="选择类型" allowClear style={{ width: 120 }}>
                  {slotTypes.map(type => (
                    <Option key={type.value} value={type.value}>{type.label}</Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="is_active" label="状态" style={{ marginBottom: 8 }}>
                <Select placeholder="状态" allowClear style={{ width: 100 }}>
                  <Option value={true}>启用</Option>
                  <Option value={false}>禁用</Option>
                </Select>
              </Form.Item>
              <Form.Item name="is_system" label="分类" style={{ marginBottom: 8 }}>
                <Select placeholder="分类" allowClear style={{ width: 120 }}>
                  <Option value={false}>自定义词槽</Option>
                  <Option value={true}>系统词槽</Option>
                </Select>
              </Form.Item>
              <Form.Item style={{ marginBottom: 8 }}>
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
          </div>
          
          {/* 右侧：操作按钮区域 */}
          <div style={{ flexShrink: 0 }}>
            {/* 第一排：主要操作按钮 */}
            <div style={{ marginBottom: 12 }}>
              <Space wrap>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => openSlotModal()}
                >
                  新增词槽
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
              </Space>
            </div>
            
            {/* 第二排：系统和批量操作 */}
            <div>
              <Space wrap>
                <Button
                  icon={<SettingOutlined />}
                  onClick={handleInitSystemSlots}
                  type="dashed"
                >
                  初始化系统词槽
                </Button>
                <Dropdown
                  menu={{
                    items: [
                      {
                        key: 'selectAll',
                        label: '全选',
                        icon: <CheckOutlined />,
                        disabled: slots.length === 0,
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
                        disabled: slots.length === 0,
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
                            title: '确定要删除选中的词槽吗？',
                            content: `将删除 ${selectedRowKeys.length} 个词槽，此操作不可恢复。`,
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
        </div>
      </Card>

      {/* 词槽列表 */}
      <Card title={`词槽列表 - ${currentLibrary?.name || '未选择指令库'}`}>
        <Table
          columns={slotColumns}
          dataSource={safeTableDataSource(slots)}
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
            showTotal: (total) => `共 ${total} 个词槽`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 词槽创建/编辑模态框 */}
      <Modal
        title={editingSlot ? '编辑词槽' : '新增词槽'}
        open={slotModalVisible}
        onCancel={closeSlotModal}
        footer={null}
        width={600}
      >
        <Form
          form={slotForm}
          layout="vertical"
          onFinish={handleSaveSlot}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="slot_name"
                label="词槽名称"
                rules={[{ required: true, message: '请输入词槽名称' }]}
              >
                <Input placeholder="请输入词槽名称" autoComplete="off" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="slot_name_en"
                label="英文名称"
                rules={[
                  { required: true, message: '请输入英文名称' },
                  { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: '只能包含字母、数字和下划线，且以字母或下划线开头' }
                ]}
              >
                <Input placeholder="请输入英文名称" autoComplete="off" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="slot_type"
                label="词槽类型"
                rules={[{ required: true, message: '请选择词槽类型' }]}
              >
                <Select placeholder="选择词槽类型">
                  {slotTypes.map(type => (
                    <Option key={type.value} value={type.value}>{type.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_required" label="是否必填" valuePropName="checked">
                <Switch checkedChildren="必填" unCheckedChildren="选填" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="词槽描述">
            <TextArea rows={3} placeholder="请输入词槽描述" />
          </Form.Item>

          <Form.Item name="is_active" label="启用状态" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" defaultChecked />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={closeSlotModal}>取消</Button>
              <Button type="primary" htmlType="submit">
                {editingSlot ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 词槽值管理模态框 */}
      <Modal
        title={`词槽值管理 - ${currentSlot?.slot_name}`}
        open={slotValuesModalVisible}
        onCancel={() => setSlotValuesModalVisible(false)}
        footer={null}
        width={900}
      >
        <Tabs 
          defaultActiveKey="1"
          items={[
            {
              key: '1',
              label: '词槽值列表',
              children: (
                <div>
                  <Form
                    form={slotValueForm}
                    layout="vertical"
                    onFinish={handleAddSlotValue}
                    style={{ marginBottom: 16, padding: 16, background: '#fafafa', borderRadius: 6 }}
                  >
                    <Row gutter={16}>
                      <Col span={8}>
                        <Form.Item
                          name="standard_value"
                          label="标准值"
                          rules={[{ required: true, message: '请输入标准值' }]}
                        >
                          <Input placeholder="请输入标准值" autoComplete="off" />
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item
                          name="aliases"
                          label="别名"
                          extra="多个别名用 == 分隔"
                        >
                          <Input placeholder="别名1==别名2==别名3" autoComplete="off" />
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item name="description" label="描述">
                          <Input placeholder="词槽值描述" autoComplete="off" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Form.Item>
                      <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>
                        添加词槽值
                      </Button>
                    </Form.Item>
                  </Form>

                  <Table
                    columns={slotValueColumns}
                    dataSource={safeTableDataSource(slotValues)}
                    rowKey="id"
                    loading={slotValuesLoading}
                    pagination={{ pageSize: 10 }}
                    locale={{ emptyText: '暂无词槽值' }}
                  />
                </div>
              )
            },
            {
              key: '2',
              label: '批量导入',
              children: (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <UploadOutlined style={{ fontSize: '48px', color: '#ccc', marginBottom: '16px' }} />
                  <h3>批量导入词槽值</h3>
                  <p style={{ color: '#666', marginBottom: '24px' }}>
                    支持Excel格式文件导入词槽值
                  </p>
                  <Space direction="vertical" size="large">
                    <Upload
                      accept=".xlsx,.xls"
                      beforeUpload={() => false}
                    >
                      <Button icon={<UploadOutlined />} size="large">
                        选择Excel文件
                      </Button>
                    </Upload>
                    <Button type="link">
                      下载导入模板
                    </Button>
                  </Space>
                </div>
              )
            }
          ]}
        />
      </Modal>

      {/* 关联指令模态框 */}
      <Modal
        title={`关联指令 - ${currentSlot?.slot_name}`}
        open={relatedInstructionsModalVisible}
        onCancel={() => setRelatedInstructionsModalVisible(false)}
        footer={null}
        width={700}
      >
        {relatedInstructions.length > 0 ? (
          <List
            dataSource={safeTableDataSource(relatedInstructions)}
            renderItem={(item) => (
              <List.Item>
                <List.Item.Meta
                  title={item.instruction_name}
                  description={
                    <div>
                      <div>编码: {item.instruction_code}</div>
                      <div>分类: {item.category || '未分类'}</div>
                    </div>
                  }
                />
                <Badge status={item.is_enabled ? 'success' : 'default'} />
              </List.Item>
            )}
          />
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
            <LinkOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
            <div>暂无关联指令</div>
          </div>
        )}
      </Modal>

      {/* 批量导入模态框 */}
      <Modal
        title="批量导入词槽"
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

      {/* 实体管理抽屉 */}
      <Drawer
        title="词槽信息"
        placement="right"
        width={600}
        onClose={closeEntitiesDrawer}
        open={entitiesDrawerVisible}
        styles={{
          body: { padding: 24 }
        }}
      >
        {currentSlot && (
          <div>
            {/* 词槽基本信息 */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: 8 }}>
                词槽名称：
              </div>
              <div style={{ fontSize: '18px', color: '#1890ff', marginBottom: 16 }}>
                {currentSlot.slot_name}
              </div>
              
              <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: 8 }}>
                命名实体：
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <span style={{ color: '#666' }}>管理词槽的实体值和别名</span>
                <Button 
                  type="primary" 
                  size="small"
                  icon={<PlusOutlined />}
                  onClick={() => {
                    setEditingEntity({ isNew: true });
                    // 重置表单，确保新增时是空白状态
                    setTimeout(() => {
                      entityForm.resetFields();
                    }, 100);
                  }}
                >
                  新增实体
                </Button>
              </div>
            </div>

            {/* 实体列表 */}
            <div style={{ marginBottom: 24 }}>
              {entities.length > 0 ? (
                <div>
                  {/* 表头 */}
                  <div style={{ 
                    display: 'grid', 
                    gridTemplateColumns: '80px 120px 1fr 60px', 
                    gap: '12px',
                    padding: '12px 0',
                    borderBottom: '1px solid #f0f0f0',
                    fontWeight: 'bold',
                    backgroundColor: '#fafafa',
                    marginBottom: 8
                  }}>
                    <div>ID</div>
                    <div>标准名</div>
                    <div>别名</div>
                    <div>操作</div>
                  </div>
                  
                  {/* 实体列表 */}
                  <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                    {entities.map((entity, index) => (
                      <div key={entity.id} style={{ 
                        display: 'grid', 
                        gridTemplateColumns: '80px 120px 1fr 60px', 
                        gap: '12px',
                        padding: '12px 0',
                        borderBottom: '1px solid #f0f0f0',
                        alignItems: 'center'
                      }}>
                        <div style={{ color: '#666' }}>{entity.id}</div>
                        <div style={{ fontWeight: 'bold' }}>{entity.standard_value}</div>
                        <div style={{ fontSize: '14px', color: '#666' }}>
                          {entity.aliases ? (
                            entity.aliases.split('==').filter(alias => alias.trim()).map((alias, i) => (
                              <Tag key={i} size="small" style={{ marginRight: 4, marginBottom: 2 }}>
                                {alias.trim()}
                              </Tag>
                            ))
                          ) : (
                            <span style={{ color: '#ccc' }}>无别名</span>
                          )}
                        </div>
                        <div style={{ display: 'flex', gap: '4px' }}>
                          <Button
                            type="text"
                            icon={<EditOutlined />}
                            size="small"
                            onClick={() => handleEditEntity(entity)}
                            title="编辑"
                          />
                          <Popconfirm
                            title="确定要删除这个实体吗？"
                            onConfirm={() => handleDeleteEntity(entity.id)}
                            okText="确定"
                            cancelText="取消"
                          >
                            <Button
                              type="text"
                              danger
                              icon={<DeleteOutlined />}
                              size="small"
                              title="删除"
                            />
                          </Popconfirm>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {/* 分页信息 */}
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginTop: 16,
                    padding: '12px 0',
                    borderTop: '1px solid #f0f0f0'
                  }}>
                    <div style={{ color: '#666' }}>共 {entities.length} 条</div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <Button 
                        size="small" 
                        icon={<ReloadOutlined />}
                        onClick={() => fetchEntities(currentSlot.id)}
                      >
                        刷新
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '40px',
                  color: '#666',
                  backgroundColor: '#fafafa',
                  borderRadius: '6px'
                }}>
                  <TagsOutlined style={{ fontSize: '32px', marginBottom: '12px' }} />
                  <div>暂无实体数据</div>
                  <div style={{ fontSize: '12px', marginTop: '8px' }}>
                    <Button 
                      type="link" 
                      onClick={() => {
                        setEditingEntity({ isNew: true });
                        // 重置表单，确保新增时是空白状态
                        setTimeout(() => {
                          entityForm.resetFields();
                        }, 100);
                      }}
                    >
                      点击添加第一个实体
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </Drawer>

      {/* 实体编辑/新增模态框 */}
      <Modal
        title={editingEntity?.isNew ? '新增实体' : '编辑实体'}
        open={!!editingEntity}
        onCancel={() => {
          setEditingEntity(null);
          entityForm.resetFields();
        }}
        footer={null}
        width={500}
        destroyOnHidden={false}
        maskClosable={false}
        forceRender={true}
        zIndex={2000}
        getContainer={() => document.body}
      >
        <Form
          form={entityForm}
          layout="vertical"
          onFinish={editingEntity?.isNew ? handleAddEntity : handleSaveEntity}
          preserve={true}
        >
          <Form.Item
            label="标准名"
            name="standard_value"
            rules={[
              { required: true, message: '请输入标准名' },
              { max: 200, message: '标准名不能超过200个字符' }
            ]}
          >
            <Input placeholder="请输入实体的标准名称" />
          </Form.Item>

          <Form.Item
            label="别名"
            name="aliases"
            extra="多个别名请用 == 分隔，例如：灯光==电灯==照明灯"
          >
            <Input.TextArea 
              placeholder="请输入别名，用==分隔" 
              rows={3}
              showCount
              maxLength={500}
            />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
          >
            <Input placeholder="请输入实体描述（可选）" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => {
                setEditingEntity(null);
                entityForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit" loading={entitiesLoading}>
                {editingEntity?.isNew ? '添加' : '保存'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SlotTab; 