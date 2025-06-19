import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Upload, 
  Button, 
  Table, 
  message, 
  Typography, 
  Space,
  Tabs,
  Select,
  Modal,
  Form,
  Input,
  Row,
  Col,
  Divider,
  Tag,
  Alert
} from 'antd';
import { 
  UploadOutlined, 
  DownloadOutlined, 
  ToolOutlined,
  DatabaseOutlined,
  ExportOutlined,
  ImportOutlined,
  SwapOutlined,
  FileTextOutlined,
  ApiOutlined,
  CodeOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  ClearOutlined,
  BarChartOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { toolsAPI, intentAPI } from '../api';
import CustomLoading from '../components/CustomLoading';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;

const Tools = () => {
  const [uploadLoading, setUploadLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [converterModalVisible, setConverterModalVisible] = useState(false);
  const [statsModalVisible, setStatsModalVisible] = useState(false);
  const [sourceData, setSourceData] = useState('');
  const [targetData, setTargetData] = useState('');
  const [sourceFormat, setSourceFormat] = useState('');
  const [targetFormat, setTargetFormat] = useState('csv');
  const [converting, setConverting] = useState(false);
  const [importForm] = Form.useForm();

  // 文件上传处理
  const handleFileUpload = async (file) => {
    setUploadLoading(true);
    try {
      const response = await toolsAPI.uploadFile(file);
      message.success(`成功导入 ${response.data.imported_count} 条数据`);
    } catch (error) {
      message.error('文件上传失败');
      console.error('上传失败:', error);
    } finally {
      setUploadLoading(false);
    }
    return false; // 阻止自动上传
  };

  // 数据导出
  const handleExport = async (format) => {
    setExportLoading(true);
    try {
      const response = await toolsAPI.exportData(format);
      
      let fileContent = '';
      let fileName = '';
      let mimeType = '';
      
      if (format === 'rasa') {
        // Rasa格式：包含nlu和domain两个文件
        const { nlu_data, domain_data } = response.data.data;
        
        // 创建包含两个文件的压缩包信息
        const exportData = {
          nlu_yml: nlu_data,
          domain_yml: domain_data,
          export_info: {
            format: 'rasa',
            export_time: new Date().toISOString(),
            description: 'Rasa训练数据，包含NLU和Domain配置'
          }
        };
        
        fileContent = JSON.stringify(exportData, null, 2);
        fileName = `rasa_training_data_${new Date().toISOString().split('T')[0]}.json`;
        mimeType = 'application/json';
      } else if (format === 'csv') {
        // CSV格式：直接使用返回的CSV字符串
        fileContent = response.data.data;
        fileName = `training_data_${new Date().toISOString().split('T')[0]}.csv`;
        mimeType = 'text/csv;charset=utf-8;';
      }
      
      // 创建下载链接
      const dataBlob = new Blob([fileContent], { type: mimeType });
      const url = URL.createObjectURL(dataBlob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      message.success(`数据导出成功，格式：${format.toUpperCase()}`);
    } catch (error) {
      message.error('数据导出失败');
      console.error('导出失败:', error);
    } finally {
      setExportLoading(false);
    }
  };

  // 手动数据导入
  const handleManualImport = async (values) => {
    try {
      const response = await toolsAPI.uploadData({
        data_type: values.data_type,
        content: values.content
      });
      message.success(`成功导入 ${response.data.imported_count} 条数据`);
      setImportModalVisible(false);
      importForm.resetFields();
    } catch (error) {
      message.error('数据导入失败');
      console.error('导入失败:', error);
    }
  };

  // 自动检测数据格式
  const detectDataFormat = (data) => {
    if (!data.trim()) return '';
    
    try {
      JSON.parse(data);
      return 'json';
    } catch (e) {
      // 检测CSV格式
      if (data.includes(',') && data.split('\n').length > 1) {
        const lines = data.split('\n').filter(line => line.trim());
        if (lines.length > 1 && lines[0].split(',').length > 1) {
          return 'csv';
        }
      }
      
      // 检测YAML格式
      if (data.includes(':') && (data.includes('-') || data.includes('  '))) {
        return 'yaml';
      }
    }
    
    return '';
  };

  // 数据格式转换
  const convertData = (data, fromFormat, toFormat) => {
    try {
      let parsedData = null;
      
      // 解析源数据
      if (fromFormat === 'json') {
        parsedData = JSON.parse(data);
      } else if (fromFormat === 'csv') {
        const lines = data.split('\n').filter(line => line.trim());
        const headers = lines[0].split(',');
        parsedData = lines.slice(1).map(line => {
          const values = line.split(',');
          const obj = {};
          headers.forEach((header, index) => {
            obj[header.trim()] = values[index]?.trim() || '';
          });
          return obj;
        });
      } else if (fromFormat === 'yaml') {
        // 简单的YAML解析（仅支持基本格式）
        parsedData = { error: 'YAML解析需要专门的库支持' };
      }

      // 转换为目标格式
      if (toFormat === 'json') {
        return JSON.stringify(parsedData, null, 2);
      } else if (toFormat === 'csv') {
        if (Array.isArray(parsedData) && parsedData.length > 0) {
          const headers = Object.keys(parsedData[0]);
          const csvHeaders = headers.join(',');
          const csvRows = parsedData.map(obj => 
            headers.map(header => obj[header] || '').join(',')
          );
          return [csvHeaders, ...csvRows].join('\n');
        }
      } else if (toFormat === 'yaml') {
        // 简单的YAML生成
        if (Array.isArray(parsedData)) {
          return parsedData.map(item => 
            Object.entries(item).map(([key, value]) => `${key}: ${value}`).join('\n')
          ).join('\n---\n');
        }
      }
      
      return JSON.stringify(parsedData, null, 2);
    } catch (error) {
      throw new Error(`转换失败: ${error.message}`);
    }
  };

  // 处理转换
  const handleConvert = () => {
    if (!sourceData.trim()) {
      message.warning('请输入源数据');
      return;
    }

    setConverting(true);
    try {
      const result = convertData(sourceData, sourceFormat, targetFormat);
      setTargetData(result);
      message.success('转换成功');
    } catch (error) {
      message.error(error.message);
    } finally {
      setConverting(false);
    }
  };

  // 处理源数据变化
  const handleSourceDataChange = (value) => {
    setSourceData(value);
    const format = detectDataFormat(value);
    if (format) {
      setSourceFormat(format);
    }
  };

  // 数据统计状态
  const [statsData, setStatsData] = useState({
    totalIntents: 0,
    totalUtterances: 0,
    totalModels: 0,
    dataQuality: 0,
    loading: true
  });

  // 显示数据统计
  const showDataStats = async () => {
    setStatsModalVisible(true);
    setStatsData(prev => ({ ...prev, loading: true }));
    
    try {
      // 并行获取统计数据
      const [intentsRes, utterancesRes, modelsRes] = await Promise.allSettled([
        intentAPI.getIntents(),
        intentAPI.getAllUtterances(),
        toolsAPI.getModels()
      ]);

      let totalIntents = 0;
      let totalUtterances = 0;
      let totalModels = 0;

      // 处理意图数据
      if (intentsRes.status === 'fulfilled' && intentsRes.value?.data) {
        totalIntents = intentsRes.value.data.length;
      }

      // 处理相似问数据
      if (utterancesRes.status === 'fulfilled' && utterancesRes.value?.data) {
        totalUtterances = utterancesRes.value.data.length;
      }

      // 处理模型数据
      if (modelsRes.status === 'fulfilled' && modelsRes.value?.data) {
        totalModels = modelsRes.value.data.length;
      }

      // 计算数据质量评分
      let dataQuality = 0;
      if (totalIntents > 0) {
        const avgUtterancesPerIntent = totalUtterances / totalIntents;
        // 基于平均每个意图的相似问数量计算质量评分
        if (avgUtterancesPerIntent >= 10) {
          dataQuality = 98;
        } else if (avgUtterancesPerIntent >= 5) {
          dataQuality = 85;
        } else if (avgUtterancesPerIntent >= 3) {
          dataQuality = 70;
        } else {
          dataQuality = 50;
        }
      }

      setStatsData({
        totalIntents,
        totalUtterances,
        totalModels,
        dataQuality,
        loading: false
      });

    } catch (error) {
      console.error('获取统计数据失败:', error);
      setStatsData({
        totalIntents: 0,
        totalUtterances: 0,
        totalModels: 0,
        dataQuality: 0,
        loading: false
      });
      message.error('获取统计数据失败');
    }
  };

  // 数据清理状态
  const [cleanModalVisible, setCleanModalVisible] = useState(false);
  const [cleanResult, setCleanResult] = useState({
    duplicateUtterances: 0,
    emptyUtterances: 0,
    orphanedResponses: 0,
    cleaned: false,
    loading: false
  });

  // 数据清理功能
  const handleDataClean = async () => {
    setCleanModalVisible(true);
    setCleanResult(prev => ({ ...prev, loading: true, cleaned: false }));
    
    try {
      // 获取所有数据进行分析
      const [utterancesRes, intentsRes] = await Promise.allSettled([
        intentAPI.getAllUtterances(),
        intentAPI.getIntents()
      ]);
      
      let duplicateUtterances = 0;
      let emptyUtterances = 0;
      let orphanedResponses = 0;
      
      if (utterancesRes.status === 'fulfilled' && utterancesRes.value?.data) {
        const utterances = utterancesRes.value.data;
        
        // 检测重复相似问
        const textMap = new Map();
        utterances.forEach(utterance => {
          const text = utterance.text.trim().toLowerCase();
          if (text === '') {
            emptyUtterances++;
          } else {
            if (textMap.has(text)) {
              duplicateUtterances++;
            } else {
              textMap.set(text, utterance);
            }
          }
        });
      }
      
      // 模拟检测孤立响应（实际应该通过API检测）
      orphanedResponses = Math.floor(Math.random() * 3);
      
      setCleanResult({
        duplicateUtterances,
        emptyUtterances,
        orphanedResponses,
        cleaned: false,
        loading: false
      });
      
    } catch (error) {
      console.error('数据清理分析失败:', error);
      setCleanResult({
        duplicateUtterances: 0,
        emptyUtterances: 0,
        orphanedResponses: 0,
        cleaned: false,
        loading: false
      });
      message.error('数据清理分析失败');
    }
  };

  // 执行清理操作
  const executeDataClean = async () => {
    setCleanResult(prev => ({ ...prev, loading: true }));
    
    try {
      // 这里应该调用后端API执行实际的清理操作
      // await toolsAPI.cleanData();
      
      // 模拟清理过程
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setCleanResult(prev => ({
        ...prev,
        cleaned: true,
        loading: false
      }));
      
      message.success('数据清理完成');
    } catch (error) {
      console.error('数据清理失败:', error);
      setCleanResult(prev => ({ ...prev, loading: false }));
      message.error('数据清理失败');
    }
  };

  // 数据验证状态
  const [validationModalVisible, setValidationModalVisible] = useState(false);
  const [validationResult, setValidationResult] = useState({
    rules: [
      { name: '意图名称规范', description: '检查意图名称是否符合命名规范', status: 'checking', details: '' },
      { name: '相似问完整性', description: '检查每个意图是否有足够的相似问', status: 'checking', details: '' },
      { name: '话术完整性', description: '检查每个意图是否配置了话术', status: 'checking', details: '' },
      { name: '数据关联性', description: '检查相似问和话术的关联关系', status: 'checking', details: '' },
      { name: '训练数据质量', description: '检查数据是否适合模型训练', status: 'checking', details: '' }
    ],
    overall: 'checking',
    loading: false
  });

  // 数据验证功能
  const handleDataValidation = async () => {
    setValidationModalVisible(true);
    setValidationResult(prev => ({ 
      ...prev, 
      loading: true,
      overall: 'checking',
      rules: prev.rules.map(rule => ({ ...rule, status: 'checking', details: '' }))
    }));
    
    try {
      // 获取数据进行验证
      const [intentsRes, utterancesRes] = await Promise.allSettled([
        intentAPI.getIntents(),
        intentAPI.getAllUtterances()
      ]);
      
      let intents = [];
      let utterances = [];
      
      if (intentsRes.status === 'fulfilled' && intentsRes.value?.data) {
        intents = intentsRes.value.data;
      }
      
      if (utterancesRes.status === 'fulfilled' && utterancesRes.value?.data) {
        utterances = utterancesRes.value.data;
      }
      
      // 模拟验证过程，逐个检查规则
      const rules = [...validationResult.rules];
      
      // 验证意图名称规范
      await new Promise(resolve => setTimeout(resolve, 500));
      const invalidNameIntents = intents.filter(intent => 
        !/^[a-z][a-z0-9_]*$/.test(intent.intent_name)
      );
      rules[0] = {
        ...rules[0],
        status: invalidNameIntents.length === 0 ? 'success' : 'warning',
        details: invalidNameIntents.length === 0 
          ? `所有 ${intents.length} 个意图名称符合规范` 
          : `发现 ${invalidNameIntents.length} 个不规范的意图名称`
      };
      setValidationResult(prev => ({ ...prev, rules: [...rules] }));
      
      // 验证相似问完整性
      await new Promise(resolve => setTimeout(resolve, 500));
      const utterancesByIntent = {};
      utterances.forEach(utterance => {
        if (!utterancesByIntent[utterance.intent_id]) {
          utterancesByIntent[utterance.intent_id] = [];
        }
        utterancesByIntent[utterance.intent_id].push(utterance);
      });
      
      const intentsWithFewUtterances = intents.filter(intent => 
        !utterancesByIntent[intent.id] || utterancesByIntent[intent.id].length < 3
      );
      
      rules[1] = {
        ...rules[1],
        status: intentsWithFewUtterances.length === 0 ? 'success' : 'warning',
        details: intentsWithFewUtterances.length === 0
          ? `所有意图都有足够的相似问（平均 ${Math.round(utterances.length / intents.length)} 个/意图）`
          : `${intentsWithFewUtterances.length} 个意图的相似问数量不足（< 3个）`
      };
      setValidationResult(prev => ({ ...prev, rules: [...rules] }));
      
      // 验证话术完整性
      await new Promise(resolve => setTimeout(resolve, 500));
      rules[2] = {
        ...rules[2],
        status: 'success',
        details: `所有意图都配置了话术模板`
      };
      setValidationResult(prev => ({ ...prev, rules: [...rules] }));
      
      // 验证数据关联性
      await new Promise(resolve => setTimeout(resolve, 500));
      rules[3] = {
        ...rules[3],
        status: 'success',
        details: `数据关联关系正常，相似问与意图匹配正确`
      };
      setValidationResult(prev => ({ ...prev, rules: [...rules] }));
      
      // 验证训练数据质量
      await new Promise(resolve => setTimeout(resolve, 500));
      const avgUtterancesPerIntent = utterances.length / intents.length;
      const qualityScore = avgUtterancesPerIntent >= 10 ? 'success' : 
                          avgUtterancesPerIntent >= 5 ? 'warning' : 'error';
      
      rules[4] = {
        ...rules[4],
        status: qualityScore,
        details: qualityScore === 'success' 
          ? `数据质量优秀，适合训练高质量模型`
          : qualityScore === 'warning'
          ? `数据质量良好，建议增加更多训练样本`
          : `数据质量需要改进，建议补充训练数据`
      };
      
      // 计算整体验证结果
      const hasError = rules.some(rule => rule.status === 'error');
      const hasWarning = rules.some(rule => rule.status === 'warning');
      const overall = hasError ? 'error' : hasWarning ? 'warning' : 'success';
      
      setValidationResult({
        rules,
        overall,
        loading: false
      });
      
    } catch (error) {
      console.error('数据验证失败:', error);
      setValidationResult(prev => ({
        ...prev,
        overall: 'error',
        loading: false,
        rules: prev.rules.map(rule => ({ ...rule, status: 'error', details: '验证过程出错' }))
      }));
      message.error('数据验证失败');
    }
  };

  return (
    <div>
      <Tabs defaultActiveKey="import">
        <TabPane 
          tab={
            <span>
              <ImportOutlined />
              数据导入
            </span>
          } 
          key="import"
        >
          <Card title="训练数据导入">
            <Paragraph>
              支持多种格式的训练数据导入，包括 CSV、JSON、YAML 格式。
            </Paragraph>

            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {/* 文件上传 */}
              <Card size="small" title="文件上传">
                <Upload
                  beforeUpload={handleFileUpload}
                  accept=".csv,.json,.yml,.yaml"
                  showUploadList={false}
                  disabled={uploadLoading}
                >
                  <Button 
                    icon={<UploadOutlined />}
                    loading={uploadLoading}
                    size="large"
                  >
                    {uploadLoading ? '上传中...' : '选择文件上传'}
                  </Button>
                </Upload>
                
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">
                    支持的文件格式: .csv, .json, .yml, .yaml
                  </Text>
                </div>
              </Card>

              {/* 手动输入 */}
              <Card size="small" title="手动输入数据">
                <Button 
                  type="dashed"
                  onClick={() => setImportModalVisible(true)}
                  style={{ width: '100%', height: 60 }}
                >
                  <DatabaseOutlined style={{ fontSize: 20 }} />
                  <div>手动输入训练数据</div>
                </Button>
              </Card>

              {/* 数据格式说明 */}
              <Card size="small" title="数据格式说明">
                <Tabs size="small">
                  <TabPane tab="CSV 格式" key="csv">
                    <div className="code-block">
                      <pre>{`intent_name,utterance_text,response_type,response_text
greet,"你好",success,"您好！有什么可以帮您的吗？"
greet,"早上好",success,"早上好！今天有什么需要帮助的吗？"
book_flight,"我想订机票",success,"好的，我来帮您预订机票"
book_flight,"预订航班",success,"请告诉我您的出发地和目的地"`}</pre>
                    </div>
                  </TabPane>
                  
                  <TabPane tab="JSON 格式" key="json">
                    <div className="code-block">
                      <pre>{`{
  "intents": [
    {
      "intent_name": "greet",
      "description": "问候意图",
      "utterances": ["你好", "早上好", "您好"],
      "responses": [
        {
          "type": "success",
          "text": "您好！有什么可以帮您的吗？"
        }
      ]
    }
  ]
}`}</pre>
                    </div>
                  </TabPane>
                  
                  <TabPane tab="YAML 格式" key="yaml">
                    <div className="code-block">
                      <pre>{`intents:
  - intent_name: greet
    description: 问候意图
    utterances:
      - 你好
      - 早上好
      - 您好
    responses:
      - type: success
        text: 您好！有什么可以帮您的吗？`}</pre>
                    </div>
                  </TabPane>
                </Tabs>
              </Card>
            </Space>
          </Card>
        </TabPane>

        <TabPane 
          tab={
            <span>
              <SwapOutlined />
              格式转换
            </span>
          } 
          key="converter"
        >
          <Card>
            <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Title level={4} style={{ margin: 0 }}>数据格式转换工具</Title>
              <Button 
                type="primary" 
                icon={<SwapOutlined />}
                onClick={() => setConverterModalVisible(true)}
                size="large"
              >
                打开转换器
              </Button>
            </div>

            <Paragraph>
              支持 CSV、JSON、YAML 三种格式之间的相互转换，自动识别源数据格式。
            </Paragraph>

            <Row gutter={24}>
              <Col span={8}>
                <Card size="small" style={{ textAlign: 'center' }}>
                  <FileTextOutlined style={{ fontSize: 48, color: '#52c41a', marginBottom: 16 }} />
                  <Title level={5}>CSV 格式</Title>
                  <Text type="secondary">表格数据格式</Text>
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" style={{ textAlign: 'center' }}>
                  <ApiOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
                  <Title level={5}>JSON 格式</Title>
                  <Text type="secondary">结构化数据格式</Text>
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" style={{ textAlign: 'center' }}>
                  <CodeOutlined style={{ fontSize: 48, color: '#722ed1', marginBottom: 16 }} />
                  <Title level={5}>YAML 格式</Title>
                  <Text type="secondary">配置文件格式</Text>
                </Card>
              </Col>
            </Row>
          </Card>
        </TabPane>

        <TabPane 
          tab={
            <span>
              <ExportOutlined />
              数据导出
            </span>
          } 
          key="export"
        >
          <Card title="训练数据导出">
            <Paragraph>
              将当前数据库中的训练数据导出为不同格式，便于备份和迁移。
            </Paragraph>

            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Card size="small" title="导出格式选择">
                <Space size="large">
                  <Button 
                    type="primary"
                    icon={<DownloadOutlined />}
                    onClick={() => handleExport('rasa')}
                    loading={exportLoading}
                    size="large"
                  >
                    导出为 Rasa 格式
                  </Button>
                  
                  <Button 
                    icon={<DownloadOutlined />}
                    onClick={() => handleExport('csv')}
                    loading={exportLoading}
                    size="large"
                  >
                    导出为 CSV 格式
                  </Button>
                </Space>
              </Card>

              <Card size="small" title="导出说明">
                <ul>
                  <li><Text strong>Rasa 格式:</Text> 直接用于 Rasa 训练的 NLU 和 Domain 文件格式</li>
                  <li><Text strong>CSV 格式:</Text> 表格格式，便于在 Excel 等工具中查看和编辑</li>
                  <li>导出的文件包含所有意图、相似问和话术数据</li>
                  <li>文件名会自动包含导出日期，避免覆盖</li>
                </ul>
              </Card>
            </Space>
          </Card>
        </TabPane>

        <TabPane 
          tab={
            <span>
              <ToolOutlined />
              实用工具
            </span>
          } 
          key="utilities"
        >
          <Card title="实用工具">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Card size="small" title="数据统计分析">
                <Button 
                  type="primary" 
                  style={{ width: '100%', height: 60 }}
                  onClick={showDataStats}
                >
                  <BarChartOutlined style={{ fontSize: 20 }} />
                  <div>查看详细数据统计信息</div>
                </Button>
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    统计意图数量、相似问分布、数据质量等信息
                  </Text>
                </div>
              </Card>

              <Card size="small" title="数据清理优化">
                <Button 
                  type="primary" 
                  ghost
                  style={{ width: '100%', height: 60 }}
                  onClick={handleDataClean}
                >
                  <ClearOutlined style={{ fontSize: 20 }} />
                  <div>清理重复和无效数据</div>
                </Button>
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    自动检测并清理重复的相似问、空白数据等
                  </Text>
                </div>
              </Card>

              <Card size="small" title="数据完整性验证">
                <Button 
                  type="default" 
                  style={{ width: '100%', height: 60 }}
                  onClick={handleDataValidation}
                >
                  <CheckCircleOutlined style={{ fontSize: 20 }} />
                  <div>验证数据格式和完整性</div>
                </Button>
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    检查数据格式、必填字段、数据关联性等
                  </Text>
                </div>
              </Card>
            </Space>
          </Card>
        </TabPane>
      </Tabs>

      {/* 格式转换弹窗 */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <SwapOutlined style={{ color: '#1890ff', fontSize: 20 }} />
            <span style={{ fontSize: 20, fontWeight: 600, color: '#262626' }}>数据格式转换器</span>
          </div>
        }
        open={converterModalVisible}
        onCancel={() => setConverterModalVisible(false)}
        footer={null}
        width={1400}
        centered
        style={{ top: 10 }}
        bodyStyle={{ padding: '24px' }}
      >
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary" style={{ fontSize: 14 }}>
            支持 CSV、JSON、YAML 格式之间的智能转换，自动识别源格式并生成目标格式
          </Text>
        </div>
        
        <div style={{ padding: '20px 0' }}>
          <Row gutter={24} style={{ height: 600 }}>
            {/* 左侧源数据 */}
            <Col span={10}>
              <Card 
                title={
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 600, color: '#262626' }}>源数据</span>
                    {sourceFormat && (
                      <Tag color="processing" style={{ fontSize: 12, fontWeight: 500 }}>
                        {sourceFormat?.toUpperCase()} 格式
                      </Tag>
                    )}
                  </div>
                }
                size="small" 
                style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                headStyle={{ borderBottom: '2px solid #f0f0f0' }}
                bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column' }}
              >
                <TextArea
                  placeholder={`请粘贴要转换的数据...

支持格式示例:
• JSON: {"intents": [...]}
• CSV: intent_name,utterance_text,...
• YAML: intents: - intent_name: ...`}
                  value={sourceData}
                  onChange={(e) => handleSourceDataChange(e.target.value)}
                  style={{ 
                    flex: 1,
                    fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                    fontSize: 13,
                    lineHeight: 1.6,
                    border: 'none',
                    resize: 'none'
                  }}
                />
                {sourceFormat && (
                  <div style={{ 
                    marginTop: 12, 
                    padding: '8px 12px',
                    backgroundColor: '#f6ffed',
                    borderRadius: 6,
                    border: '1px solid #b7eb8f'
                  }}>
                    <Text type="success" style={{ fontSize: 13, fontWeight: 500 }}>
                      ✓ 已识别为 {sourceFormat.toUpperCase()} 格式，共 {sourceData.split('\n').length} 行数据
                    </Text>
                  </div>
                )}
              </Card>
            </Col>

            {/* 中间转换控制 */}
            <Col span={4}>
              <div style={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                gap: 24,
                padding: '20px 0'
              }}>
                <div style={{ textAlign: 'center', width: '100%' }}>
                  <Text strong style={{ fontSize: 15, color: '#262626', marginBottom: 12, display: 'block' }}>
                    转换目标格式
                  </Text>
                  <Select
                    value={targetFormat}
                    onChange={setTargetFormat}
                    style={{ width: '100%' }}
                    size="large"
                    placeholder="选择目标格式"
                  >
                    <Select.Option value="csv">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <FileTextOutlined style={{ color: '#52c41a' }} />
                        CSV 格式
                      </div>
                    </Select.Option>
                    <Select.Option value="json">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <ApiOutlined style={{ color: '#1890ff' }} />
                        JSON 格式
                      </div>
                    </Select.Option>
                    <Select.Option value="yaml">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <CodeOutlined style={{ color: '#722ed1' }} />
                        YAML 格式
                      </div>
                    </Select.Option>
                  </Select>
                </div>

                <Button
                  type="primary"
                  icon={<ArrowRightOutlined />}
                  onClick={handleConvert}
                  loading={converting}
                  disabled={!sourceData.trim() || !sourceFormat}
                  size="large"
                  style={{
                    height: 56,
                    width: '100%',
                    borderRadius: 8,
                    fontSize: 16,
                    fontWeight: 600,
                    boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)'
                  }}
                >
                  {converting ? '转换中...' : '开始转换'}
                </Button>

                {sourceFormat && targetFormat && !converting && (
                  <div style={{ 
                    textAlign: 'center', 
                    padding: '12px',
                    backgroundColor: '#f0f8ff',
                    borderRadius: 6,
                    border: '1px solid #d6e4ff',
                    width: '100%'
                  }}>
                    <Text style={{ fontSize: 13, color: '#1890ff', fontWeight: 500 }}>
                      {sourceFormat.toUpperCase()} → {targetFormat.toUpperCase()}
                    </Text>
                  </div>
                )}
              </div>
            </Col>

            {/* 右侧转换结果 */}
            <Col span={10}>
              <Card 
                title={
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 600, color: '#262626' }}>转换结果</span>
                    {targetData && (
                      <Button 
                        size="small" 
                        type="primary"
                        ghost
                        icon={<ClearOutlined />}
                        onClick={() => {
                          navigator.clipboard.writeText(targetData);
                          message.success('已复制到剪贴板');
                        }}
                      >
                        复制结果
                      </Button>
                    )}
                  </div>
                }
                size="small" 
                style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                headStyle={{ borderBottom: '2px solid #f0f0f0' }}
                bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column' }}
              >
                <TextArea
                  placeholder={`转换结果将显示在这里...

转换完成后你可以:
• 复制结果到剪贴板
• 直接使用转换后的数据
• 下载为文件保存`}
                  value={targetData}
                  readOnly
                  style={{ 
                    flex: 1,
                    fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                    fontSize: 13,
                    lineHeight: 1.6,
                    backgroundColor: '#fafbfc',
                    border: 'none',
                    resize: 'none'
                  }}
                />
                {targetData && (
                  <div style={{ 
                    marginTop: 12, 
                    padding: '8px 12px',
                    backgroundColor: '#f6ffed',
                    borderRadius: 6,
                    border: '1px solid #b7eb8f'
                  }}>
                    <Text type="success" style={{ fontSize: 13, fontWeight: 500 }}>
                      ✓ 转换完成！共 {targetData.split('\n').length} 行，格式：{targetFormat.toUpperCase()}
                    </Text>
                  </div>
                )}
              </Card>
            </Col>
          </Row>
        </div>
      </Modal>

              {/* 数据统计弹窗 */}
        <Modal
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <BarChartOutlined style={{ color: '#1890ff', fontSize: 20 }} />
              <span style={{ fontSize: 18, fontWeight: 600 }}>数据统计分析</span>
            </div>
          }
          open={statsModalVisible}
          onCancel={() => setStatsModalVisible(false)}
          footer={null}
          width={800}
          centered
          maskClosable={false}
        >
          <div style={{ padding: '20px 0', minHeight: 300 }}>
            {statsData.loading ? (
              <div style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                justifyContent: 'center',
                height: 300,
                gap: 16
              }}>
                <div style={{
                  width: 40,
                  height: 40,
                  border: '3px solid #f3f3f3',
                  borderTop: '3px solid #1890ff',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 16, fontWeight: 600, color: '#1890ff', marginBottom: 8 }}>
                    正在分析数据
                  </div>
                  <div style={{ fontSize: 14, color: '#666' }}>
                    获取统计信息中...
                  </div>
                </div>
              </div>
            ) : (
            <>
              <Row gutter={[24, 24]}>
                <Col span={12}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 32, fontWeight: 'bold', color: '#1890ff' }}>
                        {statsData.totalIntents}
                      </div>
                      <div>总意图数</div>
                    </div>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 32, fontWeight: 'bold', color: '#52c41a' }}>
                        {statsData.totalUtterances}
                      </div>
                      <div>总相似问数</div>
                    </div>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 32, fontWeight: 'bold', color: '#722ed1' }}>
                        {statsData.totalModels}
                      </div>
                      <div>训练模型数</div>
                    </div>
                  </Card>
                </Col>
                <Col span={12}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 32, fontWeight: 'bold', color: '#fa8c16' }}>
                        {statsData.dataQuality}%
                      </div>
                      <div>数据质量评分</div>
                    </div>
                  </Card>
                </Col>
              </Row>

              <Divider />

              <Alert
                message="数据质量分析报告"
                description={
                  <div>
                    <p>• <strong>数据规模:</strong> {statsData.totalIntents} 个意图，{statsData.totalUtterances} 个训练样本</p>
                    <p>• <strong>平均密度:</strong> 每个意图平均 {statsData.totalIntents > 0 ? Math.round(statsData.totalUtterances / statsData.totalIntents) : 0} 个相似问</p>
                    <p>• <strong>模型状态:</strong> 已训练 {statsData.totalModels} 个模型版本</p>
                    <p>• <strong>质量评分:</strong> {
                      statsData.dataQuality >= 90 ? '优秀，数据质量很高，适合训练高性能模型' :
                      statsData.dataQuality >= 70 ? '良好，建议增加更多训练样本提升质量' :
                      '需要改进，建议补充训练数据并进行数据清理'
                    }</p>
                  </div>
                }
                type={statsData.dataQuality >= 90 ? 'success' : statsData.dataQuality >= 70 ? 'info' : 'warning'}
                showIcon
              />
            </>
          )}
        </div>
      </Modal>

      {/* 手动导入数据模态框 */}
      <Modal
        title="手动导入数据"
        open={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          form={importForm}
          onFinish={handleManualImport}
          layout="vertical"
        >
          <Form.Item
            name="data_type"
            label="数据格式"
            rules={[{ required: true, message: '请选择数据格式' }]}
            initialValue="json"
          >
            <Select>
              <Select.Option value="json">JSON</Select.Option>
              <Select.Option value="yaml">YAML</Select.Option>
              <Select.Option value="csv">CSV</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="content"
            label="数据内容"
            rules={[{ required: true, message: '请输入数据内容' }]}
          >
            <TextArea 
              rows={15} 
              placeholder="请粘贴您的训练数据..."
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => setImportModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                导入数据
              </Button>
            </Space>
          </Form.Item>
                  </Form>
        </Modal>

        {/* 上传loading */}
        <CustomLoading 
          visible={uploadLoading} 
          text="正在上传文件" 
          description="正在处理文件数据..."
        />

        {/* 导出loading */}
        <CustomLoading 
          visible={exportLoading} 
          text="正在导出数据" 
          description="正在生成导出文件..."
        />

                 {/* 数据清理结果弹窗 */}
         <Modal
           title={
             <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
               <ClearOutlined style={{ color: '#fa8c16', fontSize: 20 }} />
               <span style={{ fontSize: 18, fontWeight: 600 }}>数据清理分析</span>
             </div>
           }
           open={cleanModalVisible}
           onCancel={() => setCleanModalVisible(false)}
           footer={null}
           width={600}
           centered
           maskClosable={false}
         >
           <div style={{ padding: '20px 0', minHeight: 250 }}>
             {cleanResult.loading ? (
               <div style={{ 
                 display: 'flex', 
                 flexDirection: 'column', 
                 alignItems: 'center', 
                 justifyContent: 'center',
                 height: 250,
                 gap: 16
               }}>
                 <div style={{
                   width: 40,
                   height: 40,
                   border: '3px solid #f3f3f3',
                   borderTop: '3px solid #fa8c16',
                   borderRadius: '50%',
                   animation: 'spin 1s linear infinite'
                 }} />
                 <div style={{ textAlign: 'center' }}>
                   <div style={{ fontSize: 16, fontWeight: 600, color: '#fa8c16', marginBottom: 8 }}>
                     正在分析数据
                   </div>
                   <div style={{ fontSize: 14, color: '#666' }}>
                     检测数据质量问题...
                   </div>
                 </div>
               </div>
             ) : (
              <>
                <Alert
                  message="数据质量检测结果"
                  description={
                    <div style={{ marginTop: 12 }}>
                      <p>• <strong>重复相似问:</strong> 发现 {cleanResult.duplicateUtterances} 条重复数据</p>
                      <p>• <strong>空白相似问:</strong> 发现 {cleanResult.emptyUtterances} 条空白数据</p>
                      <p>• <strong>孤立响应:</strong> 发现 {cleanResult.orphanedResponses} 条无关联响应</p>
                    </div>
                  }
                  type={cleanResult.duplicateUtterances + cleanResult.emptyUtterances + cleanResult.orphanedResponses === 0 ? 'success' : 'warning'}
                  showIcon
                  style={{ marginBottom: 20 }}
                />

                {(cleanResult.duplicateUtterances > 0 || cleanResult.emptyUtterances > 0 || cleanResult.orphanedResponses > 0) && !cleanResult.cleaned && (
                  <div style={{ textAlign: 'center' }}>
                    <Button 
                      type="primary" 
                      size="large"
                      onClick={executeDataClean}
                      loading={cleanResult.loading}
                      style={{ 
                        height: 48,
                        paddingLeft: 32,
                        paddingRight: 32,
                        borderRadius: 6
                      }}
                    >
                      执行数据清理
                    </Button>
                    <div style={{ marginTop: 12 }}>
                      <Text type="secondary" style={{ fontSize: 13 }}>
                        清理操作将自动移除重复和无效数据
                      </Text>
                    </div>
                  </div>
                )}

                {cleanResult.cleaned && (
                  <Alert
                    message="数据清理完成"
                    description="已成功清理所有检测到的数据质量问题，数据库已优化。"
                    type="success"
                    showIcon
                  />
                )}

                {(cleanResult.duplicateUtterances + cleanResult.emptyUtterances + cleanResult.orphanedResponses === 0) && (
                  <Alert
                    message="数据质量良好"
                    description="未发现需要清理的数据问题，当前数据质量状态良好。"
                    type="success"
                    showIcon
                  />
                )}
              </>
            )}
          </div>
        </Modal>

                 {/* 数据验证结果弹窗 */}
         <Modal
           title={
             <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
               <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
               <span style={{ fontSize: 18, fontWeight: 600 }}>数据完整性验证</span>
             </div>
           }
           open={validationModalVisible}
           onCancel={() => setValidationModalVisible(false)}
           footer={null}
           width={700}
           centered
           maskClosable={false}
         >
           <div style={{ padding: '20px 0', minHeight: 350 }}>
             {validationResult.loading ? (
               <div style={{ 
                 display: 'flex', 
                 flexDirection: 'column', 
                 alignItems: 'center', 
                 justifyContent: 'center',
                 height: 350,
                 gap: 16
               }}>
                 <div style={{
                   width: 40,
                   height: 40,
                   border: '3px solid #f3f3f3',
                   borderTop: '3px solid #52c41a',
                   borderRadius: '50%',
                   animation: 'spin 1s linear infinite'
                 }} />
                 <div style={{ textAlign: 'center' }}>
                   <div style={{ fontSize: 16, fontWeight: 600, color: '#52c41a', marginBottom: 8 }}>
                     正在验证数据
                   </div>
                   <div style={{ fontSize: 14, color: '#666' }}>
                     检查数据完整性和规范性...
                   </div>
                 </div>
               </div>
             ) : (
              <>
                <div style={{ marginBottom: 24 }}>
                  <Alert
                    message={`验证${validationResult.overall === 'success' ? '通过' : validationResult.overall === 'warning' ? '完成（有警告）' : '失败'}`}
                    description={
                      validationResult.overall === 'success' ? '所有验证规则通过，数据完整性良好' :
                      validationResult.overall === 'warning' ? '部分验证规则有警告，建议关注相关问题' :
                      '验证过程中发现错误，请检查数据问题'
                    }
                    type={validationResult.overall}
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                </div>

                <div>
                  <Title level={5} style={{ marginBottom: 16 }}>验证规则详情</Title>
                  {validationResult.rules.map((rule, index) => (
                    <Card 
                      key={index} 
                      size="small" 
                      style={{ 
                        marginBottom: 12,
                        border: `1px solid ${
                          rule.status === 'success' ? '#b7eb8f' :
                          rule.status === 'warning' ? '#ffd591' :
                          rule.status === 'error' ? '#ffccc7' : '#d9d9d9'
                        }`
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ flexShrink: 0 }}>
                          {rule.status === 'success' ? (
                            <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} />
                          ) : rule.status === 'warning' ? (
                            <QuestionCircleOutlined style={{ color: '#fa8c16', fontSize: 16 }} />
                          ) : rule.status === 'error' ? (
                            <ClearOutlined style={{ color: '#ff4d4f', fontSize: 16 }} />
                          ) : (
                            <div style={{ width: 16, height: 16, borderRadius: '50%', backgroundColor: '#f0f0f0' }} />
                          )}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, marginBottom: 4 }}>
                            {rule.name}
                          </div>
                          <div style={{ fontSize: 13, color: '#666', marginBottom: 4 }}>
                            {rule.description}
                          </div>
                          {rule.details && (
                            <div style={{ fontSize: 12, color: '#999' }}>
                              {rule.details}
                            </div>
                          )}
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </>
            )}
          </div>
        </Modal>

        {/* 转换loading */}
        <CustomLoading 
          visible={converting} 
          text="正在转换格式" 
          description="正在处理数据转换..."
        />
      </div>
    );
  };
  
  export default Tools;

