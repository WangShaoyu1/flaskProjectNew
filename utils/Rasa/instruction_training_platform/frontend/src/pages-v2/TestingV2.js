import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Form, Input, Select, message, App,
  Row, Col, Statistic, Upload, List, Badge, Tabs, Progress,
  Tag, Space, Tooltip, Alert, Divider, Steps, Timeline
} from 'antd';
import {
  ExperimentOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  UploadOutlined,
  DownloadOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  BugOutlined
} from '@ant-design/icons';
import { testAPI, versionAPI, apiUtils } from '../api-v2';
import { formatLocalTime } from '../utils/timeUtils';
import { safeTableDataSource } from '../utils/dataSourceUtils';

const { TextArea } = Input;
const { TabPane } = Tabs;
const { Step } = Steps;

const TestingV2 = ({ currentLibrary }) => {
  const [loading, setLoading] = useState(false);
  const [testRecords, setTestRecords] = useState([]);
  const [availableVersions, setAvailableVersions] = useState([]);
  const [currentVersion, setCurrentVersion] = useState(null);
  const [singleTestResult, setSingleTestResult] = useState(null);
  const [batchTestStatus, setBatchTestStatus] = useState(null);
  
  // 模态框状态
  const [singleTestModalVisible, setSingleTestModalVisible] = useState(false);
  const [batchTestModalVisible, setBatchTestModalVisible] = useState(false);
  const [testDetailModalVisible, setTestDetailModalVisible] = useState(false);
  const [currentTestRecord, setCurrentTestRecord] = useState(null);
  
  const [singleTestForm] = Form.useForm();
  const [batchTestForm] = Form.useForm();

  // 检查是否选择了指令库
  if (!currentLibrary) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <ExperimentOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
          <h3>请先选择指令库</h3>
          <p style={{ color: '#666' }}>在开始测试之前，请先在指令库管理页面选择一个指令库。</p>
        </div>
      </Card>
    );
  }

  // 获取可用版本
  const fetchAvailableVersions = async () => {
    try {
      const response = await versionAPI.getVersions({ 
        library_id: currentLibrary.id,
        status_filter: 'success'
      });
      setAvailableVersions(response.data.versions || []);
      
      // 获取当前激活版本
      const activeResponse = await versionAPI.getActiveVersion(currentLibrary.id);
      setCurrentVersion(activeResponse.data.version);
    } catch (error) {
      console.error('获取版本信息失败:', error);
    }
  };

  // 获取测试记录
  const fetchTestRecords = async () => {
    setLoading(true);
    try {
      const response = await testAPI.getTestRecords({ library_id: currentLibrary.id });
      setTestRecords(response.data.test_records || []);
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取测试记录失败'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentLibrary) {
      fetchAvailableVersions();
      fetchTestRecords();
    }
  }, [currentLibrary]);

  // 单条测试
  const handleSingleTest = async (values) => {
    try {
      setLoading(true);
      const response = await testAPI.singleTest({
        library_id: currentLibrary.id,
        model_version_id: values.model_version_id || currentVersion?.id,
        input_text: values.input_text
      });
      
      setSingleTestResult(response.data);
      message.success('测试完成');
    } catch (error) {
      message.error(apiUtils.handleError(error, '测试失败'));
    } finally {
      setLoading(false);
    }
  };

  // 批量测试
  const handleBatchTest = async (values) => {
    try {
      setLoading(true);
      
      const formData = new FormData();
      if (values.test_file && values.test_file.length > 0) {
        formData.append('file', values.test_file[0].originFileObj);
      }
      formData.append('library_id', currentLibrary.id);
      formData.append('model_version_id', values.model_version_id || currentVersion?.id);
      formData.append('test_name', values.test_name || '批量测试');
      
      const response = await testAPI.batchTest(formData);
      setBatchTestStatus(response.data);
      message.success(`批量测试完成: ${response.data.message}`);
      setBatchTestModalVisible(false);
      batchTestForm.resetFields();
      
      // 刷新测试记录
      setTimeout(() => {
        fetchTestRecords();
      }, 1000);
    } catch (error) {
      message.error(apiUtils.handleError(error, '批量测试启动失败'));
    } finally {
      setLoading(false);
    }
  };

  // 查看测试详情
  const viewTestDetail = async (record) => {
    setCurrentTestRecord(record);
    setTestDetailModalVisible(true);
  };

  // 删除测试记录
  const handleDeleteTestRecord = async (recordId) => {
    try {
      await testAPI.deleteTestRecord(recordId);
      message.success('测试记录删除成功');
      fetchTestRecords();
    } catch (error) {
      message.error(apiUtils.handleError(error, '删除测试记录失败'));
    }
  };

  // 下载测试模板
  const handleDownloadTemplate = async () => {
    try {
      const response = await testAPI.downloadTemplate();
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = '测试模板.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('测试模板下载成功');
    } catch (error) {
      message.error(apiUtils.handleError(error, '下载模板失败'));
    }
  };

  // 导出测试结果
  const handleExportResults = async (recordId, testName) => {
    try {
      const response = await testAPI.exportResults(recordId);
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `测试结果_${testName}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('测试结果导出成功');
    } catch (error) {
      message.error(apiUtils.handleError(error, '导出结果失败'));
    }
  };

  // 渲染单条测试结果
  const renderSingleTestResult = () => {
    if (!singleTestResult) return null;

    const { intent, confidence, entities, response_time } = singleTestResult;
    
    return (
      <Card 
        title="测试结果" 
        style={{ marginTop: 16 }}
        extra={
          <Tag color={confidence >= 0.8 ? 'green' : confidence >= 0.6 ? 'orange' : 'red'}>
            置信度: {(confidence * 100).toFixed(1)}%
          </Tag>
        }
      >
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Statistic
              title="识别意图"
              value={intent || '未识别'}
              prefix={<ExperimentOutlined style={{ color: '#1890ff' }} />}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="响应时间"
              value={response_time || 0}
              suffix="ms"
              prefix={<ClockCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Col>
        </Row>
        
        {entities && entities.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <h4>实体提取结果:</h4>
            <Space wrap>
              {entities.map((entity, index) => (
                <Tag key={index} color="blue">
                  {entity.entity}: {entity.value}
                </Tag>
              ))}
            </Space>
          </div>
        )}
      </Card>
    );
  };

  // 测试记录表格列定义
  const testRecordColumns = [
    {
      title: '测试名称',
      dataIndex: 'test_name',
      key: 'test_name',
      render: (name, record) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{name}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            类型: {record.test_type === 'single' ? '单条测试' : '批量测试'}
          </div>
        </div>
      ),
    },
    {
      title: '测试状态',
      dataIndex: 'test_status',
      key: 'test_status',
      width: 120,
      render: (status) => {
        const statusConfig = {
          'running': { color: 'processing', text: '运行中', icon: <ClockCircleOutlined /> },
          'completed': { color: 'success', text: '已完成', icon: <CheckCircleOutlined /> },
          'failed': { color: 'error', text: '失败', icon: <CloseCircleOutlined /> }
        };
        const config = statusConfig[status] || { color: 'default', text: status };
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
      title: '测试结果',
      key: 'test_result',
      width: 200,
      render: (_, record) => (
        <div>
          <div>
            总数: {record.total_count || 0} | 
            成功: {record.success_count || 0}
          </div>
          <Progress 
            percent={record.total_count ? ((record.success_count || 0) / record.total_count * 100) : 0}
            size="small"
            status={record.success_rate >= 80 ? 'success' : record.success_rate >= 60 ? 'normal' : 'exception'}
          />
        </div>
      ),
    },
    {
      title: '平均置信度',
      dataIndex: 'avg_confidence',
      key: 'avg_confidence',
      width: 120,
      render: (confidence) => (
        <Tag color={confidence >= 0.8 ? 'green' : confidence >= 0.6 ? 'orange' : 'red'}>
          {confidence ? (confidence * 100).toFixed(1) + '%' : '-'}
        </Tag>
      ),
    },
    {
      title: '测试时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 150,
      render: (time) => formatLocalTime(time),
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
              onClick={() => viewTestDetail(record)}
            />
          </Tooltip>
          <Tooltip title="下载报告">
            <Button
              type="text"
              icon={<DownloadOutlined />}
              onClick={() => handleExportResults(record.id, record.test_name)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteTestRecord(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="testing-v2">
      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="总测试次数"
              value={testRecords.length}
              prefix={<ExperimentOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="成功测试"
              value={testRecords.filter(r => r.test_status === 'completed').length}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="平均成功率"
              value={testRecords.length > 0 ? 
                (testRecords.reduce((sum, r) => sum + (r.success_rate || 0), 0) / testRecords.length).toFixed(1) : 0}
              suffix="%"
              prefix={<BarChartOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="当前版本"
              value={currentVersion ? `v${currentVersion.version_number}` : '未选择'}
              prefix={<FileTextOutlined style={{ color: '#722ed1' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 版本信息提示 */}
      {currentVersion && (
        <Alert
          message={`当前测试版本: v${currentVersion.version_number}`}
          description={`状态: ${currentVersion.training_status} | 意图数量: ${currentVersion.intent_count} | 创建时间: ${formatLocalTime(currentVersion.created_time)}`}
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <Row gutter={[16, 16]}>
        {/* 快速测试区域 */}
        <Col xs={24} lg={12}>
          <Card
            title="快速单条测试"
            extra={
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={() => setSingleTestModalVisible(true)}
              >
                详细测试
              </Button>
            }
          >
            <Form
              form={singleTestForm}
              layout="vertical"
              onFinish={handleSingleTest}
            >
              <Form.Item
                name="input_text"
                label="测试文本"
                rules={[{ required: true, message: '请输入测试文本' }]}
              >
                <TextArea
                  rows={3}
                  placeholder="请输入要测试的文本..."
                  maxLength={200}
                  showCount
                />
              </Form.Item>
              
              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<PlayCircleOutlined />}
                >
                  立即测试
                </Button>
              </Form.Item>
            </Form>

            {renderSingleTestResult()}
          </Card>
        </Col>

        {/* 批量测试区域 */}
        <Col xs={24} lg={12}>
          <Card
            title="批量测试"
            extra={
              <Button
                type="primary"
                icon={<UploadOutlined />}
                onClick={() => setBatchTestModalVisible(true)}
              >
                开始批量测试
              </Button>
            }
          >
            <div style={{ textAlign: 'center', padding: '40px 20px' }}>
              <UploadOutlined style={{ fontSize: '48px', color: '#ccc', marginBottom: '16px' }} />
              <h3>批量测试</h3>
              <p style={{ color: '#666', marginBottom: '24px' }}>
                上传CSV或Excel文件进行批量测试
              </p>
              <Space direction="vertical">
                <Button
                  type="primary"
                  icon={<UploadOutlined />}
                  onClick={() => setBatchTestModalVisible(true)}
                >
                  选择测试文件
                </Button>
                <Button 
                  type="link" 
                  icon={<DownloadOutlined />}
                  onClick={handleDownloadTemplate}
                >
                  下载测试模板
                </Button>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 测试记录 */}
      <Card 
        title="测试记录" 
        style={{ marginTop: 24 }}
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchTestRecords}
          >
            刷新
          </Button>
        }
      >
        <Table
          columns={testRecordColumns}
          dataSource={safeTableDataSource(testRecords)}
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

      {/* 单条测试详细模态框 */}
      <Modal
        title="详细单条测试"
        open={singleTestModalVisible}
        onCancel={() => setSingleTestModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form layout="vertical" onFinish={handleSingleTest}>
          <Form.Item
            name="model_version_id"
            label="选择测试版本"
          >
            <Select placeholder="选择版本（默认使用当前激活版本）">
              {availableVersions.map(version => (
                <Select.Option key={version.id} value={version.id}>
                  v{version.version_number} - {version.training_status}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="input_text"
            label="测试文本"
            rules={[{ required: true, message: '请输入测试文本' }]}
          >
            <TextArea
              rows={4}
              placeholder="请输入要测试的文本..."
              maxLength={500}
              showCount
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button onClick={() => setSingleTestModalVisible(false)}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<PlayCircleOutlined />}
              >
                开始测试
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量测试模态框 */}
      <Modal
        title="批量测试"
        open={batchTestModalVisible}
        onCancel={() => setBatchTestModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form
          form={batchTestForm}
          layout="vertical"
          onFinish={handleBatchTest}
        >
          <Form.Item
            name="test_name"
            label="测试名称"
            rules={[{ required: true, message: '请输入测试名称' }]}
          >
            <Input placeholder="请输入测试名称" autoComplete="off" />
          </Form.Item>

          <Form.Item
            name="model_version_id"
            label="选择测试版本"
          >
            <Select placeholder="选择版本（默认使用当前激活版本）">
              {availableVersions.map(version => (
                <Select.Option key={version.id} value={version.id}>
                  v{version.version_number} - {version.training_status}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="test_file"
            label="测试文件"
            valuePropName="fileList"
            getValueFromEvent={(e) => {
              if (Array.isArray(e)) {
                return e;
              }
              return e && e.fileList;
            }}
            rules={[{ required: true, message: '请选择测试文件' }]}
          >
            <Upload
              accept=".csv,.xlsx,.xls"
              beforeUpload={() => false}
              maxCount={1}
            >
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>

          <Alert
            message="文件格式要求"
            description="支持CSV和Excel格式，文件应包含'text'列（必需）和'expected_intent'列（可选）"
            type="info"
            style={{ marginBottom: 16 }}
          />

          <Form.Item>
            <Space>
              <Button onClick={() => setBatchTestModalVisible(false)}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<PlayCircleOutlined />}
              >
                开始批量测试
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 测试详情模态框 */}
      <Modal
        title={`测试详情 - ${currentTestRecord?.test_name}`}
        open={testDetailModalVisible}
        onCancel={() => setTestDetailModalVisible(false)}
        footer={null}
        width={900}
      >
        {currentTestRecord && (
          <Tabs defaultActiveKey="1">
            <TabPane tab="基本信息" key="1">
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Statistic title="测试类型" value={currentTestRecord.test_type === 'single' ? '单条测试' : '批量测试'} />
                </Col>
                <Col span={12}>
                  <Statistic title="测试状态" value={currentTestRecord.test_status} />
                </Col>
                <Col span={12}>
                  <Statistic title="总测试数" value={currentTestRecord.total_count || 0} />
                </Col>
                <Col span={12}>
                  <Statistic title="成功数" value={currentTestRecord.success_count || 0} />
                </Col>
                <Col span={12}>
                  <Statistic title="成功率" value={currentTestRecord.success_rate || 0} suffix="%" />
                </Col>
                <Col span={12}>
                  <Statistic title="平均置信度" value={currentTestRecord.avg_confidence ? (currentTestRecord.avg_confidence * 100).toFixed(1) : 0} suffix="%" />
                </Col>
              </Row>
            </TabPane>
            
            <TabPane tab="测试报告" key="2">
              <div style={{ textAlign: 'center', padding: '50px' }}>
                <FileTextOutlined style={{ fontSize: '48px', color: '#ccc', marginBottom: '16px' }} />
                <h3>详细测试报告</h3>
                <p style={{ color: '#666' }}>测试报告功能开发中...</p>
              </div>
            </TabPane>
          </Tabs>
        )}
      </Modal>
    </div>
  );
};

export default TestingV2; 