import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Input,
  Button,
  Select,
  Space,
  message,
  Typography,
  Tooltip,
  Spin
} from 'antd';
import {
  TranslationOutlined,
  SwapOutlined,
  ClearOutlined,
  CopyOutlined,
  EditOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import apiService from '../services/api';
import { copyToClipboard, pasteFromClipboard, debounce } from '../utils';

const { TextArea } = Input;
const { Option } = Select;
const { Text } = Typography;

const TranslationPanel = ({ onTranslationChange }) => {
  const [sourceText, setSourceText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [sourceLang, setSourceLang] = useState('zh');
  const [targetLang, setTargetLang] = useState('en');
  const [loading, setLoading] = useState(false);
  const [languages, setLanguages] = useState([]);

  // 防抖处理翻译结果变化
  const debouncedTranslationChange = debounce((text) => {
    if (onTranslationChange) {
      onTranslationChange(text);
    }
  }, 300);

  useEffect(() => {
    loadLanguages();
  }, []);

  useEffect(() => {
    debouncedTranslationChange(translatedText);
  }, [translatedText]);

  const loadLanguages = async () => {
    const result = await apiService.getSupportedLanguages();
    if (result.success) {
      setLanguages(result.languages);
    }
  };

  const handleTranslate = async () => {
    if (!sourceText.trim()) {
      message.warning('请输入要翻译的文本');
      return;
    }

    setLoading(true);
    try {
      const result = await apiService.translateText(sourceText, sourceLang, targetLang);
      
      if (result.success) {
        setTranslatedText(result.translation);
        message.success('翻译完成！');
      } else {
        message.error(`翻译失败: ${result.error}`);
      }
    } catch (error) {
      message.error(`翻译出错: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSwapLanguages = () => {
    // 交换语言
    const tempLang = sourceLang;
    setSourceLang(targetLang);
    setTargetLang(tempLang);
    
    // 交换文本
    const tempText = sourceText;
    setSourceText(translatedText);
    setTranslatedText(tempText);
    
    message.info('语言已交换');
  };

  const handleClearSource = () => {
    setSourceText('');
    message.info('源文本已清空');
  };

  const handleClearResult = () => {
    setTranslatedText('');
    message.info('翻译结果已清空');
  };

  const handleCopyResult = async () => {
    if (!translatedText) {
      message.warning('没有可复制的内容');
      return;
    }

    const success = await copyToClipboard(translatedText);
    if (success) {
      message.success('已复制到剪贴板');
    } else {
      message.error('复制失败');
    }
  };

  const handlePaste = async () => {
    const text = await pasteFromClipboard();
    if (text) {
      setSourceText(text);
      message.success('已粘贴文本');
    } else {
      message.warning('粘贴失败，请手动粘贴');
    }
  };

  const handleKeyDown = (e) => {
    if (e.ctrlKey || e.metaKey) {
      switch (e.key) {
        case 'Enter':
          e.preventDefault();
          handleTranslate();
          break;
        case 'r':
          e.preventDefault();
          handleSwapLanguages();
          break;
        default:
          break;
      }
    }
  };

  return (
    <Card
      title={
        <Space>
          <TranslationOutlined />
          文本翻译
        </Space>
      }
      extra={
        <Space>
          <Text type="secondary">
            快捷键: Ctrl+Enter 翻译, Ctrl+R 交换语言
          </Text>
        </Space>
      }
    >
      {/* 语言选择 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={10}>
          <Select
            value={sourceLang}
            onChange={setSourceLang}
            style={{ width: '100%' }}
            placeholder="选择源语言"
          >
            {languages.map(lang => (
              <Option key={lang.code} value={lang.code}>
                {lang.name}
              </Option>
            ))}
          </Select>
        </Col>
        <Col span={4} style={{ textAlign: 'center' }}>
          <Button
            type="text"
            icon={<SwapOutlined />}
            onClick={handleSwapLanguages}
            style={{ width: '100%' }}
          >
            交换
          </Button>
        </Col>
        <Col span={10}>
          <Select
            value={targetLang}
            onChange={setTargetLang}
            style={{ width: '100%' }}
            placeholder="选择目标语言"
          >
            {languages.map(lang => (
              <Option key={lang.code} value={lang.code}>
                {lang.name}
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      {/* 文本输入区域 */}
      <Row gutter={16}>
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text strong>源文本</Text>
              <Space>
                <Text type="secondary">{sourceText.length} 字符</Text>
                <Button
                  type="text"
                  size="small"
                  icon={<FileTextOutlined />}
                  onClick={handlePaste}
                  title="粘贴文本"
                />
                <Button
                  type="text"
                  size="small"
                  icon={<ClearOutlined />}
                  onClick={handleClearSource}
                  title="清空"
                />
              </Space>
            </div>
            <TextArea
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="请输入要翻译的文本..."
              rows={8}
              maxLength={5000}
              showCount
            />
          </Space>
        </Col>
        
        <Col span={12}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text strong>
                翻译结果
                <Tooltip title="翻译结果可以编辑，支持按换行符分隔的批量语音生成">
                  <EditOutlined style={{ marginLeft: 8, color: '#1890ff' }} />
                </Tooltip>
              </Text>
              <Space>
                <Text type="secondary">{translatedText.length} 字符</Text>
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={handleCopyResult}
                  title="复制结果"
                />
                <Button
                  type="text"
                  size="small"
                  icon={<ClearOutlined />}
                  onClick={handleClearResult}
                  title="清空"
                />
              </Space>
            </div>
            <TextArea
              value={translatedText}
              onChange={(e) => setTranslatedText(e.target.value)}
              placeholder="翻译结果将显示在这里...&#10;&#10;💡 提示：您可以直接编辑翻译结果&#10;支持按换行符分隔进行批量语音生成"
              rows={8}
              maxLength={5000}
              showCount
            />
          </Space>
        </Col>
      </Row>

      {/* 操作按钮 */}
      <Row style={{ marginTop: 16 }}>
        <Col span={24} style={{ textAlign: 'center' }}>
          <Button
            type="primary"
            size="large"
            icon={<TranslationOutlined />}
            onClick={handleTranslate}
            loading={loading}
            disabled={!sourceText.trim()}
          >
            {loading ? '翻译中...' : '翻译'}
          </Button>
        </Col>
      </Row>
    </Card>
  );
};

export default TranslationPanel; 