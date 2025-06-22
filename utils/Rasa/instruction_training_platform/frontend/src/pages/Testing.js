import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
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
  PlusCircleOutlined,
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
  ClockCircleOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { rasaAPI, toolsAPI } from '../api';
import CustomLoading from '../components/CustomLoading';
import { formatLocalTime, generateDefaultTestName } from '../utils/timeUtils';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const Testing = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const [testText, setTestText] = useState('');
  const [testHistory, setTestHistory] = useState([]);
  const [latestRawResponse, setLatestRawResponse] = useState(null);
  const [testing, setTesting] = useState(false);
  
  // Tab 状态管理
  const [activeTab, setActiveTab] = useState('single');
  
  // 全局配置
  const [globalConfig, setGlobalConfig] = useState({
    confidenceThreshold: 0.80 // 置信度阈值
  });
  
  // 原始响应弹框状态
  const [rawResponseModalVisible, setRawResponseModalVisible] = useState(false);
  const [currentRawResponse, setCurrentRawResponse] = useState(null);
  
  // 批量测试相关状态
  const [batchModalVisible, setBatchModalVisible] = useState(false);
  const [batchTestData, setBatchTestData] = useState([]);
  const [batchTesting, setBatchTesting] = useState(false);
  
  // 批量测试历史记录状态
  const [batchHistoryLoading, setBatchHistoryLoading] = useState(false);
  const [batchHistoryList, setBatchHistoryList] = useState([]);
  const [batchHistoryTotal, setBatchHistoryTotal] = useState(0);
  const [batchHistoryPagination, setBatchHistoryPagination] = useState({
    current: 1,
    pageSize: 10
  });
  
  // 批量测试详情状态 (已移至单独页面，保留用于其他功能)
  const [currentBatchRecord, setCurrentBatchRecord] = useState(null);
  const [batchTestResult, setBatchTestResult] = useState(null);
  
  // 测试结果详情弹窗状态 (成功识别/识别失败详情)
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [detailType, setDetailType] = useState(''); // 'recognized' 或 'unrecognized'
  const [detailData, setDetailData] = useState([]);
  
  // 批量测试结果分页状态
  const [batchPagination, setBatchPagination] = useState({
    current: 1,
    pageSize: 20
  });

  // 组件初始化时加载批量测试历史记录
  useEffect(() => {
    loadBatchTestHistory();
  }, []);

  // 检测从详情页面返回时的导航状态
  useEffect(() => {
    if (location.state?.activeTab) {
      setActiveTab(location.state.activeTab);
      // 清除location state，避免页面刷新时保持该状态
      navigate(location.pathname, { replace: true });
    }
  }, [location.state, navigate, location.pathname]);

  // 加载批量测试历史记录
  const loadBatchTestHistory = async (page = 1, pageSize = 10) => {
    setBatchHistoryLoading(true);
    try {
      const response = await toolsAPI.getBatchTestRecords({
        skip: (page - 1) * pageSize,
        limit: pageSize
      });
      
      setBatchHistoryList(response.data.records);
      setBatchHistoryTotal(response.data.total);
      setBatchHistoryPagination(prev => ({
        ...prev,
        current: page,
        pageSize: pageSize
      }));
    } catch (error) {
      console.error('加载批量测试历史记录失败:', error);
      message.error('加载历史记录失败');
    } finally {
      setBatchHistoryLoading(false);
    }
  };

  // 查看批量测试详情 - 跳转到新页面
  const viewBatchTestDetail = (record) => {
    navigate(`/testing/batch-detail/${record.id}`);
  };

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
      
      // 使用全局阈值判断意图识别状态
      const intentName = result.intent?.name || result.intent;
      const intentConfidence = result.intent?.confidence || result.confidence || 0;
      const isRecognized = intentName && 
                          intentName !== 'nlu_fallback' && 
                          intentName !== 'out_of_scope' && 
                          intentName.trim() !== '' &&
                          intentConfidence >= globalConfig.confidenceThreshold;
      
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
    // 设置表单初始值为当前全局配置
    batchTestForm.setFieldsValue({
      confidenceThreshold: globalConfig.confidenceThreshold
    });
    setBatchModalVisible(true);
  };

  // 批量测试表单处理
  const [batchTestForm] = Form.useForm();

  // 批量测试 - 带配置版本
  const handleBatchTest = async (values) => {
    if (batchTestData.length === 0) {
      message.warning('请先上传测试数据');
      return;
    }

    setBatchTesting(true);
    try {
      const confidenceThreshold = values.confidenceThreshold || globalConfig.confidenceThreshold;
      let testName = values.testName?.trim();
      
      // 如果没有提供测试名称，生成默认名称
      if (!testName) {
        // 获取当前的测试数量来生成序号
        const testCount = batchHistoryTotal + 1;
        testName = generateDefaultTestName(testCount);
      }
      
      const response = await toolsAPI.batchTest({
        test_data: batchTestData,
        confidence_threshold: confidenceThreshold,
        test_name: testName
      });
      
      message.success(`批量测试完成！共测试 ${batchTestData.length} 条数据，结果已保存到数据库`);
      setBatchModalVisible(false);
      
      // 重新加载历史记录列表
      loadBatchTestHistory();
      
      // 清空当前测试数据
      setBatchTestData([]);
      
      // 重置表单
      batchTestForm.resetFields();
    } catch (error) {
      message.error('批量测试失败');
      console.error('批量测试失败:', error);
    } finally {
      setBatchTesting(false);
    }
  };

  // 处理文件上传 - 简化版，只需要测试文本
  const handleFileUpload = async (file) => {
    // 检查文件类型
    const allowedTypes = ['.csv', '.txt', '.json'];
    const fileName = file.name.toLowerCase();
    const isValidType = allowedTypes.some(type => fileName.endsWith(type));
    
    if (!isValidType) {
      message.error('不支持的文件格式，请上传 CSV(.csv)、文本(.txt) 或 JSON(.json) 文件');
      return false;
    }

    // 检查文件大小 (限制5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      message.error('文件大小不能超过5MB');
      return false;
    }

    try {
      message.loading('正在上传和解析文件...', 0);
      
      // 创建FormData对象
      const formData = new FormData();
      formData.append('file', file);
      
      // 调用后端接口上传文件
      const response = await toolsAPI.uploadBatchTestFile(formData);
      
      message.destroy(); // 关闭loading
      
      if (response.data && response.data.test_data) {
        setBatchTestData(response.data.test_data);
        message.success(`文件上传成功！解析到 ${response.data.test_data.length} 条测试数据`);
      } else {
        message.warning('文件上传成功，但未找到有效的测试数据');
      }
      
    } catch (error) {
      message.destroy(); // 关闭loading
      console.error('文件上传失败:', error);
      
      if (error.response && error.response.data && error.response.data.detail) {
        message.error(`文件处理失败: ${error.response.data.detail}`);
      } else {
        message.error('文件上传失败，请检查文件格式和网络连接');
      }
    }
    
    return false; // 阻止Antd的默认上传行为
  };

  // 下载测试模板 - 简化版，只有测试文本
  const downloadTemplate = () => {
    const testData = [
      '查询北京天气',
      '预订机票到上海', 
      '调整屏幕亮度',
      '播放音乐',
      '关闭客厅灯光',
      '设置明天早上7点闹钟',
      '查询当前时间',
      '打开空调制冷模式',
      '切换到CCTV1频道'
    ];

    const csvContent = '测试文本\n' + testData.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = '批量测试模板.csv';
    link.click();
    
    message.success('已下载CSV格式模板文件');
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



  // 渲染批量测试历史记录列表
  const renderBatchTestHistory = () => {
    const columns = [
      {
        title: '序号',
        key: 'index',
        width: 60,
        render: (text, record, index) => 
          (batchHistoryPagination.current - 1) * batchHistoryPagination.pageSize + index + 1,
      },
      {
        title: '测试时间',
        dataIndex: 'created_at',
        key: 'created_at',
        width: '20%',
        render: (text) => formatLocalTime(text)
      },
      {
        title: '总测试数',
        dataIndex: 'total_tests',
        key: 'total_tests',
        width: '12%',
        render: (text) => (
          <Tag color="blue" style={{ fontWeight: 600 }}>
            {text} 条
          </Tag>
        )
      },
      {
        title: '成功识别',
        dataIndex: 'recognized_count',
        key: 'recognized_count',
        width: '12%',
        render: (text) => (
          <Tag color="success" style={{ fontWeight: 600 }}>
            {text} 条
          </Tag>
        )
      },
      {
        title: '识别失败',
        key: 'failed_count',
        width: '12%',
        render: (text, record) => {
          const failedCount = record.total_tests - record.recognized_count;
          return (
            <Tag color="error" style={{ fontWeight: 600 }}>
              {failedCount} 条
            </Tag>
          );
        }
      },
      {
        title: '识别率',
        dataIndex: 'recognition_rate',
        key: 'recognition_rate',
        width: '12%',
        render: (rate) => {
          const color = rate >= 80 ? '#52c41a' : rate >= 60 ? '#fa8c16' : '#ff4d4f';
          return (
            <span style={{ 
              color: color, 
              fontWeight: 600,
              fontSize: 14
            }}>
              {rate?.toFixed(1)}%
            </span>
          );
        }
      },
      {
        title: '置信度阈值',
        dataIndex: 'confidence_threshold',
        key: 'confidence_threshold',
        width: '15%',
        render: (threshold) => (
          <Tag color="processing">
            {threshold.toFixed(2)}
          </Tag>
        )
      },
      {
        title: '操作',
        key: 'action',
        width: '17%',
        render: (text, record) => (
          <Space size="small">
            <Button
              type="primary"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => viewBatchTestDetail(record)}
            >
              查看详情
            </Button>
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => {
                Modal.confirm({
                  title: '确认删除',
                  content: '确定要删除这条测试记录吗？删除后无法恢复。',
                  okText: '确定',
                  cancelText: '取消',
                  onOk: () => deleteBatchRecord(record.id),
                });
              }}
            />
          </Space>
        ),
      },
    ];

    return (
      <div style={{ height: '100%' }}>
        <Card 
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <BarChartOutlined style={{ color: '#1890ff' }} />
              <span>批量测试历史记录</span>
              <Tag color="blue">{batchHistoryTotal} 条记录</Tag>
            </div>
          }
          extra={
            <div 
              onClick={showBatchTestModal}
              style={{
                cursor: 'pointer',
                padding: '8px 12px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.3s ease',
                boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
                minWidth: '48px',
                minHeight: '48px'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.6)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0px)';
                e.target.style.boxShadow = '0 4px 15px rgba(102, 126, 234, 0.4)';
              }}
              title="开始新的批量测试"
            >
              <PlusCircleOutlined 
                style={{ 
                  color: 'white', 
                  fontSize: '20px',
                  filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))'
                }} 
              />
            </div>
          }
          style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
          styles={{ body: { flex: 1, padding: '16px 24px' } }}
        >
          {batchHistoryList.length === 0 && !batchHistoryLoading ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '80px 40px', 
              color: '#999',
              minHeight: '400px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <BarChartOutlined style={{ fontSize: 64, marginBottom: 24, color: '#d9d9d9' }} />
              <div style={{ fontSize: 18, marginBottom: 12, color: '#666' }}>
                暂无批量测试记录
              </div>
              <div style={{ fontSize: 14, color: '#999', marginBottom: 24 }}>
                点击"开始新测试"按钮进行首次批量测试
              </div>
              <div 
                onClick={showBatchTestModal}
                style={{
                  cursor: 'pointer',
                  padding: '12px 24px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 6px 25px rgba(102, 126, 234, 0.4)',
                  color: 'white',
                  fontSize: '16px',
                  fontWeight: '600',
                  gap: '8px'
                }}
                onMouseEnter={(e) => {
                  e.target.style.transform = 'translateY(-3px)';
                  e.target.style.boxShadow = '0 8px 30px rgba(102, 126, 234, 0.6)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0px)';
                  e.target.style.boxShadow = '0 6px 25px rgba(102, 126, 234, 0.4)';
                }}
              >
                <PlusCircleOutlined style={{ fontSize: '18px' }} />
                开始新测试
              </div>
            </div>
          ) : (
            <Table
              columns={columns}
              dataSource={batchHistoryList}
              rowKey="id"
              loading={batchHistoryLoading}
              pagination={{
                current: batchHistoryPagination.current,
                pageSize: batchHistoryPagination.pageSize,
                total: batchHistoryTotal,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`,
                onChange: (page, pageSize) => {
                  loadBatchTestHistory(page, pageSize);
                },
                onShowSizeChange: (current, size) => {
                  loadBatchTestHistory(1, size);
                }
              }}
              scroll={{ 
                y: 'calc(100vh - 400px)',
                scrollToFirstRowOnChange: true 
              }}
              className="hide-scrollbar"
            />
          )}
        </Card>
      </div>
    );
  };

  // 显示详情弹窗 (成功识别/识别失败详情)
  const showDetailModal = (type, results) => {
    let filteredData = [];
    
    if (type === 'recognized') {
      // 过滤出成功识别的数据
      filteredData = results.filter(item => 
        item.predicted_intent && 
        item.predicted_intent !== 'nlu_fallback' && 
        item.predicted_intent !== 'out_of_scope' &&
        (item.confidence || 0) >= (globalConfig.confidenceThreshold || 0.80)
      );
    } else if (type === 'unrecognized') {
      // 过滤出未识别的数据
      filteredData = results.filter(item => 
        !item.predicted_intent || 
        item.predicted_intent === 'nlu_fallback' || 
        item.predicted_intent === 'out_of_scope' ||
        (item.confidence || 0) < (globalConfig.confidenceThreshold || 0.80)
      );
    }
    
    setDetailType(type);
    setDetailData(filteredData);
    setDetailModalVisible(true);
  };

  // 删除批量测试记录
  const deleteBatchRecord = async (recordId) => {
    try {
      await toolsAPI.deleteBatchTestRecord(recordId);
      message.success('测试记录删除成功');
      // 重新加载历史记录列表
      loadBatchTestHistory(batchHistoryPagination.current, batchHistoryPagination.pageSize);
    } catch (error) {
      console.error('删除测试记录失败:', error);
      message.error('删除记录失败');
    }
  };

  return (
    <div>
      <Tabs 
        activeKey={activeTab}
        onChange={(key) => setActiveTab(key)}
        items={[
          {
            key: 'single',
            label: (
              <span>
                <ApiOutlined />
                单条测试
              </span>
            ),
            children: (
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
            )
          },
          {
            key: 'batch',
            label: (
              <span>
                <BarChartOutlined />
                批量测试
              </span>
            ),
            children: (
              <div style={{ height: 'calc(100vh - 280px)' }}>
                {renderBatchTestHistory()}
              </div>
            )
          }
        ]}
      />

      {/* 批量测试配置弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <SettingOutlined style={{ color: '#1890ff' }} />
            <span style={{ fontSize: 18, fontWeight: 600 }}>批量测试配置</span>
          </div>
        }
        open={batchModalVisible}
        onCancel={() => {
          setBatchModalVisible(false);
          batchTestForm.resetFields();
        }}
        footer={null}
        width={800}
        centered
      >
        <div style={{ padding: '20px 0' }}>
          <Form
            form={batchTestForm}
            layout="vertical"
            onFinish={handleBatchTest}
            initialValues={{
              confidenceThreshold: globalConfig.confidenceThreshold
            }}
          >
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
                  accept=".csv,.txt,.json"
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

              <Text type="secondary" style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
                支持 CSV、TXT 和 JSON 格式。CSV/TXT：每行一个测试文本；JSON：["文本1", "文本2"] 格式
              </Text>
              <Text type="secondary" style={{ fontSize: 12, color: '#fa8c16' }}>
                💡 提示：只需要上传测试文本，系统会自动识别意图并显示结果
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

            {/* 测试参数配置区域 */}
            <div style={{ 
              backgroundColor: '#f9f9f9', 
              padding: 20, 
              borderRadius: 12, 
              marginBottom: 24,
              border: '1px solid #e8e8e8'
            }}>
              <Title level={5} style={{ marginBottom: 16, color: '#595959' }}>
                测试参数配置
              </Title>
              
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item
                    name="testName"
                    label={
                      <span style={{ fontWeight: 500 }}>
                        测试名称
                        <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                          (可选，留空将自动生成)
                        </Text>
                      </span>
                    }
                  >
                    <Input
                      placeholder={`如留空将自动生成，例如：${generateDefaultTestName(1)}`}
                      style={{ width: '100%' }}
                      maxLength={50}
                      showCount
                    />
                  </Form.Item>
                </Col>
              </Row>
              
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="confidenceThreshold"
                    label={
                      <span style={{ fontWeight: 500 }}>
                        置信度阈值
                        <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                          (用于判断意图识别成功的最低置信度)
                        </Text>
                      </span>
                    }
                                         rules={[
                       { required: true, message: '请设置置信度阈值' },
                       { 
                         type: 'number', 
                         min: 0.10, 
                         max: 1.00, 
                         message: '置信度阈值范围为 0.10 - 1.00' 
                       }
                     ]}
                  >
                    <InputNumber
                      min={0.10}
                      max={1.00}
                      step={0.01}
                      precision={2}
                      style={{ width: '100%' }}
                      placeholder="请输入置信度阈值 (如: 0.85)"
                      addonAfter="(0.10-1.00)"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <div style={{ 
                    marginTop: 30, 
                    padding: 12, 
                    backgroundColor: '#e6f7ff', 
                    borderRadius: 6,
                    border: '1px solid #91d5ff'
                  }}>
                                         <Text type="secondary" style={{ fontSize: 12, lineHeight: 1.5 }}>
                       <strong>说明：</strong><br/>
                       • 阈值越高，识别越严格<br/>
                       • 建议范围：0.60 - 0.90<br/>
                       • 默认值：0.80<br/>
                       • 精度：0.01 (可精确到百分位)
                     </Text>
                  </div>
                </Col>
              </Row>
            </div>

            {/* 操作按钮区域 */}
            <div style={{ textAlign: 'right', paddingTop: 16 }}>
              <Space size="large">
                <Button 
                  size="large"
                  onClick={() => {
                    setBatchModalVisible(false);
                    batchTestForm.resetFields();
                  }}
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

      {/* 详情弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <EyeOutlined style={{ color: detailType === 'recognized' ? '#52c41a' : '#ff4d4f' }} />
            <span style={{ fontSize: 16, fontWeight: 600 }}>
              {detailType === 'recognized' ? '成功识别详情' : '识别失败详情'}
            </span>
            <Tag color={detailType === 'recognized' ? 'success' : 'error'}>
              {detailData.length} 条记录
            </Tag>
          </div>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button 
            key="close" 
            onClick={() => setDetailModalVisible(false)}
            style={{ borderRadius: 6 }}
          >
            关闭
          </Button>
        ]}
        width={1000}
        centered
        maskClosable={true}
      >
        <div style={{ maxHeight: 600, overflow: 'hidden' }}>
          <Table
            columns={[
              {
                title: '序号',
                key: 'index',
                width: 60,
                render: (text, record, index) => index + 1,
              },
              {
                title: '测试文本',
                dataIndex: 'text',
                key: 'text',
                ellipsis: true,
                width: '35%',
              },
              {
                title: '识别意图',
                dataIndex: 'predicted_intent',
                key: 'predicted_intent',
                width: '25%',
                render: (text, record) => {
                  const isRecognized = text && 
                                       text !== 'nlu_fallback' && 
                                       text !== 'out_of_scope' &&
                                       (record.confidence || 0) >= (globalConfig.confidenceThreshold || 0.80);
                  
                  return (
                    <Tag color={isRecognized ? 'success' : 'error'}>
                      {isRecognized ? text : '未识别'}
                    </Tag>
                  );
                }
              },
              {
                title: '置信度',
                dataIndex: 'confidence',
                key: 'confidence',
                width: '25%',
                render: (confidence) => {
                  const percent = Math.round((confidence || 0) * 100);
                  const threshold = Math.round((globalConfig.confidenceThreshold || 0.80) * 100);
                  return (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <Progress 
                        percent={percent} 
                        size="small"
                        status={percent >= threshold ? 'success' : 'exception'}
                        style={{ flex: 1 }}
                      />
                      <span style={{ 
                        fontSize: 12, 
                        color: percent >= threshold ? '#52c41a' : '#ff4d4f',
                        fontWeight: 500 
                      }}>
                        {percent}%
                      </span>
                    </div>
                  );
                }
              },
              {
                title: '状态',
                key: 'status',
                width: '15%',
                render: (text, record) => {
                  const isRecognized = record.predicted_intent && 
                                       record.predicted_intent !== 'nlu_fallback' && 
                                       record.predicted_intent !== 'out_of_scope' &&
                                       (record.confidence || 0) >= (globalConfig.confidenceThreshold || 0.80);
                  
                  return (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      {isRecognized ? (
                        <CheckCircleOutlined style={{ color: '#52c41a' }} />
                      ) : (
                        <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                      )}
                      <span style={{ 
                        fontSize: 12,
                        color: isRecognized ? '#52c41a' : '#ff4d4f',
                        fontWeight: 500
                      }}>
                        {isRecognized ? '已识别' : '未识别'}
                      </span>
                    </div>
                  );
                }
              }
            ]}
            dataSource={detailData}
            rowKey={(record, index) => index}
            scroll={{ y: 400 }}
            pagination={{
              ...batchPagination,
              total: detailData.length,
              showTotal: (total) => `共 ${total} 条记录`,
              onChange: (page, pageSize) => {
                setBatchPagination(prev => ({ ...prev, current: page, pageSize }));
              },
              onShowSizeChange: (current, size) => {
                setBatchPagination(prev => ({ ...prev, current: 1, pageSize: size }));
              }
            }}
          />
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

