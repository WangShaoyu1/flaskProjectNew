import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Card, 
  Table, 
  Tag, 
  Progress, 
  Button, 
  Row, 
  Col, 
  Typography, 
  Space,
  message,
  Spin,
  Alert,
  Dropdown,
  Modal
} from 'antd';
import {
  ArrowLeftOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  DownloadOutlined,
  FileExcelOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { toolsAPI } from '../api';
import * as XLSX from 'xlsx';
import { formatLocalTime, formatTimeForFilename } from '../utils/timeUtils';

const { Title, Text } = Typography;

const BatchTestDetail = () => {
  const { recordId } = useParams();
  const navigate = useNavigate();
  const hasLoaded = useRef(false); // 防止重复加载
  
  const [loading, setLoading] = useState(true);
  const [batchRecord, setBatchRecord] = useState(null);
  const [testResults, setTestResults] = useState([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });

  // 详情弹窗状态
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [detailType, setDetailType] = useState(''); // 'recognized' 或 'unrecognized'
  const [detailData, setDetailData] = useState([]);
  const [detailPagination, setDetailPagination] = useState({
    current: 1,
    pageSize: 10
  });

  // 加载批量测试详情
  const loadBatchTestDetail = async () => {
    if (!recordId || hasLoaded.current) {
      return;
    }
    
    hasLoaded.current = true;
    setLoading(true);
    
    try {
      // 确保recordId是数字
      const numericRecordId = parseInt(recordId, 10);
      if (isNaN(numericRecordId)) {
        throw new Error('无效的记录ID');
      }
      
      const response = await toolsAPI.getBatchTestRecordDetail(numericRecordId);
      
      // 后端直接返回数据，格式为 { record: {...}, test_results: [...] }
      if (response.data && response.data.record) {
        setBatchRecord(response.data.record);
        setTestResults(response.data.test_results || []);
        setPagination(prev => ({
          ...prev,
          total: response.data.test_results?.length || 0
        }));
      } else {
        console.error('数据格式错误:', response.data);
        message.error('数据格式错误，无法加载测试详情');
        navigate('/testing');
      }
    } catch (error) {
      console.error('加载批量测试详情失败:', error);
      
      // 更详细的错误处理
      if (error.response?.status === 404) {
        message.error('测试记录不存在或已被删除');
      } else if (error.response?.status === 500) {
        message.error('服务器内部错误，请稍后重试');
      } else if (error.code === 'NETWORK_ERROR') {
        message.error('网络连接失败，请检查网络状态');
      } else {
        message.error('加载测试详情失败，请稍后重试');
      }
      navigate('/testing');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 重置加载标志并加载数据
    hasLoaded.current = false;
    loadBatchTestDetail();
    
    // 清理函数：当组件卸载或recordId变化时重置状态
    return () => {
      hasLoaded.current = false;
    };
  }, [recordId]);

  // 下载Excel格式
  const downloadExcel = () => {
    if (!testResults.length) {
      message.warning('没有可下载的数据');
      return;
    }

    try {
      // 准备Excel数据
      const excelData = testResults.map((item, index) => {
        const isRecognized = item.predicted_intent && 
                             item.predicted_intent !== 'nlu_fallback' && 
                             item.predicted_intent !== 'out_of_scope' &&
                             (item.confidence || 0) >= (batchRecord.confidence_threshold || 0.80);
        
        return {
          '序号': index + 1,
          '测试文本': item.text || '',
          '识别意图': isRecognized ? item.predicted_intent : '未识别',
          '置信度': item.confidence ? (item.confidence * 100).toFixed(2) + '%' : '0%',
          '阈值': batchRecord.confidence_threshold?.toFixed(2) || '0.80',
          '状态': isRecognized ? '已识别' : '未识别',
          '实体信息': item.entities ? JSON.stringify(item.entities) : '',
          '响应时间': item.response_time != null ? `${Number(item.response_time).toFixed(0)}ms` : '-'
        };
      });

      // 创建工作簿，直接包含详细结果
      const workbook = XLSX.utils.book_new();
      
      // 只添加详细结果工作表
      const detailSheet = XLSX.utils.json_to_sheet(excelData);
      XLSX.utils.book_append_sheet(workbook, detailSheet, '测试结果');

      // 生成文件名
      const timestamp = formatTimeForFilename(batchRecord.created_at);
      const filename = `批量测试结果_${batchRecord.test_name || '未命名'}_${timestamp}.xlsx`;

      // 下载文件
      XLSX.writeFile(workbook, filename);
      message.success('Excel文件下载成功');
    } catch (error) {
      console.error('下载Excel失败:', error);
      message.error('下载Excel失败');
    }
  };

  // 下载CSV格式
  const downloadCSV = () => {
    if (!testResults.length) {
      message.warning('没有可下载的数据');
      return;
    }

    try {
      // 准备CSV数据
      const csvData = testResults.map((item, index) => {
        const isRecognized = item.predicted_intent && 
                             item.predicted_intent !== 'nlu_fallback' && 
                             item.predicted_intent !== 'out_of_scope' &&
                             (item.confidence || 0) >= (batchRecord.confidence_threshold || 0.80);
        
        return {
          '序号': index + 1,
          '测试文本': item.text || '',
          '识别意图': isRecognized ? item.predicted_intent : '未识别',
          '置信度': item.confidence ? (item.confidence * 100).toFixed(2) + '%' : '0%',
          '阈值': batchRecord.confidence_threshold?.toFixed(2) || '0.80',
          '状态': isRecognized ? '已识别' : '未识别',
          '实体信息': item.entities ? JSON.stringify(item.entities) : '',
          '响应时间': item.response_time != null ? `${Number(item.response_time).toFixed(0)}ms` : '-'
        };
      });

      // 转换为CSV格式，直接从详细数据开始
      const headers = Object.keys(csvData[0]);
      const csvContent = [
        // 添加BOM以支持中文
        '\ufeff',
        // 添加表头
        headers.join(','),
        // 添加数据行
        ...csvData.map(row => 
          headers.map(header => {
            const value = row[header] || '';
            // 如果包含逗号或引号，需要用引号包围并转义
            return value.toString().includes(',') || value.toString().includes('"') 
              ? `"${value.toString().replace(/"/g, '""')}"` 
              : value;
          }).join(',')
        )
      ].join('\n');

      // 创建下载链接
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      
      const timestamp = formatTimeForFilename(batchRecord.created_at);
      const filename = `批量测试结果_${batchRecord.test_name || '未命名'}_${timestamp}.csv`;
      
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      message.success('CSV文件下载成功');
    } catch (error) {
      console.error('下载CSV失败:', error);
      message.error('下载CSV失败');
    }
  };

  // 下载菜单项
  const downloadMenuItems = [
    {
      key: 'excel',
      icon: <FileExcelOutlined />,
      label: 'Excel格式 (.xlsx)',
      onClick: downloadExcel
    },
    {
      key: 'csv',
      icon: <FileTextOutlined />,
      label: 'CSV格式 (.csv)',
      onClick: downloadCSV
    }
  ];

  // 显示详情弹窗
  const showDetailModal = (type) => {
    let filteredData = [];
    
    if (type === 'recognized') {
      // 过滤出成功识别的数据
      filteredData = testResults.filter(item => 
        item.predicted_intent && 
        item.predicted_intent !== 'nlu_fallback' && 
        item.predicted_intent !== 'out_of_scope' &&
        (item.confidence || 0) >= (batchRecord.confidence_threshold || 0.80)
      );
    } else if (type === 'unrecognized') {
      // 过滤出未识别的数据
      filteredData = testResults.filter(item => 
        !item.predicted_intent || 
        item.predicted_intent === 'nlu_fallback' || 
        item.predicted_intent === 'out_of_scope' ||
        (item.confidence || 0) < (batchRecord.confidence_threshold || 0.80)
      );
    }
    
    setDetailType(type);
    setDetailData(filteredData);
    setDetailModalVisible(true);
    setDetailPagination({ current: 1, pageSize: 10 }); // 重置分页
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="正在加载批量测试详情..." />
      </div>
    );
  }

  if (!batchRecord) {
    return (
      <Alert
        message="数据加载失败"
        description="未找到指定的批量测试记录"
        type="error"
        showIcon
        action={
          <Button type="primary" onClick={() => navigate('/testing')}>
            返回测试中心
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ padding: '0 24px 24px' }}>
      {/* 页面头部 */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        marginBottom: 24,
        padding: '16px 0',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate('/testing', { state: { activeTab: 'batch' } })}
            style={{ borderRadius: 6 }}
          >
            返回测试中心
          </Button>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <BarChartOutlined style={{ color: '#1890ff', fontSize: 20 }} />
            <Title level={3} style={{ margin: 0 }}>
              批量测试详情
            </Title>
            <Tag color="blue">
              {formatLocalTime(batchRecord.created_at)}
            </Tag>
          </div>
        </div>

        <Dropdown menu={{ items: downloadMenuItems }}>
          <Button 
            type="primary" 
            icon={<DownloadOutlined />}
            style={{ borderRadius: 6 }}
          >
            下载结果
          </Button>
        </Dropdown>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 32, fontWeight: 'bold', color: '#1890ff', marginBottom: 8 }}>
                {batchRecord.total_tests}
              </div>
              <div style={{ fontSize: 16, color: '#666' }}>总测试数</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card 
            hoverable 
            onClick={() => showDetailModal('recognized')} 
            style={{ cursor: 'pointer' }}
          >
            <div style={{ textAlign: 'center' }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                gap: 8,
                marginBottom: 8
              }}>
                <div style={{ fontSize: 32, fontWeight: 'bold', color: '#52c41a' }}>
                  {batchRecord.recognized_count}
                </div>
                <EyeOutlined style={{ color: '#999', fontSize: 14 }} />
              </div>
              <div style={{ fontSize: 16, color: '#666' }}>成功识别</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 32, fontWeight: 'bold', color: '#fa8c16', marginBottom: 8 }}>
                {batchRecord.recognition_rate?.toFixed(1)}%
              </div>
              <div style={{ fontSize: 16, color: '#666' }}>识别率</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card 
            hoverable 
            onClick={() => showDetailModal('unrecognized')} 
            style={{ cursor: 'pointer' }}
          >
            <div style={{ textAlign: 'center' }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                gap: 8,
                marginBottom: 8
              }}>
                <div style={{ fontSize: 32, fontWeight: 'bold', color: '#ff4d4f' }}>
                  {batchRecord.total_tests - batchRecord.recognized_count}
                </div>
                <EyeOutlined style={{ color: '#999', fontSize: 14 }} />
              </div>
              <div style={{ fontSize: 16, color: '#666' }}>识别失败</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 测试信息 */}
      <Card title="测试信息" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Text strong>测试名称：</Text>
            <Text>{batchRecord.test_name || '未命名'}</Text>
          </Col>
          <Col span={6}>
            <Text strong>置信度阈值：</Text>
            <Tag color="processing">{batchRecord.confidence_threshold?.toFixed(2)}</Tag>
          </Col>
          <Col span={6}>
            <Text strong>测试时间：</Text>
            <Text>{formatLocalTime(batchRecord.created_at)}</Text>
          </Col>
          <Col span={6}>
            <Text strong>平均响应时间：</Text>
            <Text>
              {(() => {
                if (testResults.length === 0) return 'N/A';
                
                // 过滤出有效的响应时间数据
                const validResponseTimes = testResults
                  .map(item => item.response_time)
                  .filter(time => time != null && time > 0);
                
                if (validResponseTimes.length === 0) return 'N/A';
                
                const avgTime = validResponseTimes.reduce((sum, time) => sum + time, 0) / validResponseTimes.length;
                return Math.round(avgTime) + 'ms';
              })()}
            </Text>
          </Col>
        </Row>
      </Card>

      {/* 详细测试结果表格 */}
      <Card title="测试结果详情">
        <Table
          columns={[
            {
              title: '序号',
              key: 'index',
              width: 80,
              render: (text, record, index) => 
                (pagination.current - 1) * pagination.pageSize + index + 1,
            },
            {
              title: '测试文本',
              dataIndex: 'text',
              key: 'text',
              ellipsis: true,
              width: '30%',
            },
            {
              title: '识别意图',
              dataIndex: 'predicted_intent',
              key: 'predicted_intent',
              width: '20%',
              render: (text, record) => {
                const isRecognized = text && 
                                     text !== 'nlu_fallback' && 
                                     text !== 'out_of_scope' &&
                                     (record.confidence || 0) >= (batchRecord.confidence_threshold || 0.80);
                
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
              width: '20%',
              render: (confidence) => {
                const percent = Math.round((confidence || 0) * 100);
                const threshold = Math.round((batchRecord.confidence_threshold || 0.80) * 100);
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
                      fontWeight: 500,
                      minWidth: 35
                    }}>
                      {percent}%
                    </span>
                  </div>
                );
              }
            },
            {
              title: '响应时间',
              dataIndex: 'response_time',
              key: 'response_time',
              width: '10%',
              render: (time) => {
                if (time == null || time === undefined) return '-';
                return `${Number(time).toFixed(0)}ms`;
              }
            },
            {
              title: '状态',
              key: 'status',
              width: '10%',
              render: (text, record) => {
                const isRecognized = record.predicted_intent && 
                                     record.predicted_intent !== 'nlu_fallback' && 
                                     record.predicted_intent !== 'out_of_scope' &&
                                     (record.confidence || 0) >= (batchRecord.confidence_threshold || 0.80);
                
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
          dataSource={testResults}
          rowKey={(record, index) => index}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
            onChange: (page, pageSize) => {
              setPagination(prev => ({ ...prev, current: page, pageSize }));
            },
            onShowSizeChange: (current, size) => {
              setPagination(prev => ({ ...prev, current: 1, pageSize: size }));
            }
          }}
          scroll={{ y: 600 }}
        />
      </Card>

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
                render: (text, record, index) => 
                  (detailPagination.current - 1) * detailPagination.pageSize + index + 1,
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
                                       (record.confidence || 0) >= (batchRecord.confidence_threshold || 0.80);
                  
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
                  const threshold = Math.round((batchRecord.confidence_threshold || 0.80) * 100);
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
                 title: '响应时间',
                 dataIndex: 'response_time',
                 key: 'response_time',
                 width: '15%',
                 render: (time) => {
                   if (time == null || time === undefined) return '-';
                   return `${Number(time).toFixed(0)}ms`;
                 }
               }
            ]}
            dataSource={detailData}
            rowKey={(record, index) => index}
            scroll={{ y: 400 }}
            pagination={{
              ...detailPagination,
              total: detailData.length,
              showTotal: (total) => `共 ${total} 条记录`,
              onChange: (page, pageSize) => {
                setDetailPagination(prev => ({ ...prev, current: page, pageSize }));
              },
              onShowSizeChange: (current, size) => {
                setDetailPagination(prev => ({ ...prev, current: 1, pageSize: size }));
              }
            }}
          />
        </div>
      </Modal>
    </div>
  );
};

export default BatchTestDetail; 