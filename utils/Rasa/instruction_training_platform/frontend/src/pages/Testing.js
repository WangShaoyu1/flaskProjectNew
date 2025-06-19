import React, { useState } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  Typography, 
  Space, 
  Divider,
  Upload,
  Table,
  Progress,
  Alert,
  message,
  Tabs,
  Form,
  Row,
  Col,
  Modal,
  InputNumber,
  Collapse,
  Tag,
  List,
  Spin
} from 'antd';
import { 
  SendOutlined, 
  UploadOutlined, 
  ApiOutlined,
  FileTextOutlined,
  BarChartOutlined,
  SettingOutlined,
  DownloadOutlined,
  UserOutlined,
  RobotOutlined,
  ExpandAltOutlined,
  CompressOutlined,
  CodeOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  QuestionCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { rasaAPI, toolsAPI } from '../api';
import CustomLoading from '../components/CustomLoading';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Panel } = Collapse;

const Testing = () => {
  const [testText, setTestText] = useState('');
  const [testHistory, setTestHistory] = useState([]);
  const [latestRawResponse, setLatestRawResponse] = useState(null);
  const [testing, setTesting] = useState(false);
  
  // 原始响应弹框状态
  const [rawResponseModalVisible, setRawResponseModalVisible] = useState(false);
  const [currentRawResponse, setCurrentRawResponse] = useState(null);
  
  // 批量测试相关状态
  const [batchModalVisible, setBatchModalVisible] = useState(false);
  const [batchTestData, setBatchTestData] = useState([]);
  const [batchTestResult, setBatchTestResult] = useState(null);
  const [batchTesting, setBatchTesting] = useState(false);
  const [batchTestConfig, setBatchTestConfig] = useState({
    threshold: 0.5,
    confidence_threshold: 0.3
  });

  // 单条测试 - 对话式
  const handleSingleTest = async () => {
    if (!testText.trim()) {
      message.warning('请输入测试文本');
      return;
    }

    setTesting(true);
    const startTime = Date.now(); // 记录开始时间
    
    try {
      const response = await rasaAPI.predict(testText);
      const endTime = Date.now(); // 记录结束时间
      const responseTime = endTime - startTime; // 计算响应时间
      const result = response.data;
      
      // 显示响应时间提醒
      if (responseTime > 3000) {
        message.warning(`响应时间较长: ${responseTime}ms，建议检查模型性能`);
      } else if (responseTime > 1000) {
        message.info(`响应时间: ${responseTime}ms`);
      } else {
        message.success(`响应时间: ${responseTime}ms`);
      }
      
      // 添加到对话历史
      const newMessage = {
        id: Date.now(),
        type: 'user',
        content: testText,
        timestamp: new Date(),
        responseTime: responseTime
      };
      
      // 判断意图识别状态
      const intentName = result.intent?.name;
      const intentConfidence = result.intent?.confidence || 0;
      const isRecognized = intentName && intentName !== 'nlu_fallback' && intentConfidence > 0.3;
      
      const botResponse = {
        id: Date.now() + 1,
        type: 'bot',
        content: {
          text: testText,
          intent: isRecognized ? intentName : '未识别',
          confidence: intentConfidence,
          entities: result.entities || [],
          raw: result,
          responseTime: responseTime,
          isRecognized: isRecognized
        },
        timestamp: new Date()
      };

      setTestHistory(prev => [...prev, newMessage, botResponse]);
      setLatestRawResponse(result);
      setTestText(''); // 清空输入框
    } catch (error) {
      const endTime = Date.now();
      const responseTime = endTime - startTime;
      message.error(`测试失败 (耗时: ${responseTime}ms)`);
      console.error('测试失败:', error);
    } finally {
      setTesting(false);
    }
  };

  // 清空对话历史
  const clearHistory = () => {
    setTestHistory([]);
    setLatestRawResponse(null);
  };

  // 显示原始响应
  const showRawResponse = (rawData) => {
    setCurrentRawResponse(rawData);
    setRawResponseModalVisible(true);
  };

  // 批量测试配置弹窗
  const showBatchTestModal = () => {
    setBatchModalVisible(true);
  };

  // 批量测试
  const handleBatchTest = async () => {
    if (batchTestData.length === 0) {
      message.warning('请先上传测试数据');
      return;
    }

    setBatchTesting(true);
    try {
      const response = await toolsAPI.batchTest({
        test_data: batchTestData,
        ...batchTestConfig
      });
      setBatchTestResult(response.data);
      message.success('批量测试完成');
      setBatchModalVisible(false);
    } catch (error) {
      message.error('批量测试失败');
      console.error('批量测试失败:', error);
    } finally {
      setBatchTesting(false);
    }
  };

  // 处理文件上传
  const handleFileUpload = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target.result;
        let data = [];

        if (file.name.endsWith('.json')) {
          data = JSON.parse(content);
        } else if (file.name.endsWith('.csv')) {
          // 简单的 CSV 解析
          const lines = content.split('\n');
          const headers = lines[0].split(',');
          
          for (let i = 1; i < lines.length; i++) {
            if (lines[i].trim()) {
              const values = lines[i].split(',');
              data.push({
                text: values[0]?.trim(),
                expected_intent: values[1]?.trim()
              });
            }
          }
        }

        setBatchTestData(data);
        message.success(`成功加载 ${data.length} 条测试数据`);
      } catch (error) {
        message.error('文件解析失败');
        console.error('文件解析失败:', error);
      }
    };
    reader.readAsText(file);
    return false; // 阻止自动上传
  };

  // 下载测试模板
  const downloadTemplate = () => {
    const csvContent = "测试文本,期望意图\n查询北京天气,query_weather\n预订机票,book_flight\n";
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = '批量测试模板.csv';
    link.click();
  };

  // 渲染高亮文本（突出显示实体）
  const renderHighlightedText = (text, entities) => {
    if (!entities || entities.length === 0) {
      return text;
    }

    // 按起始位置排序实体
    const sortedEntities = [...entities]
      .filter(entity => entity.start !== undefined && entity.end !== undefined)
      .sort((a, b) => a.start - b.start);

    if (sortedEntities.length === 0) {
      return text;
    }

    const result = [];
    let lastIndex = 0;

    sortedEntities.forEach((entity, index) => {
      // 添加实体前的文本
      if (entity.start > lastIndex) {
        result.push(text.substring(lastIndex, entity.start));
      }

      // 添加高亮的实体
      const entityText = text.substring(entity.start, entity.end);
      const confidence = entity.confidence || entity.confidence_entity || 1;
      const confidencePercent = Math.round(confidence * 100);
      
      result.push(
        <span
          key={`entity-${index}`}
          style={{
            backgroundColor: confidencePercent > 80 ? '#e6f7ff' : 
                           confidencePercent > 60 ? '#fff2e6' : '#fff1f0',
            color: confidencePercent > 80 ? '#1890ff' : 
                   confidencePercent > 60 ? '#fa8c16' : '#ff4d4f',
            padding: '1px 3px',
            borderRadius: 2,
            fontWeight: 600,
            border: `1px solid ${
              confidencePercent > 80 ? '#91d5ff' : 
              confidencePercent > 60 ? '#ffd591' : '#ffccc7'
            }`,
            cursor: 'help'
          }}
          title={`${entity.entity}: ${entity.value} (${confidencePercent}%)`}
        >
          {entityText}
        </span>
      );

      lastIndex = entity.end;
    });

    // 添加最后剩余的文本
    if (lastIndex < text.length) {
      result.push(text.substring(lastIndex));
    }

    return result;
  };

  // 渲染对话消息
  const renderMessage = (message) => {
    if (message.type === 'user') {
      return (
        <div key={message.id} style={{ marginBottom: 12, textAlign: 'right' }}>
          <div style={{ 
            display: 'inline-block', 
            maxWidth: '70%', 
            padding: '8px 12px',
            backgroundColor: '#1890ff',
            color: 'white',
            borderRadius: '16px 16px 4px 16px',
            wordBreak: 'break-word'
          }}>
            <UserOutlined style={{ marginRight: 6 }} />
            {message.content}
          </div>
          <div style={{ 
            textAlign: 'right', 
            fontSize: 11, 
            color: '#999', 
            marginTop: 2 
          }}>
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      );
    } else {
      // Bot消息 - 重新设计布局
      const { content } = message;
      return (
        <div key={message.id} style={{ marginBottom: 12, textAlign: 'left' }}>
          <div style={{ 
            display: 'inline-block', 
            maxWidth: '85%', 
            padding: '10px 14px',
            backgroundColor: '#f5f5f5',
            borderRadius: '16px 16px 16px 4px',
            wordBreak: 'break-word'
          }}>
            {/* 机器人图标和测试文本 */}
            <div style={{ marginBottom: 8 }}>
              <RobotOutlined style={{ 
                color: '#1890ff', 
                marginRight: 6, 
                fontSize: 14 
              }} />
              <span style={{ fontWeight: 500 }}>
                {renderHighlightedText(content.text, content.entities)}
              </span>
            </div>
            
            {/* 识别状态、实体、响应时间一行显示 */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '8px',
              padding: '6px 0',
              borderTop: '1px solid #e8e8e8'
            }}>
              {/* 识别状态 */}
              <div style={{ display: 'flex', alignItems: 'center' }}>
                {content.isRecognized ? (
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 4 }} />
                ) : (
                  <CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: 4 }} />
                )}
                <Tag 
                  color={content.isRecognized ? 'success' : 'error'}
                  style={{ margin: 0, fontSize: 11 }}
                >
                  {content.intent}
                </Tag>
                {content.isRecognized && (
                  <span style={{ 
                    color: '#666', 
                    fontSize: 11, 
                    marginLeft: 4 
                  }}>
                    {Math.round(content.confidence * 100)}%
                  </span>
                )}
              </div>

              <Divider type="vertical" style={{ margin: 0, height: 14 }} />

              {/* 实体情况 */}
              <div style={{ display: 'flex', alignItems: 'center' }}>
                {content.entities && content.entities.length > 0 ? (
                  <>
                    <EyeOutlined style={{ color: '#1890ff', marginRight: 4 }} />
                    <span style={{ fontSize: 11, color: '#666' }}>
                      {content.entities.length}个实体
                    </span>
                  </>
                ) : (
                  <>
                    <QuestionCircleOutlined style={{ color: '#d9d9d9', marginRight: 4 }} />
                    <span style={{ fontSize: 11, color: '#999' }}>无实体</span>
                  </>
                )}
              </div>

              <Divider type="vertical" style={{ margin: 0, height: 14 }} />

              {/* 响应时间 */}
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <ClockCircleOutlined style={{ 
                  color: content.responseTime > 3000 ? '#ff4d4f' : 
                         content.responseTime > 1000 ? '#fa8c16' : '#52c41a',
                  marginRight: 4 
                }} />
                <span style={{ 
                  fontSize: 11, 
                  color: content.responseTime > 3000 ? '#ff4d4f' : 
                         content.responseTime > 1000 ? '#fa8c16' : '#52c41a'
                }}>
                  {content.responseTime}ms
                </span>
              </div>

              <Divider type="vertical" style={{ margin: 0, height: 14 }} />

              {/* 原始响应按钮 */}
              <Button
                type="text"
                size="small"
                icon={<CodeOutlined />}
                onClick={() => showRawResponse(content.raw)}
                style={{
                  padding: '0 4px',
                  height: 18,
                  fontSize: 11,
                  color: '#666'
                }}
              >
                原始响应
              </Button>
            </div>

            {/* 实体详情展示 */}
            {content.entities && content.entities.length > 0 && (
              <Collapse
                ghost
                size="small"
                style={{ marginTop: 8 }}
                items={[{
                  key: 'entities',
                  label: (
                    <span style={{ fontSize: 11, color: '#666' }}>
                      <EyeOutlined style={{ marginRight: 4 }} />
                      实体详情 ({content.entities.length})
                    </span>
                  ),
                  children: (
                    <div style={{ paddingLeft: 8 }}>
                      {content.entities.map((entity, index) => {
                        const confidence = entity.confidence || entity.confidence_entity || 1;
                        const confidencePercent = Math.round(confidence * 100);
                        return (
                          <Tag
                            key={index}
                            style={{
                              marginBottom: 4,
                              padding: '2px 8px',
                              fontSize: 11,
                              borderRadius: 4
                            }}
                            color={confidencePercent > 80 ? 'blue' : 
                                   confidencePercent > 60 ? 'orange' : 'red'}
                          >
                            <strong>{entity.entity}:</strong> {entity.value} 
                            <span style={{ opacity: 0.8 }}>
                              ({confidencePercent}%)
                            </span>
                          </Tag>
                        );
                      })}
                    </div>
                  )
                }]}
              />
            )}
          </div>
          
          <div style={{ 
            textAlign: 'left', 
            fontSize: 11, 
            color: '#999', 
            marginTop: 2 
          }}>
            {message.timestamp.toLocaleTimeString()}
          </div>
        </div>
      );
    }
  };

  // 渲染批量测试结果
  const renderBatchTestResult = () => {
    if (!batchTestResult) return null;

    const { total_tests, correct_predictions, accuracy, results } = batchTestResult;

    const resultColumns = [
      {
        title: '测试文本',
        dataIndex: 'text',
        key: 'text',
        ellipsis: true,
      },
      {
        title: '期望意图',
        dataIndex: 'expected_intent',
        key: 'expected_intent',
        render: (text) => <Tag color="blue">{text}</Tag>
      },
      {
        title: '识别意图',
        dataIndex: 'predicted_intent',
        key: 'predicted_intent',
        render: (text) => <Tag color="green">{text}</Tag>
      },
      {
        title: '置信度',
        dataIndex: 'confidence',
        key: 'confidence',
        render: (confidence) => (
          <Progress 
            percent={Math.round((confidence || 0) * 100)} 
            size="small"
            status={confidence > 0.7 ? 'success' : confidence > 0.4 ? 'normal' : 'exception'}
          />
        )
      },
      {
        title: '结果',
        dataIndex: 'is_correct',
        key: 'is_correct',
        render: (isCorrect) => (
          <Tag color={isCorrect ? 'success' : 'error'}>
            {isCorrect ? '正确' : '错误'}
          </Tag>
        )
      }
    ];

    return (
      <Card title="批量测试结果" style={{ marginTop: 24 }}>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
                  {total_tests}
                </div>
                <div>总测试数</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
                  {correct_predictions}
                </div>
                <div>正确预测</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: '#fa8c16' }}>
                  {Math.round(accuracy * 100)}%
                </div>
                <div>准确率</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 'bold', color: '#722ed1' }}>
                  {total_tests - correct_predictions}
                </div>
                <div>错误预测</div>
              </div>
            </Card>
          </Col>
        </Row>

        <Table
          columns={resultColumns}
          dataSource={results}
          rowKey={(record, index) => index}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>
    );
  };

  return (
    <div>
      <Tabs defaultActiveKey="single">
        <TabPane 
          tab={
            <span>
              <ApiOutlined />
              单条测试
            </span>
          } 
          key="single"
        >
          <Row gutter={24} style={{ height: 'calc(100vh - 200px)' }}>
            {/* 左侧对话区 */}
            <Col span={16}>
              <Card 
                title="语义理解测试" 
                style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                extra={
                  <Button size="small" onClick={clearHistory}>
                    清空对话
                  </Button>
                }
              >
                <div style={{ 
                  flex: 1, 
                  overflowY: 'auto', 
                  padding: '0 16px',
                  marginBottom: 16,
                  border: '1px solid #f0f0f0',
                  borderRadius: 6,
                  backgroundColor: '#fafafa'
                }}>
                  {testHistory.length === 0 ? (
                    <div style={{ 
                      textAlign: 'center', 
                      padding: 40, 
                      color: '#999' 
                    }}>
                      开始测试对话吧！输入文本查看AI理解结果
                    </div>
                  ) : (
                    testHistory.map(renderMessage)
                  )}
                </div>
                
                <div style={{ display: 'flex', gap: 8 }}>
                  <Input
                    value={testText}
                    onChange={(e) => setTestText(e.target.value)}
                    placeholder="输入要测试的文本..."
                    onPressEnter={handleSingleTest}
                    disabled={testing}
                  />
                  <Button 
                    type="primary" 
                    icon={<SendOutlined />}
                    onClick={handleSingleTest}
                    loading={testing}
                  >
                    发送
                  </Button>
                </div>
              </Card>
            </Col>

            {/* 右侧原始响应 */}
            <Col span={8}>
              <Card 
                title="原始响应" 
                style={{ height: '100%' }}
                extra={
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    最新测试结果
                  </Text>
                }
              >
                {latestRawResponse ? (
                  <div>
                    <div style={{ marginBottom: 16 }}>
                      <Text strong>置信度最高的前两条：</Text>
                    </div>
                    
                    {/* 显示前两个最高置信度的意图 */}
                    {latestRawResponse.intent_ranking && latestRawResponse.intent_ranking.slice(0, 2).map((intent, index) => (
                      <div key={index} style={{ 
                        marginBottom: 12, 
                        padding: 12,
                        border: '1px solid #f0f0f0',
                        borderRadius: 6,
                        backgroundColor: index === 0 ? '#f6ffed' : '#fafafa'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Text strong>{intent.name}</Text>
                          <Tag color={index === 0 ? 'green' : 'default'}>
                            {Math.round(intent.confidence * 100)}%
                          </Tag>
                        </div>
                      </div>
                    ))}

                    <Divider />
                    
                    <Collapse size="small" defaultActiveKey={[]}>
                      <Panel header="完整原始响应" key="full">
                        <pre style={{ 
                          fontSize: 11,
                          backgroundColor: '#fafafa',
                          padding: 12,
                          borderRadius: 4,
                          maxHeight: 400,
                          overflow: 'auto'
                        }}>
                          {JSON.stringify(latestRawResponse, null, 2)}
                        </pre>
                      </Panel>
                    </Collapse>
                  </div>
                ) : (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: 40, 
                    color: '#999' 
                  }}>
                    <ApiOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                    <div>进行测试后，这里将显示详细的响应信息</div>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane 
          tab={
            <span>
              <BarChartOutlined />
              批量测试
            </span>
          } 
          key="batch"
        >
          <Card>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Title level={4} style={{ margin: 0 }}>批量测试</Title>
              <Button 
                type="primary" 
                icon={<SettingOutlined />}
                onClick={showBatchTestModal}
                size="large"
              >
                开始批量测试
              </Button>
            </div>

            {batchTestData.length > 0 && (
              <Alert
                message={`已加载 ${batchTestData.length} 条测试数据`}
                type="success"
                style={{ marginBottom: 16 }}
                showIcon
              />
            )}

            {renderBatchTestResult()}
          </Card>
        </TabPane>
      </Tabs>

      {/* 批量测试配置弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <SettingOutlined style={{ color: '#1890ff' }} />
            <span style={{ fontSize: 18, fontWeight: 600 }}>批量测试配置</span>
          </div>
        }
        open={batchModalVisible}
        onCancel={() => setBatchModalVisible(false)}
        footer={null}
        width={800}
        centered
      >
        <div style={{ padding: '20px 0' }}>
          <Form
            layout="vertical"
            initialValues={batchTestConfig}
            onFinish={(values) => {
              setBatchTestConfig(values);
              handleBatchTest();
            }}
          >
            {/* 测试配置区域 */}
            <div style={{ 
              backgroundColor: '#f8f9fa', 
              padding: 20, 
              borderRadius: 12, 
              marginBottom: 24,
              border: '1px solid #e9ecef'
            }}>
              <Title level={5} style={{ marginBottom: 16, color: '#495057' }}>
                测试参数配置
              </Title>
              
              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name="threshold"
                    label="意图识别阈值"
                    help="低于此值的预测将被视为无效"
                  >
                    <InputNumber
                      min={0}
                      max={1}
                      step={0.1}
                      style={{ width: '100%' }}
                      formatter={value => `${value}`}
                      parser={value => value.replace('%', '')}
                      size="large"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="confidence_threshold"
                    label="置信度阈值"
                    help="用于判断预测质量的阈值"
                  >
                    <InputNumber
                      min={0}
                      max={1}
                      step={0.1}
                      style={{ width: '100%' }}
                      size="large"
                    />
                  </Form.Item>
                </Col>
              </Row>
            </div>

            {/* 数据上传区域 */}
            <div style={{ 
              backgroundColor: '#f0f8ff', 
              padding: 20, 
              borderRadius: 12, 
              marginBottom: 24,
              border: '1px solid #91d5ff'
            }}>
              <Title level={5} style={{ marginBottom: 16, color: '#1890ff' }}>
                测试数据上传
              </Title>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
                <Upload
                  accept=".csv,.json"
                  beforeUpload={handleFileUpload}
                  showUploadList={false}
                >
                  <Button 
                    icon={<UploadOutlined />}
                    size="large"
                    style={{
                      height: 60,
                      width: 200,
                      borderRadius: 8,
                      fontSize: 16,
                      fontWeight: 600,
                      background: 'linear-gradient(45deg, #40a9ff 0%, #1890ff 100%)',
                      border: 'none',
                      color: 'white',
                      boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)'
                    }}
                  >
                    选择测试文件
                  </Button>
                </Upload>
                
                <Button 
                  icon={<DownloadOutlined />}
                  onClick={downloadTemplate}
                  style={{
                    height: 48,
                    borderRadius: 6,
                    color: '#1890ff',
                    borderColor: '#1890ff'
                  }}
                >
                  下载模板
                </Button>
              </div>

              <Text type="secondary" style={{ fontSize: 13 }}>
                支持 CSV 和 JSON 格式，CSV 格式要求：测试文本,期望意图
              </Text>

              {batchTestData.length > 0 && (
                <Alert
                  message={`已成功加载 ${batchTestData.length} 条测试数据`}
                  type="success"
                  style={{ marginTop: 16 }}
                  showIcon
                />
              )}
            </div>

            {/* 操作按钮区域 */}
            <div style={{ textAlign: 'right', paddingTop: 16 }}>
              <Space size="large">
                <Button 
                  size="large"
                  onClick={() => setBatchModalVisible(false)}
                  style={{ 
                    borderRadius: 8,
                    padding: '8px 24px',
                    height: 48
                  }}
                >
                  取消
                </Button>
                <Button 
                  type="primary" 
                  htmlType="submit"
                  loading={batchTesting}
                  disabled={batchTestData.length === 0}
                  size="large"
                  style={{ 
                    borderRadius: 8,
                    padding: '8px 32px',
                    height: 48,
                    fontSize: 16,
                    fontWeight: 600
                  }}
                >
                  开始批量测试
                </Button>
              </Space>
            </div>
          </Form>
        </div>
      </Modal>

      {/* 原始响应弹框 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <CodeOutlined style={{ color: '#1890ff' }} />
            <span style={{ fontSize: 16, fontWeight: 600 }}>原始响应数据</span>
          </div>
        }
        open={rawResponseModalVisible}
        onCancel={() => setRawResponseModalVisible(false)}
        footer={[
          <Button 
            key="close" 
            onClick={() => setRawResponseModalVisible(false)}
            style={{ borderRadius: 6 }}
          >
            关闭
          </Button>
        ]}
        width={800}
        centered
        maskClosable={true}
      >
        <div style={{ 
          maxHeight: 500, 
          overflow: 'auto',
          backgroundColor: '#f6f8fa',
          border: '1px solid #d0d7de',
          borderRadius: 8,
          padding: 16
        }}>
          <pre style={{ 
            margin: 0,
            fontSize: 12,
            lineHeight: 1.5,
            color: '#24292f',
            fontFamily: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word'
          }}>
            {currentRawResponse ? JSON.stringify(currentRawResponse, null, 2) : '暂无数据'}
          </pre>
        </div>
      </Modal>

      {/* 批量测试loading */}
      <CustomLoading 
        visible={batchTesting} 
        text="正在进行批量测试" 
        description="正在处理测试数据，请稍候..."
        size="large"
      />
    </div>
  );
};

export default Testing;

