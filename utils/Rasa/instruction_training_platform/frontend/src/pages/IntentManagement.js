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
  Tabs, 
  Tag,
  Space,
  Typography,
  Divider
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  BulbOutlined,
  MessageOutlined,
  SoundOutlined
} from '@ant-design/icons';
import { intentAPI } from '../api';

const { TextArea } = Input;
const { TabPane } = Tabs;
const { Title, Text } = Typography;

const IntentManagement = () => {
  const [intents, setIntents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingIntent, setEditingIntent] = useState(null);
  const [selectedIntent, setSelectedIntent] = useState(null);
  const [utterances, setUtterances] = useState([]);
  const [responses, setResponses] = useState([]);
  const [form] = Form.useForm();
  const [utteranceForm] = Form.useForm();
  const [responseForm] = Form.useForm();

  useEffect(() => {
    loadIntents();
  }, []);

  const loadIntents = async () => {
    setLoading(true);
    try {
      const response = await intentAPI.getIntents();
      setIntents(response.data);
    } catch (error) {
      message.error('加载意图列表失败');
      console.error('加载意图失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadIntentDetails = async (intentId) => {
    try {
      const [utterancesRes, responsesRes] = await Promise.all([
        intentAPI.getUtterances(intentId),
        intentAPI.getResponses(intentId)
      ]);
      setUtterances(utterancesRes.data);
      setResponses(responsesRes.data);
    } catch (error) {
      message.error('加载意图详情失败');
      console.error('加载意图详情失败:', error);
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
    form.setFieldsValue(intent);
  };

  const handleDeleteIntent = async (intentId) => {
    try {
      await intentAPI.deleteIntent(intentId);
      message.success('删除成功');
      loadIntents();
      if (selectedIntent?.id === intentId) {
        setSelectedIntent(null);
        setUtterances([]);
        setResponses([]);
      }
    } catch (error) {
      message.error('删除失败');
      console.error('删除意图失败:', error);
    }
  };

  const handleSubmitIntent = async (values) => {
    try {
      if (editingIntent) {
        await intentAPI.updateIntent(editingIntent.id, values);
        message.success('更新成功');
      } else {
        await intentAPI.createIntent(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadIntents();
    } catch (error) {
      message.error(editingIntent ? '更新失败' : '创建失败');
      console.error('提交意图失败:', error);
    }
  };

  const handleAddUtterance = async (values) => {
    if (!selectedIntent) return;
    
    try {
      await intentAPI.createUtterance(selectedIntent.id, values);
      message.success('添加相似问成功');
      utteranceForm.resetFields();
      loadIntentDetails(selectedIntent.id);
    } catch (error) {
      message.error('添加相似问失败');
      console.error('添加相似问失败:', error);
    }
  };

  const handleDeleteUtterance = async (utteranceId) => {
    try {
      await intentAPI.deleteUtterance(utteranceId);
      message.success('删除成功');
      loadIntentDetails(selectedIntent.id);
    } catch (error) {
      message.error('删除失败');
      console.error('删除相似问失败:', error);
    }
  };

  const handleAddResponse = async (values) => {
    if (!selectedIntent) return;
    
    try {
      await intentAPI.createResponse(selectedIntent.id, values);
      message.success('添加话术成功');
      responseForm.resetFields();
      loadIntentDetails(selectedIntent.id);
    } catch (error) {
      message.error('添加话术失败');
      console.error('添加话术失败:', error);
    }
  };

  const handleDeleteResponse = async (responseId) => {
    try {
      await intentAPI.deleteResponse(responseId);
      message.success('删除成功');
      loadIntentDetails(selectedIntent.id);
    } catch (error) {
      message.error('删除失败');
      console.error('删除话术失败:', error);
    }
  };

  const intentColumns = [
    {
      title: '意图名称',
      dataIndex: 'intent_name',
      key: 'intent_name',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString(),
      width: 180,
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<EditOutlined />}
            onClick={() => handleEditIntent(record)}
          >
            编辑
          </Button>
          <Button 
            type="link" 
            onClick={() => {
              setSelectedIntent(record);
              loadIntentDetails(record.id);
            }}
          >
            详情
          </Button>
          <Popconfirm
            title="确定要删除这个意图吗？"
            onConfirm={() => handleDeleteIntent(record.id)}
            okText="确定"
            cancelText="取消"
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
      ),
    },
  ];

  const utteranceColumns = [
    {
      title: '相似问文本',
      dataIndex: 'text',
      key: 'text',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString(),
      width: 180,
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Popconfirm
          title="确定要删除这个相似问吗？"
          onConfirm={() => handleDeleteUtterance(record.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button 
            type="link" 
            danger 
            icon={<DeleteOutlined />}
            size="small"
          >
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  const responseColumns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type) => {
        const colorMap = {
          success: 'green',
          failure: 'red',
          fallback: 'orange'
        };
        return <Tag color={colorMap[type] || 'blue'}>{type}</Tag>;
      }
    },
    {
      title: '话术内容',
      dataIndex: 'text',
      key: 'text',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString(),
      width: 180,
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Popconfirm
          title="确定要删除这个话术吗？"
          onConfirm={() => handleDeleteResponse(record.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button 
            type="link" 
            danger 
            icon={<DeleteOutlined />}
            size="small"
          >
            删除
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Card 
        title={
          <Space>
            <BulbOutlined />
            意图管理
          </Space>
        }
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={handleCreateIntent}
          >
            新建意图
          </Button>
        }
      >
        <Table
          columns={intentColumns}
          dataSource={intents}
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

      {selectedIntent && (
        <Card 
          title={`意图详情: ${selectedIntent.intent_name}`}
          style={{ marginTop: 24 }}
        >
          <Tabs defaultActiveKey="utterances">
            <TabPane 
              tab={
                <span>
                  <MessageOutlined />
                  相似问 ({utterances.length})
                </span>
              } 
              key="utterances"
            >
              <Form
                form={utteranceForm}
                onFinish={handleAddUtterance}
                layout="inline"
                style={{ marginBottom: 16 }}
              >
                <Form.Item
                  name="text"
                  rules={[{ required: true, message: '请输入相似问文本' }]}
                  style={{ flex: 1 }}
                >
                  <Input placeholder="输入相似问文本" />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit">
                    添加相似问
                  </Button>
                </Form.Item>
              </Form>

              <Table
                columns={utteranceColumns}
                dataSource={utterances}
                rowKey="id"
                size="small"
                pagination={false}
              />
            </TabPane>

            <TabPane 
              tab={
                <span>
                  <SoundOutlined />
                  话术 ({responses.length})
                </span>
              } 
              key="responses"
            >
              <Form
                form={responseForm}
                onFinish={handleAddResponse}
                layout="vertical"
                style={{ marginBottom: 16 }}
              >
                <Form.Item
                  name="type"
                  label="话术类型"
                  rules={[{ required: true, message: '请选择话术类型' }]}
                  initialValue="success"
                >
                  <select style={{ width: '100%', padding: '4px 8px' }}>
                    <option value="success">成功话术</option>
                    <option value="failure">失败话术</option>
                    <option value="fallback">兜底话术</option>
                  </select>
                </Form.Item>
                <Form.Item
                  name="text"
                  label="话术内容"
                  rules={[{ required: true, message: '请输入话术内容' }]}
                >
                  <TextArea rows={3} placeholder="输入话术内容" />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit">
                    添加话术
                  </Button>
                </Form.Item>
              </Form>

              <Table
                columns={responseColumns}
                dataSource={responses}
                rowKey="id"
                size="small"
                pagination={false}
              />
            </TabPane>
          </Tabs>
        </Card>
      )}

      <Modal
        title={editingIntent ? '编辑意图' : '新建意图'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          onFinish={handleSubmitIntent}
          layout="vertical"
        >
          <Form.Item
            name="intent_name"
            label="意图名称"
            rules={[
              { required: true, message: '请输入意图名称' },
              { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: '意图名称只能包含字母、数字和下划线，且以字母或下划线开头' }
            ]}
          >
            <Input placeholder="例如: greet, book_flight" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="描述这个意图的用途" />
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
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
    </div>
  );
};

export default IntentManagement;

