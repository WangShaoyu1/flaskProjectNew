import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Form, Input, Select, App,
  Popconfirm, Tag, Space, Tooltip, Row, Col, Statistic 
} from 'antd';
import {
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  DatabaseOutlined,
  MessageOutlined,
  TagsOutlined,
  BranchesOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { libraryAPI, apiUtils } from '../api-v2';
import { formatLocalTime } from '../utils/timeUtils';
import { safeTableDataSource } from '../utils/dataSourceUtils';

const { Option } = Select;

const LibraryManagement = ({ onLibrarySelect, navigate }) => {
  const { message } = App.useApp();
  const [libraries, setLibraries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingLibrary, setEditingLibrary] = useState(null);
  const [form] = Form.useForm();

  // 语言选项
  const languageOptions = [
    { value: 'zh-CN', label: '中文（简体）' },
    { value: 'zh-TW', label: '中文（繁体）' },
    { value: 'en-US', label: '英语（美国）' },
    { value: 'en-GB', label: '英语（英国）' },
    { value: 'ja-JP', label: '日语' },
    { value: 'ko-KR', label: '韩语' },
    { value: 'fr-FR', label: '法语' },
    { value: 'de-DE', label: '德语' },
    { value: 'es-ES', label: '西班牙语' },
  ];

  // 获取指令库列表
  const fetchLibraries = async () => {
    setLoading(true);
    try {
      const response = await libraryAPI.getLibraries();
      console.log('API响应:', response);
      
      // 确保libraries始终是数组
      let librariesData = [];
      if (response.data) {
        // 如果response.data是数组，直接使用
        if (Array.isArray(response.data)) {
          librariesData = response.data;
        }
        // 如果response.data是对象且包含libraries字段
        else if (response.data.libraries && Array.isArray(response.data.libraries)) {
          librariesData = response.data.libraries;
        }
        // 如果response.data是对象且包含data字段
        else if (response.data.data && Array.isArray(response.data.data)) {
          librariesData = response.data.data;
        }
        // 其他情况，设为空数组
        else {
          console.warn('API返回的数据格式不是预期的数组:', response.data);
          librariesData = [];
        }
      }
      
      setLibraries(librariesData);
    } catch (error) {
      console.error('获取指令库列表失败:', error);
      message.error(apiUtils.handleError(error, '获取指令库列表失败'));
      setLibraries([]); // 确保出错时也设置为空数组
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLibraries();
  }, []);

  // 打开创建/编辑模态框
  const openModal = (library = null) => {
    setEditingLibrary(library);
    setModalVisible(true);
    
    if (library) {
      form.setFieldsValue(library);
    } else {
      form.resetFields();
    }
  };

  // 关闭模态框
  const closeModal = () => {
    setModalVisible(false);
    setEditingLibrary(null);
    form.resetFields();
  };

  // 保存指令库
  const handleSave = async (values) => {
    try {
      if (editingLibrary) {
        await libraryAPI.updateLibrary(editingLibrary.id, values);
        message.success('指令库更新成功');
      } else {
        await libraryAPI.createLibrary(values);
        message.success('指令库创建成功');
      }
      
      closeModal();
      fetchLibraries();
    } catch (error) {
      message.error(apiUtils.handleError(error, '保存指令库失败'));
    }
  };

  // 删除指令库
  const handleDelete = async (libraryId) => {
    try {
      await libraryAPI.deleteLibrary(libraryId);
      message.success('指令库删除成功');
      fetchLibraries();
    } catch (error) {
      message.error(apiUtils.handleError(error, '删除指令库失败'));
    }
  };

  // 选择指令库 - 修改为跳转到指令数据管理页面
  const handleSelectLibrary = (library) => {
    localStorage.setItem('currentLibrary', JSON.stringify(library));
    onLibrarySelect(library);
    message.success(`已选择指令库：${library.name}`, 1.5);
    
    // 跳转到指令数据管理页面
    if (navigate) {
      setTimeout(() => {
        navigate('/instructions');
      }, 500); // 给用户看到选择成功的消息
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '指令库名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <DatabaseOutlined style={{ color: '#1890ff' }} />
          <span style={{ fontWeight: 'bold' }}>{text}</span>
          {!record.is_active && <Tag color="red">已禁用</Tag>}
        </div>
      ),
    },
    {
      title: '语言',
      dataIndex: 'language',
      key: 'language',
      render: (language) => {
        const option = languageOptions.find(opt => opt.value === language);
        return option ? option.label : language;
      },
    },
    {
      title: '业务编码',
      dataIndex: 'business_code',
      key: 'business_code',
      render: (code) => code || '-',
    },
    {
      title: '统计信息',
      key: 'stats',
      render: (_, record) => (
        <Space>
          <Tag color="blue">
            <MessageOutlined style={{ marginRight: 4 }} />
            指令: {record.instruction_count || 0}
          </Tag>
          <Tag color="green">
            <TagsOutlined style={{ marginRight: 4 }} />
            词槽: {record.slot_count || 0}
          </Tag>
          <Tag color="orange">
            <BranchesOutlined style={{ marginRight: 4 }} />
            版本: v{record.latest_version || 0}
          </Tag>
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_time',
      key: 'created_time',
      render: (time) => formatLocalTime(time),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            onClick={() => handleSelectLibrary(record)}
          >
            选择
          </Button>
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => openModal(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个指令库吗？"
            description="删除后将无法恢复，包括所有的指令数据、词槽和训练记录。"
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

  return (
    <div className="library-management">
      {/* 页面头部 */}
      <div style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8} md={6}>
            <Card>
              <Statistic
                title="指令库总数"
                value={Array.isArray(libraries) ? libraries.length : 0}
                prefix={<DatabaseOutlined style={{ color: '#1890ff' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Card>
              <Statistic
                title="启用的指令库"
                value={Array.isArray(libraries) ? libraries.filter(lib => lib.is_active).length : 0}
                prefix={<SettingOutlined style={{ color: '#52c41a' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Card>
              <Statistic
                title="总指令数"
                value={Array.isArray(libraries) ? libraries.reduce((sum, lib) => sum + (lib.instruction_count || 0), 0) : 0}
                prefix={<MessageOutlined style={{ color: '#fa8c16' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8} md={6}>
            <Card>
              <Statistic
                title="总词槽数"
                value={Array.isArray(libraries) ? libraries.reduce((sum, lib) => sum + (lib.slot_count || 0), 0) : 0}
                prefix={<TagsOutlined style={{ color: '#722ed1' }} />}
              />
            </Card>
          </Col>
        </Row>
      </div>

      {/* 指令库列表 */}
      <Card
        title="指令库列表"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openModal()}
          >
            创建指令库
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={safeTableDataSource(libraries)}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个指令库`,
          }}
        />
      </Card>

      {/* 创建/编辑模态框 */}
      <Modal
        title={editingLibrary ? '编辑指令库' : '创建指令库'}
        open={modalVisible}
        onCancel={closeModal}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
        >
          <Form.Item
            name="name"
            label="指令库名称"
            rules={[
              { required: true, message: '请输入指令库名称' },
              { max: 100, message: '指令库名称不能超过100个字符' }
            ]}
          >
            <Input placeholder="请输入指令库名称" autoComplete="off" />
          </Form.Item>

          <Form.Item
            name="language"
            label="语言"
            rules={[{ required: true, message: '请选择语言' }]}
          >
            <Select placeholder="请选择语言">
              {languageOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="business_code"
            label="业务编码"
            rules={[{ max: 50, message: '业务编码不能超过50个字符' }]}
          >
            <Input placeholder="请输入业务编码（可选）" autoComplete="off" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
            rules={[{ max: 500, message: '描述不能超过500个字符' }]}
          >
            <Input.TextArea
              rows={4}
              placeholder="请输入指令库描述（可选）"
              autoComplete="off"
            />
          </Form.Item>

          <Form.Item
            name="created_by"
            label="创建人"
            rules={[{ max: 50, message: '创建人不能超过50个字符' }]}
          >
            <Input placeholder="请输入创建人（可选）" autoComplete="off" />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={closeModal}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingLibrary ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default LibraryManagement; 