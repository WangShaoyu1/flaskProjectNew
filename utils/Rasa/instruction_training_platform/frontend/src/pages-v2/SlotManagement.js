import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Form, Input, Select, App,
  Popconfirm, Tag, Space, Tooltip, Row, Col, Statistic, 
  Upload, Divider, List, Badge, Switch, Tabs, Collapse, Progress,
  Drawer
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
  UnorderedListOutlined
} from '@ant-design/icons';
import { slotAPI, apiUtils } from '../api-v2';
import { formatLocalTime } from '../utils/timeUtils';
import { safeTableDataSource } from '../utils/dataSourceUtils';

const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { Panel } = Collapse;

const SlotManagement = ({ currentLibrary }) => {
  const { message } = App.useApp();
  const [slots, setSlots] = useState([]);
  const [slotTypes, setSlotTypes] = useState([]);
  const [slotValues, setSlotValues] = useState([]);
  const [relatedInstructions, setRelatedInstructions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [slotValuesLoading, setSlotValuesLoading] = useState(false);
  
  // 模态框状态
  const [slotModalVisible, setSlotModalVisible] = useState(false);
  const [slotValuesModalVisible, setSlotValuesModalVisible] = useState(false);
  const [batchImportModalVisible, setBatchImportModalVisible] = useState(false);
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
      const { slots: slotList, total } = response.data.data;
      
      setSlots(slotList || []);
      setPagination(prev => ({ ...prev, total }));
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
      setEntities(response.data.slot_values || []);
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
      entityForm.resetFields();
      await fetchEntities(currentSlot.id);
      await fetchSlots(); // 刷新词槽列表以更新实体数量
    } catch (error) {
      message.error(apiUtils.handleError(error, '添加实体失败'));
    }
  };

  // 编辑实体
  const handleEditEntity = (entity) => {
    setEditingEntity(entity);
    entityForm.setFieldsValue({
      standard_value: entity.standard_value,
      aliases: entity.aliases,
      description: entity.description,
      is_active: entity.is_active
    });
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

  // 表格列定义
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
      title: '必填',
      dataIndex: 'is_required',
      key: 'is_required',
      width: 80,
      render: (required) => (
        <Badge 
          status={required ? 'warning' : 'default'} 
          text={required ? '必填' : '选填'} 
        />
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
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="管理词槽值">
            <Button
              type="text"
              icon={<UnorderedListOutlined />}
              onClick={() => manageSlotValues(record)}
            />
          </Tooltip>
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

  // 分页处理
  const handleTableChange = (pagination) => {
    setPagination(pagination);
  };

  return (
    <div className="slot-management">
      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="总词槽数"
              value={pagination.total}
              prefix={<TagsOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="启用词槽"
              value={slots.filter(item => item.is_active).length}
              prefix={<TagsOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="必填词槽"
              value={slots.filter(item => item.is_required).length}
              prefix={<TagsOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="词槽值总数"
              value={slots.reduce((sum, slot) => sum + (slot.values_count || 0), 0)}
              prefix={<UnorderedListOutlined style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 搜索和操作栏 */}
      <Card style={{ marginBottom: 24 }}>
        <Form
          layout="inline"
          onFinish={handleSearch}
          style={{ marginBottom: 16 }}
        >
          <Form.Item name="search" label="搜索">
            <Input placeholder="词槽名称" prefix={<SearchOutlined />} autoComplete="off" />
          </Form.Item>
          <Form.Item name="slot_type" label="类型">
            <Select placeholder="选择类型" allowClear style={{ width: 120 }}>
              {slotTypes.map(type => (
                <Option key={type.value} value={type.value}>{type.label}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="is_active" label="状态">
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
      </Card>

      {/* 词槽列表 */}
      <Card title={`词槽列表 - ${currentLibrary.name}`}>
        <Table
          columns={slotColumns}
          dataSource={safeTableDataSource(slots)}
          rowKey="id"
          loading={loading}
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
        <Tabs defaultActiveKey="1">
          <TabPane tab="词槽值列表" key="1">
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
          </TabPane>
          
          <TabPane tab="批量导入" key="2">
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
          </TabPane>
        </Tabs>
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
        onCancel={() => setBatchImportModalVisible(false)}
        footer={null}
        width={600}
      >
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <UploadOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
          <h3>批量导入功能</h3>
          <p style={{ color: '#666', marginBottom: '24px' }}>
            支持Excel格式文件导入，请按照标准模板格式准备数据
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
      </Modal>

      {/* 实体管理抽屉 */}
      <Drawer
        title={`实体管理 - ${currentSlot?.slot_name}`}
        placement="right"
        width={800}
        open={entitiesDrawerVisible}
        onClose={closeEntitiesDrawer}
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => entityForm.submit()}
            >
              添加实体
            </Button>
          </Space>
        }
      >
        {/* 添加实体表单 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Form
            form={entityForm}
            layout="vertical"
            onFinish={editingEntity ? handleSaveEntity : handleAddEntity}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  name="standard_value"
                  label="标准名"
                  rules={[{ required: true, message: '请输入标准名' }]}
                >
                  <Input placeholder="请输入标准名" autoComplete="off" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="aliases"
                  label="别名"
                  extra="多个别名用 == 分隔"
                >
                  <Input placeholder="别名1==别名2==别名3" autoComplete="off" />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={16}>
                <Form.Item name="description" label="描述">
                  <Input placeholder="实体描述" autoComplete="off" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item name="is_active" label="启用状态" valuePropName="checked">
                  <Switch checkedChildren="启用" unCheckedChildren="禁用" defaultChecked />
                </Form.Item>
              </Col>
            </Row>
            {editingEntity && (
              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit">
                    保存修改
                  </Button>
                  <Button onClick={handleCancelEditEntity}>
                    取消编辑
                  </Button>
                </Space>
              </Form.Item>
            )}
          </Form>
        </Card>

        {/* 实体列表 */}
        <Card size="small" title={`实体列表 (${entities.length})`}>
          <List
            loading={entitiesLoading}
            dataSource={safeTableDataSource(entities)}
            renderItem={(entity) => (
              <List.Item
                actions={[
                  <Button
                    key="edit"
                    type="link"
                    size="small"
                    icon={<EditOutlined />}
                    onClick={() => handleEditEntity(entity)}
                  >
                    编辑
                  </Button>,
                  <Popconfirm
                    key="delete"
                    title="确定要删除这个实体吗？"
                    onConfirm={() => handleDeleteEntity(entity.id)}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button
                      type="link"
                      size="small"
                      danger
                      icon={<DeleteOutlined />}
                    >
                      删除
                    </Button>
                  </Popconfirm>
                ]}
              >
                <List.Item.Meta
                  title={
                    <div>
                      <span style={{ fontWeight: 'bold', marginRight: 8 }}>
                        {entity.standard_value}
                      </span>
                      <Badge 
                        status={entity.is_active ? 'success' : 'default'} 
                        text={entity.is_active ? '启用' : '禁用'} 
                      />
                    </div>
                  }
                  description={
                    <div>
                      {entity.aliases && (
                        <div style={{ marginBottom: 4 }}>
                          <span style={{ color: '#666', marginRight: 8 }}>别名:</span>
                          {entity.aliases.split('==').filter(alias => alias.trim()).map((alias, index) => (
                            <Tag key={index} color="geekblue" size="small" style={{ marginRight: 4 }}>
                              {alias.trim()}
                            </Tag>
                          ))}
                        </div>
                      )}
                      {entity.description && (
                        <div style={{ color: '#666', fontSize: '12px' }}>
                          {entity.description}
                        </div>
                      )}
                    </div>
                  }
                />
              </List.Item>
            )}
            locale={{ emptyText: '暂无实体数据' }}
          />
        </Card>
      </Drawer>
    </div>
  );
};

export default SlotManagement; 