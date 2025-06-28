import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  message, 
  Popconfirm, 
  Space,
  Typography,
  Drawer,
  List,
  Switch,
  Select,
  Tag,
  Divider
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  BulbOutlined,
  MessageOutlined,
  SoundOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { intentAPI } from '../api';
import CustomLoading from '../components/CustomLoading';

const { TextArea } = Input;
const { Title, Text } = Typography;
const { Option } = Select;

const IntentManagement = () => {
  const [intents, setIntents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingIntent, setEditingIntent] = useState(null);
  const [utteranceDrawerVisible, setUtteranceDrawerVisible] = useState(false);
  const [selectedIntent, setSelectedIntent] = useState(null);
  const [utterances, setUtterances] = useState([]);
  const [form] = Form.useForm();
  const [utteranceForm] = Form.useForm();

  // 模拟词槽数据（实际应该从API获取）
  const mockSlots = [
    { value: 'city', label: '城市' },
    { value: 'date', label: '日期' },
    { value: 'time', label: '时间' },
    { value: 'person_name', label: '人名' },
    { value: 'amount', label: '金额' }
  ];

  useEffect(() => {
    loadIntents();
  }, []);

  const loadIntents = async () => {
    setLoading(true);
    try {
      const response = await intentAPI.getIntents();
      setIntents(response.data || []);
    } catch (error) {
      message.error('加载意图列表失败');
      console.error('加载意图失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUtterances = async (intentId) => {
    try {
      const response = await intentAPI.getUtterances(intentId);
      setUtterances(response.data || []);
    } catch (error) {
      message.error('加载相似问失败');
      console.error('加载相似问失败:', error);
    }
  };

  const handleCreateIntent = () => {
    setEditingIntent(null);
    setModalVisible(true);
    form.resetFields();
  };

  const handleEditIntent = (intent) => {
    setEditingIntent(intent);
    setModalVisible(true);
    form.setFieldsValue({
      intent_name: intent.description, // 意图名称（中文）来自description字段
      intent_code: intent.intent_name,  // 意图编码（英文）来自intent_name字段
      description: intent.description   // 意图表述
    });
  };

  const handleDeleteIntent = async (intentId) => {
    try {
      await intentAPI.deleteIntent(intentId);
      message.success('删除成功');
      loadIntents();
    } catch (error) {
      message.error('删除失败');
      console.error('删除意图失败:', error);
    }
  };

  const handleSubmitIntent = async (values) => {
    try {
      const intentData = {
        intent_name: values.intent_code,
        description: values.intent_name
      };

      if (editingIntent) {
        await intentAPI.updateIntent(editingIntent.id, intentData);
        message.success('更新成功');
      } else {
        await intentAPI.createIntent(intentData);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadIntents();
    } catch (error) {
      message.error(editingIntent ? '更新失败' : '创建失败');
      console.error('提交意图失败:', error);
    }
  };

  const handleShowUtterances = (intent) => {
    setSelectedIntent(intent);
    setUtteranceDrawerVisible(true);
    loadUtterances(intent.id);
  };

  const handleAddUtterance = async (values) => {
    if (!selectedIntent) return;
    
    try {
      // 查重逻辑
      const isDuplicate = utterances.some(u => u.text.trim() === values.text.trim());
      if (isDuplicate) {
        message.warning('该相似问已存在');
        return;
      }

      await intentAPI.createUtterance(selectedIntent.id, values);
      message.success('添加相似问成功');
      utteranceForm.resetFields();
      loadUtterances(selectedIntent.id);
    } catch (error) {
      message.error('添加相似问失败');
      console.error('添加相似问失败:', error);
    }
  };

  const handleDeleteUtterance = async (utteranceId) => {
    try {
      await intentAPI.deleteUtterance(utteranceId);
      message.success('删除成功');
      loadUtterances(selectedIntent.id);
    } catch (error) {
      message.error('删除失败');
      console.error('删除相似问失败:', error);
    }
  };

  // 表格列配置
  const intentColumns = [
    {
      title: '意图名称',
      dataIndex: 'description',
      key: 'description',
      render: (text) => <Text strong>{text || '未设置'}</Text>
    },
    {
      title: '意图编码',
      dataIndex: 'intent_name',
      key: 'intent_name',
      render: (text) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '关联词槽',
      dataIndex: 'slot_name',
      key: 'slot_name',
      render: (text) => text ? <Tag color="green">{text}</Tag> : <Text type="secondary">无</Text>
    },
    {
      title: '相似指令',
      key: 'utterances',
      render: (_, record) => (
        <Button 
          type="link" 
          icon={<MessageOutlined />}
          onClick={() => handleShowUtterances(record)}
        >
          管理相似问
        </Button>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => text ? new Date(text).toLocaleString() : '-',
      width: 180,
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<EditOutlined />}
            onClick={() => handleEditIntent(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个意图吗？"
            onConfirm={() => handleDeleteIntent(record.id)}
            icon={<QuestionCircleOutlined style={{ color: 'red' }} />}
          >
            <Button 
              type="link" 
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0 }}>意图管理</Title>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleCreateIntent}
          >
            新建意图
          </Button>
        </div>
        
        <Table
          columns={intentColumns}
          dataSource={intents}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 新建/编辑意图模态框 */}
      <Modal
        title={editingIntent ? '编辑意图' : '新建意图'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="horizontal"
          onFinish={handleSubmitIntent}
          labelCol={{ span: 6 }}
          labelAlign='left'
        >
          <Form.Item
            name="intent_name"
            label="意图名称"
            rules={[{ required: true, message: '请输入意图名称' }]}
          >
            <Input placeholder="如：查询天气" />
          </Form.Item>

          <Form.Item
            name="intent_code"
            label="意图编码"
            rules={[
              { required: true, message: '请输入意图编码' },
              { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: '编码只能包含字母、数字和下划线，且不能以数字开头' }
            ]}
          >
            <Input placeholder="如：query_weather" />
          </Form.Item>

          <Form.Item
            name="description"
            label="意图表述"
            rules={[{ required: true, message: '请输入意图表述' }]}
          >
            <TextArea rows={3} placeholder="描述此意图的用途和功能" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingIntent ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 相似问管理抽屉 */}
      <Drawer
        title={`管理相似问 - ${selectedIntent?.intent_name || ''}`}
        placement="right"
        width={600}
        open={utteranceDrawerVisible}
        onClose={() => setUtteranceDrawerVisible(false)}
      >
        <div style={{ marginBottom: 16 }}>
          <Form
            form={utteranceForm}
            layout="vertical"
            onFinish={handleAddUtterance}
          >
            <Form.Item
              name="text"
              label="添加相似问"
              rules={[{ required: true, message: '请输入相似问内容' }]}
            >
              <Input.Search
                placeholder="输入相似问内容"
                enterButton="添加"
                onSearch={() => utteranceForm.submit()}
              />
            </Form.Item>
          </Form>
        </div>

        <Divider />

        <div style={{ marginBottom: 16 }}>
          <Title level={5} style={{ margin: 0, color: '#666' }}>
            相似指令（{utterances.length}个）
          </Title>
        </div>

        <List
          dataSource={utterances}
          renderItem={(item, index) => (
            <List.Item
              actions={[
                <Button 
                  type="link" 
                  size="small"
                  onClick={() => {
                    // 编辑功能（可选）
                    Modal.info({
                      title: '编辑相似问',
                      content: '编辑功能待实现'
                    });
                  }}
                >
                  编辑
                </Button>,
                <Popconfirm
                  title="确定要删除这个相似问吗？"
                  onConfirm={() => handleDeleteUtterance(item.id)}
                >
                  <Button type="link" size="small" danger>
                    删除
                  </Button>
                </Popconfirm>
              ]}
            >
              <div style={{ width: '100%', padding: '8px 0' }}>
                <Text>{item.text}</Text>
              </div>
            </List.Item>
          )}
          locale={{ emptyText: '暂无相似问，请添加' }}
        />
              </Drawer>

        {/* 页面loading */}
        <CustomLoading 
          visible={loading && intents.length === 0} 
          text="正在加载意图数据" 
          description="正在获取意图列表..."
        />
      </div>
    );
  };
  
  export default IntentManagement;

