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
  Col
} from 'antd';
import { 
  SendOutlined, 
  UploadOutlined, 
  ApiOutlined,
  FileTextOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { rasaAPI, toolsAPI } from '../api';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

const Testing = () => {
  const [testText, setTestText] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [batchTestData, setBatchTestData] = useState([]);
  const [batchTestResult, setBatchTestResult] = useState(null);
  const [batchTesting, setBatchTesting] = useState(false);

  // 单条测试
  const handleSingleTest = async () => {
    if (!testText.trim()) {
      message.warning('请输入测试文本');
      return;
    }

    setTesting(true);
    try {
      const response = await rasaAPI.predict(testText);
      setTestResult(response.data);
    } catch (error) {
      message.error('测试失败');
      console.error('测试失败:', error);
    } finally {
      setTesting(false);
    }
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
        test_data: batchTestData
      });
      setBatchTestResult(response.data);
      message.success('批量测试完成');
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

  // 渲染单条测试结果
  const renderSingleTestResult = () => {
    if (!testResult) return null;

    const { intent, confidence, entities } = testResult;
    const confidencePercent = Math.round((confidence || 0) * 100);

    return (
      <Card title="测试结果" style={{ marginTop: 16 }}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <div className="test-result">
              <div className="result-text">
                <Text strong>输入文本:</Text> {testResult.text}
              </div>
            </div>
          </Col>
          
          <Col span={12}>
            <Card size="small" title="意图识别">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>识别意图:</Text> 
                  <Text style={{ marginLeft: 8, fontSize: 16 }}>
                    {intent || '未识别'}
                  </Text>
                </div>
                <div>
                  <Text strong>置信度:</Text>
                  <Progress 
                    percent={confidencePercent} 
                    size="small"
                    status={confidencePercent > 70 ? 'success' : confidencePercent > 40 ? 'normal' : 'exception'}
                    style={{ marginLeft: 8, width: 200 }}
                  />
                </div>
              </Space>
            </Card>
          </Col>

          <Col span={12}>
            <Card size="small" title="实体提取">
              {entities && entities.length > 0 ? (
                <div>
                  {entities.map((entity, index) => (
                    <div key={index} style={{ marginBottom: 8 }}>
                      <Text strong>{entity.entity}:</Text> {entity.value}
                    </div>
                  ))}
                </div>
              ) : (
                <Text type="secondary">未提取到实体</Text>
              )}
            </Card>
          </Col>

          <Col span={24}>
            <Card size="small" title="原始响应">
              <div className="code-block">
                <pre>{JSON.stringify(testResult.raw_rasa_response, null, 2)}</pre>
              </div>
            </Card>
          </Col>
        </Row>
      </Card>
    );
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
      },
      {
        title: '预测意图',
        dataIndex: 'predicted_intent',
        key: 'predicted_intent',
      },
      {
        title: '置信度',
        dataIndex: 'confidence',
        key: 'confidence',
        render: (confidence) => `${Math.round((confidence || 0) * 100)}%`,
      },
      {
        title: '结果',
        dataIndex: 'is_correct',
        key: 'is_correct',
        render: (isCorrect) => (
          <Text type={isCorrect ? 'success' : 'danger'}>
            {isCorrect ? '✓ 正确' : '✗ 错误'}
          </Text>
        ),
      },
    ];

    return (
      <div style={{ marginTop: 16 }}>
        <Card title="批量测试结果">
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
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
                    {total_tests - correct_predictions}
                  </div>
                  <div>错误预测</div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 'bold', color: '#722ed1' }}>
                    {Math.round(accuracy * 100)}%
                  </div>
                  <div>准确率</div>
                </div>
              </Card>
            </Col>
          </Row>

          <Progress 
            percent={Math.round(accuracy * 100)} 
            strokeColor={{
              '0%': '#ff4d4f',
              '50%': '#fa8c16',
              '100%': '#52c41a',
            }}
            style={{ marginBottom: 16 }}
          />

          <Table
            columns={resultColumns}
            dataSource={results}
            rowKey={(record, index) => index}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `共 ${total} 条测试结果`,
            }}
            rowClassName={(record) => record.is_correct ? '' : 'error-row'}
          />
        </Card>
      </div>
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
          <Card title="语义理解测试">
            <Paragraph>
              输入任意文本，测试当前模型的意图识别和实体提取能力。
            </Paragraph>

            <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
              <TextArea
                value={testText}
                onChange={(e) => setTestText(e.target.value)}
                placeholder="请输入要测试的文本，例如：你好、我想订机票、查询天气等"
                rows={3}
                style={{ flex: 1 }}
              />
              <Button 
                type="primary"
                icon={<SendOutlined />}
                onClick={handleSingleTest}
                loading={testing}
                style={{ height: 'auto' }}
              >
                测试
              </Button>
            </Space.Compact>

            {/* 快速测试示例 */}
            <div style={{ marginBottom: 16 }}>
              <Text strong>快速测试:</Text>
              <Space wrap style={{ marginLeft: 8 }}>
                {[
                  '你好',
                  '我想预订航班',
                  '取消我的预订',
                  '今天天气怎么样',
                  '帮助'
                ].map(text => (
                  <Button 
                    key={text}
                    size="small"
                    onClick={() => setTestText(text)}
                  >
                    {text}
                  </Button>
                ))}
              </Space>
            </div>

            {renderSingleTestResult()}
          </Card>
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
          <Card title="批量性能测试">
            <Paragraph>
              上传测试数据集，批量评估模型性能。支持 JSON 和 CSV 格式。
            </Paragraph>

            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card size="small" title="上传测试数据">
                  <Upload
                    beforeUpload={handleFileUpload}
                    accept=".json,.csv"
                    showUploadList={false}
                  >
                    <Button icon={<UploadOutlined />}>
                      选择文件
                    </Button>
                  </Upload>
                  
                  <div style={{ marginTop: 16 }}>
                    <Text strong>已加载数据:</Text> {batchTestData.length} 条
                  </div>

                  {batchTestData.length > 0 && (
                    <Button 
                      type="primary"
                      onClick={handleBatchTest}
                      loading={batchTesting}
                      style={{ marginTop: 16 }}
                    >
                      开始批量测试
                    </Button>
                  )}
                </Card>
              </Col>

              <Col span={12}>
                <Card size="small" title="数据格式说明">
                  <div>
                    <Text strong>JSON 格式:</Text>
                    <div className="code-block" style={{ marginTop: 8 }}>
                      <pre>{`[
  {
    "text": "你好",
    "expected_intent": "greet"
  },
  {
    "text": "我想订机票",
    "expected_intent": "book_flight"
  }
]`}</pre>
                    </div>
                  </div>
                  
                  <Divider />
                  
                  <div>
                    <Text strong>CSV 格式:</Text>
                    <div className="code-block" style={{ marginTop: 8 }}>
                      <pre>{`text,expected_intent
你好,greet
我想订机票,book_flight`}</pre>
                    </div>
                  </div>
                </Card>
              </Col>
            </Row>

            {renderBatchTestResult()}
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default Testing;

