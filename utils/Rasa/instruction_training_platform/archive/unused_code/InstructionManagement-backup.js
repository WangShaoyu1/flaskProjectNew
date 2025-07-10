import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Form, Input, Select, App,
  Popconfirm, Tag, Space, Tooltip, Row, Col, Statistic, 
  Upload, Divider, List, Badge, Switch, Tabs, Collapse
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
  ReloadOutlined
} from '@ant-design/icons';
import { instructionAPI, apiUtils } from '../api-v2';

const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;
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
        page: pagination.current,
        size: pagination.pageSize,
        ...searchParams,
        ...params
      };
      
      const response = await instructionAPI.getInstructions(apiUtils.buildParams(queryParams));
      const { instructions: instructionList, total } = response.data;
      
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
      setCategories(response.data.categories || []);
    } catch (error) {
      console.error('获取分类失败:', error);
    }
  };

  useEffect(() => {
    if (currentLibrary) {
      fetchInstructions();
      fetchCategories();
    }
  }, [currentLibrary, pagination.current, pagination.pageSize]);

  // 搜索处理
  const handleSearch = (values) => {
    setSearchParams(values);
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchInstructions({ ...values, page: 1 });
  };

  // 重置搜索
  const handleResetSearch = () => {
    setSearchParams({});
    setPagination(prev => ({ ...prev, current: 1 }));
    fetchInstructions({ page: 1 });
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
      render: (time) => time ? new Date(time).toLocaleString() : '-',
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

  return (
    <div className="instruction-management">
      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="总指令数"
              value={pagination.total}
              prefix={<MessageOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="启用指令"
              value={instructions.filter(item => item.is_enabled).length}
              prefix={<MessageOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="词槽关联"
              value={instructions.filter(item => item.is_slot_related).length}
              prefix={<TagsOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="分类数量"
              value={categories.length}
              prefix={<TagsOutlined style={{ color: '#722ed1' }} />}
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
        </Space>
      </Card>

      {/* 指令列表 */}
      <Card title={`指令列表 - ${currentLibrary.name}`}>
        <Table
          columns={columns}
          dataSource={instructions}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
        />
      </Card>

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
            >
              {/* 这里应该从词槽API获取数据 */}
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

      {/* 相似问管理模态框 */}
      <Modal
        title={`相似问管理 - ${currentInstruction?.instruction_name}`}
        open={similarQuestionsModalVisible}
        onCancel={() => setSimilarQuestionsModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form
          form={similarQuestionForm}
          layout="inline"
          onFinish={handleAddSimilarQuestion}
          style={{ marginBottom: 16 }}
        >
          <Form.Item
            name="question_text"
            rules={[{ required: true, message: '请输入相似问' }]}
            style={{ flex: 1 }}
          >
            <Input placeholder="请输入相似问" autoComplete="off" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>
              添加
            </Button>
          </Form.Item>
        </Form>

        <List
          dataSource={similarQuestions}
          renderItem={(item, index) => (
            <List.Item
              actions={[
                <Popconfirm
                  title="确定要删除这个相似问吗？"
                  onConfirm={() => handleDeleteSimilarQuestion(item.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button type="text" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              ]}
            >
              <List.Item.Meta
                title={`相似问 ${index + 1}`}
                description={item.question_text}
              />
              <Badge status={item.is_enabled ? 'success' : 'default'} />
            </List.Item>
          )}
          locale={{ emptyText: '暂无相似问' }}
        />
      </Modal>

      {/* 批量导入模态框 */}
      <Modal
        title="批量导入指令"
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
              onChange={(info) => {
                // 处理文件上传
                console.log('文件上传:', info);
              }}
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
    </div>
  );
};

export default InstructionManagement; 