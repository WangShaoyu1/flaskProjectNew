import React, { useState, useEffect } from 'react';
import { 
  Modal, Button, Steps, Upload, Progress, message, Alert,
  Table, Checkbox, Space, Tabs, List, Tag, Divider,
  Select, Input, Card, Statistic, Row, Col
} from 'antd';
import {
  UploadOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  FileExcelOutlined,
  DatabaseOutlined,
  SyncOutlined,
  EditOutlined
} from '@ant-design/icons';

const { Step } = Steps;
const { TextArea } = Input;

const BatchOperations = ({ 
  visible, 
  onCancel, 
  onSuccess,
  operationType, // 'import', 'export', 'update', 'delete'
  dataType, // 'instructions', 'slots', 'similar_questions'
  selectedItems = [],
  onItemsChange
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [operationResult, setOperationResult] = useState(null);
  const [previewData, setPreviewData] = useState([]);
  const [validationErrors, setValidationErrors] = useState([]);
  const [fileList, setFileList] = useState([]);
  
  // 重置状态
  const resetState = () => {
    setCurrentStep(0);
    setLoading(false);
    setUploadProgress(0);
    setOperationResult(null);
    setPreviewData([]);
    setValidationErrors([]);
    setFileList([]);
  };

  useEffect(() => {
    if (!visible) {
      resetState();
    }
  }, [visible]);

  // 步骤配置
  const getSteps = () => {
    switch (operationType) {
      case 'import':
        return [
          { title: '上传文件', description: '选择要导入的Excel文件' },
          { title: '数据预览', description: '预览和验证数据' },
          { title: '执行导入', description: '批量导入数据' },
          { title: '完成', description: '查看导入结果' }
        ];
      case 'export':
        return [
          { title: '选择数据', description: '选择要导出的数据' },
          { title: '配置选项', description: '设置导出格式和选项' },
          { title: '生成文件', description: '生成并下载文件' }
        ];
      case 'update':
        return [
          { title: '选择项目', description: '选择要更新的项目' },
          { title: '批量编辑', description: '设置更新内容' },
          { title: '执行更新', description: '批量更新数据' },
          { title: '完成', description: '查看更新结果' }
        ];
      case 'delete':
        return [
          { title: '选择项目', description: '选择要删除的项目' },
          { title: '确认删除', description: '确认删除操作' },
          { title: '执行删除', description: '批量删除数据' }
        ];
      default:
        return [];
    }
  };

  // 处理文件上传
  const handleFileUpload = async (file) => {
    setLoading(true);
    try {
      // 模拟文件解析
      setUploadProgress(20);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setUploadProgress(60);
      // 这里应该调用API解析文件
      const mockPreviewData = [
        { id: 1, instruction_name: '开灯', instruction_code: 'LIGHT_ON', category: '智能家居', status: 'valid' },
        { id: 2, instruction_name: '关灯', instruction_code: 'LIGHT_OFF', category: '智能家居', status: 'valid' },
        { id: 3, instruction_name: '', instruction_code: 'INVALID', category: '', status: 'error' }
      ];
      
      setUploadProgress(100);
      setPreviewData(mockPreviewData);
      
      // 模拟验证错误
      const errors = mockPreviewData.filter(item => item.status === 'error');
      setValidationErrors(errors);
      
      message.success('文件解析完成');
      setCurrentStep(1);
    } catch (error) {
      message.error('文件解析失败');
    } finally {
      setLoading(false);
    }
  };

  // 执行批量操作
  const executeBatchOperation = async () => {
    setLoading(true);
    try {
      // 模拟批量操作
      setUploadProgress(0);
      for (let i = 0; i <= 100; i += 10) {
        setUploadProgress(i);
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      const result = {
        total: previewData.length,
        success: previewData.filter(item => item.status === 'valid').length,
        failed: previewData.filter(item => item.status === 'error').length,
        details: previewData
      };
      
      setOperationResult(result);
      setCurrentStep(currentStep + 1);
      message.success('批量操作完成');
    } catch (error) {
      message.error('批量操作失败');
    } finally {
      setLoading(false);
    }
  };

  // 渲染文件上传步骤
  const renderUploadStep = () => (
    <div style={{ textAlign: 'center', padding: '40px' }}>
      <Upload
        fileList={fileList}
        beforeUpload={(file) => {
          setFileList([file]);
          handleFileUpload(file);
          return false;
        }}
        onRemove={() => {
          setFileList([]);
          setPreviewData([]);
          setValidationErrors([]);
          setCurrentStep(0);
        }}
        accept=".xlsx,.xls,.csv"
        maxCount={1}
      >
        <Button 
          icon={<UploadOutlined />} 
          size="large"
          loading={loading}
        >
          选择Excel文件
        </Button>
      </Upload>
      
      {loading && (
        <div style={{ marginTop: 20 }}>
          <Progress percent={uploadProgress} />
          <p style={{ marginTop: 10, color: '#666' }}>正在解析文件...</p>
        </div>
      )}
      
      <Alert
        message="文件格式要求"
        description={
          <div>
            <p>请确保Excel文件包含以下列：</p>
            <ul style={{ textAlign: 'left', display: 'inline-block' }}>
              <li>指令名称 (instruction_name)</li>
              <li>指令编码 (instruction_code)</li>
              <li>指令分类 (category)</li>
              <li>指令描述 (description)</li>
            </ul>
          </div>
        }
        type="info"
        style={{ marginTop: 20, textAlign: 'left' }}
      />
    </div>
  );

  // 渲染数据预览步骤
  const renderPreviewStep = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="总条数"
              value={previewData.length}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="有效条数"
              value={previewData.filter(item => item.status === 'valid').length}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="错误条数"
              value={validationErrors.length}
              prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
            />
          </Card>
        </Col>
      </Row>

      {validationErrors.length > 0 && (
        <Alert
          message={`发现 ${validationErrors.length} 条数据错误`}
          description="请修正错误后重新上传，或选择跳过错误数据继续导入"
          type="warning"
          style={{ marginBottom: 16 }}
          action={
            <Space>
              <Button size="small" type="primary" ghost>
                下载错误报告
              </Button>
              <Button size="small" type="primary">
                修正错误
              </Button>
            </Space>
          }
        />
      )}

      <Table
        dataSource={previewData}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
        columns={[
          {
            title: '状态',
            dataIndex: 'status',
            width: 80,
            render: (status) => (
              <Tag color={status === 'valid' ? 'success' : 'error'}>
                {status === 'valid' ? (
                  <>
                    <CheckCircleOutlined /> 有效
                  </>
                ) : (
                  <>
                    <CloseCircleOutlined /> 错误
                  </>
                )}
              </Tag>
            )
          },
          {
            title: '指令名称',
            dataIndex: 'instruction_name',
            width: 150
          },
          {
            title: '指令编码',
            dataIndex: 'instruction_code',
            width: 150
          },
          {
            title: '分类',
            dataIndex: 'category',
            width: 120
          },
          {
            title: '操作',
            width: 100,
            render: (_, record) => (
              <Space>
                <Button type="text" icon={<EditOutlined />} size="small">
                  编辑
                </Button>
              </Space>
            )
          }
        ]}
      />
    </div>
  );

  // 渲染执行步骤
  const renderExecuteStep = () => (
    <div style={{ textAlign: 'center', padding: '40px' }}>
      <div style={{ marginBottom: 24 }}>
        <SyncOutlined 
          style={{ fontSize: '48px', color: '#1890ff' }} 
          spin={loading}
        />
        <h3 style={{ marginTop: 16 }}>
          {loading ? '正在执行批量操作...' : '准备执行批量操作'}
        </h3>
      </div>
      
      {loading && (
        <div style={{ marginBottom: 24 }}>
          <Progress percent={uploadProgress} />
          <p style={{ marginTop: 10, color: '#666' }}>
            正在处理 {previewData.filter(item => item.status === 'valid').length} 条有效数据
          </p>
        </div>
      )}
      
      <Alert
        message="操作提醒"
        description="批量操作将会修改数据库，请确认无误后继续"
        type="info"
        style={{ marginBottom: 24 }}
      />
      
      {!loading && (
        <Button 
          type="primary" 
          size="large"
          onClick={executeBatchOperation}
        >
          开始执行
        </Button>
      )}
    </div>
  );

  // 渲染完成步骤
  const renderCompleteStep = () => (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        <CheckCircleOutlined 
          style={{ fontSize: '48px', color: '#52c41a', marginBottom: 16 }} 
        />
        <h3>批量操作完成</h3>
      </div>
      
      {operationResult && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="总处理数"
                value={operationResult.total}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="成功数"
                value={operationResult.success}
                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="失败数"
                value={operationResult.failed}
                prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
              />
            </Card>
          </Col>
        </Row>
      )}
      
      <Space style={{ width: '100%', justifyContent: 'center' }}>
        <Button icon={<DownloadOutlined />}>
          下载详细报告
        </Button>
        <Button type="primary" onClick={() => {
          onSuccess && onSuccess(operationResult);
          onCancel();
        }}>
          完成
        </Button>
      </Space>
    </div>
  );

  // 渲染当前步骤内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return renderUploadStep();
      case 1:
        return renderPreviewStep();
      case 2:
        return renderExecuteStep();
      case 3:
        return renderCompleteStep();
      default:
        return null;
    }
  };

  // 获取操作标题
  const getOperationTitle = () => {
    const typeMap = {
      import: '批量导入',
      export: '批量导出',
      update: '批量更新',
      delete: '批量删除'
    };
    
    const dataMap = {
      instructions: '指令',
      slots: '词槽',
      similar_questions: '相似问'
    };
    
    return `${typeMap[operationType] || '批量操作'} ${dataMap[dataType] || '数据'}`;
  };

  return (
    <Modal
      title={getOperationTitle()}
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={800}
      maskClosable={false}
    >
      <Steps current={currentStep} style={{ marginBottom: 24 }}>
        {getSteps().map((step, index) => (
          <Step
            key={index}
            title={step.title}
            description={step.description}
            status={
              index < currentStep ? 'finish' :
              index === currentStep ? (loading ? 'process' : 'wait') :
              'wait'
            }
          />
        ))}
      </Steps>
      
      <div style={{ minHeight: '400px' }}>
        {renderStepContent()}
      </div>
    </Modal>
  );
};

export default BatchOperations; 