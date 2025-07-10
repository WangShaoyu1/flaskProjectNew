import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Button,
  Select,
  Slider,
  Space,
  message,
  Typography,
  Progress,
  List,
  Avatar,
  Tooltip,
  Modal,
  Tabs,
  Input,
  Popconfirm,
  Upload,
  Table,
  Divider
} from 'antd';
import {
  SoundOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  SettingOutlined,
  CloudOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DeleteOutlined,
  ClearOutlined,
  UploadOutlined,
  EyeOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import apiService from '../services/api';
import { convertSpeechRate, playAudio, downloadFile, storage } from '../utils';

const { Option } = Select;
const { Text, Title } = Typography;
const { TabPane } = Tabs;
const { Dragger } = Upload;

const VoiceSynthesis = ({ translatedText, sourceText }) => {
  const [voiceType, setVoiceType] = useState('girl');
  const [speechRate, setSpeechRate] = useState(1.0);
  const [voices, setVoices] = useState([]);
  const [synthesizing, setSynthesizing] = useState(false);
  const [previewing, setPreviewing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState('');
  const [audioFiles, setAudioFiles] = useState([]);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [aliyunToken, setAliyunToken] = useState('');
  const [testingConnection, setTestingConnection] = useState(false);

  // 批量上传相关状态
  const [batchData, setBatchData] = useState(null);
  const [batchProcessing, setBatchProcessing] = useState(false);
  const [batchPreviewVisible, setBatchPreviewVisible] = useState(false);
  const [processedData, setProcessedData] = useState([]);
  const [batchGenerating, setBatchGenerating] = useState(false);
  const [testMode, setTestMode] = useState(false); // 默认关闭测试模式（处理全部数据）

  // 批量下载相关状态
  const [batchDownloading, setBatchDownloading] = useState(false);

  useEffect(() => {
    loadVoices();
    loadSettings();
  }, []);

  const loadVoices = async () => {
    const result = await apiService.getSupportedVoices();
    if (result.success) {
      setVoices(result.voices);
    }
  };

  const loadSettings = async () => {
    // 加载阿里云配置
    const result = await apiService.getAliyunConfig();
    if (result.success) {
      setAliyunToken(result.token || '');
    }
  };

  const handleVoiceTypeChange = (value) => {
    setVoiceType(value);
    if (value === 'aitong') {
      message.info('已选择艾彤音色，使用阿里云TTS服务。如遇问题请检查阿里云Token配置。', 6);
    }
  };

  const handleSpeechRateChange = (value) => {
    setSpeechRate(value);
  };

  // 验证JSON文件格式
  const validateJsonFile = (jsonData) => {
    if (!jsonData || typeof jsonData !== 'object') {
      throw new Error('JSON文件格式无效');
    }

    if (!jsonData.data || !Array.isArray(jsonData.data)) {
      throw new Error('JSON文件必须包含data数组字段');
    }

    if (jsonData.data.length === 0) {
      throw new Error('data数组不能为空');
    }

    // 验证每个数据项
    jsonData.data.forEach((item, index) => {
      if (!item || typeof item !== 'object') {
        throw new Error(`第${index + 1}项数据格式无效`);
      }

      if (!item.chinese || typeof item.chinese !== 'string' || !item.chinese.trim()) {
        throw new Error(`第${index + 1}项缺少有效的中文文本`);
      }

      if (item.english !== undefined && typeof item.english !== 'string') {
        throw new Error(`第${index + 1}项英文文本格式无效`);
      }
    });

    return true;
  };

  // 处理批量上传的JSON数据
  const processBatchData = async (jsonData) => {
    setBatchProcessing(true);
    setProgress(0);
    setProgressText('正在处理批量数据...');

    try {
      const processedItems = [];
      const allItems = jsonData.data;
      
      // 测试模式只处理前5个
      const items = testMode ? allItems.slice(0, 5) : allItems;
      
      if (testMode && allItems.length > 5) {
        message.info(`测试模式：只处理前5个数据项（共${allItems.length}个）`, 4);
      }

      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        setProgress(Math.round((i / items.length) * 100));
        setProgressText(`正在处理第 ${i + 1}/${items.length} 项数据...`);

                 const processedItem = {
           index: i + 1,
           chinese: item.chinese.trim(),
           english: item.english ? item.english.trim() : '',
           chineseVoice: 'aitong', // 中文默认艾彤
           englishVoice: 'girl',   // 英文默认女声
           speechRate: 1.0,        // 默认语速（UI显示为1.0，艾彤会转换为0）
           id: Date.now() + i      // 唯一ID
         };

        // 如果英文为空，调用翻译API
        if (!processedItem.english) {
          setProgressText(`正在翻译第 ${i + 1} 项："${item.chinese}"...`);
          
          const translateResult = await apiService.translateText(
            item.chinese, 
            'zh', 
            'en'
          );

          if (translateResult.success) {
            processedItem.english = translateResult.translation;
            processedItem.translated = true; // 标记为自动翻译
          } else {
            processedItem.english = `Translation failed: ${translateResult.error}`;
            processedItem.translationError = true;
            message.warning(`第${i + 1}项翻译失败: ${translateResult.error}`);
          }
        }

        processedItems.push(processedItem);
      }

      setProgress(100);
      setProgressText('批量数据处理完成！');
      setProcessedData(processedItems);
      
      message.success(`成功处理 ${processedItems.length} 项数据`);
      
      // 3秒后清除进度
      setTimeout(() => {
        setProgress(0);
        setProgressText('');
      }, 3000);

    } catch (error) {
      message.error(`批量数据处理失败: ${error.message}`);
      setProgress(0);
      setProgressText('');
    } finally {
      setBatchProcessing(false);
    }
  };

  // 重新处理批量数据（当测试模式切换时）
  const reprocessBatchData = async () => {
    if (batchData) {
      await processBatchData(batchData);
    }
  };

  // 处理文件上传
  const handleFileUpload = {
    name: 'file',
    multiple: false,
    accept: '.json',
    beforeUpload: (file) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const jsonData = JSON.parse(e.target.result);
          validateJsonFile(jsonData);
          setBatchData(jsonData);
          await processBatchData(jsonData);
        } catch (error) {
          message.error(`文件解析失败: ${error.message}`);
        }
      };
      reader.readAsText(file);
      return false; // 阻止自动上传
    },
    onDrop(e) {
      console.log('Dropped files', e.dataTransfer.files);
    },
  };

  // 批量生成音频
  const handleBatchGenerate = async () => {
    if (!processedData || processedData.length === 0) {
      message.warning('没有可生成的数据');
      return;
    }

    setBatchGenerating(true);
    setProgress(0);
    setProgressText('开始批量生成音频...');

    try {
      const generatedFiles = [];
      const totalItems = processedData.length * 2; // 中英文各一个
      let currentIndex = 0;

      for (let i = 0; i < processedData.length; i++) {
        const item = processedData[i];
        
        // 生成中文音频
        setProgress(Math.round((currentIndex / totalItems) * 100));
        setProgressText(`正在生成中文音频 ${i + 1}/${processedData.length}: "${item.chinese}"`);

        const chineseResult = await apiService.synthesizeVoice(item.chinese, {
          voiceType: item.chineseVoice,
          speechRate: convertSpeechRate(item.chineseVoice, item.speechRate),
          sourceLine: `${item.index}_${item.chinese}`
        });

        if (chineseResult.success) {
          const chineseFile = {
            ...chineseResult.file,
            id: `${item.id}_chinese`,
            // 使用后端返回的实际文件名，而不是自己构造
            name: chineseResult.file.name,
            displayName: `${item.index}_${item.chinese}.wav`, // 用于显示的名称
            type: 'chinese',
            originalIndex: item.index
          };
          generatedFiles.push(chineseFile);
        } else {
          message.warning(`第${item.index}项中文音频生成失败: ${chineseResult.error}`);
        }

        currentIndex++;

        // 生成英文音频
        setProgress(Math.round((currentIndex / totalItems) * 100));
        setProgressText(`正在生成英文音频 ${i + 1}/${processedData.length}: "${item.english}"`);

        const englishResult = await apiService.synthesizeVoice(item.english, {
          voiceType: item.englishVoice,
          speechRate: convertSpeechRate(item.englishVoice, item.speechRate),
          sourceLine: `${item.index}_en_${item.english}`
        });

        if (englishResult.success) {
          const englishFile = {
            ...englishResult.file,
            id: `${item.id}_english`,
            // 使用后端返回的实际文件名，而不是自己构造
            name: englishResult.file.name,
            displayName: `${item.index}_en_${item.english}.wav`, // 用于显示的名称
            type: 'english',
            originalIndex: item.index
          };
          generatedFiles.push(englishFile);
        } else {
          message.warning(`第${item.index}项英文音频生成失败: ${englishResult.error}`);
        }

        currentIndex++;
      }

      setProgress(100);
      setProgressText('批量音频生成完成！');

      // 添加到现有音频列表
      setAudioFiles(prev => [...prev, ...generatedFiles]);
      
      message.success(`批量生成完成！共生成 ${generatedFiles.length} 个音频文件`);
      setBatchPreviewVisible(false);

      // 3秒后清除进度
      setTimeout(() => {
        setProgress(0);
        setProgressText('');
      }, 3000);

    } catch (error) {
      message.error(`批量生成失败: ${error.message}`);
      setProgress(0);
      setProgressText('');
    } finally {
      setBatchGenerating(false);
    }
  };

  const handleSynthesize = async () => {
    if (!translatedText.trim()) {
      message.warning('请先翻译文本再生成语音');
      return;
    }

    setSynthesizing(true);
    setProgress(0);
    setProgressText('准备语音合成...');

    try {
      // 分割文本行
      const lines = translatedText.split('\n').filter(line => line.trim());
      const sourceLines = sourceText.split('\n').filter(line => line.trim());

      if (lines.length === 0) {
        throw new Error('没有有效的文本行可以合成');
      }

      const files = [];
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        const sourceLine = sourceLines[i] || `文本${i + 1}`;

        if (line) {
          setProgress(Math.round((i / lines.length) * 100));
          setProgressText(`正在合成第 ${i + 1}/${lines.length} 条语音...`);

          const convertedRate = convertSpeechRate(voiceType, speechRate);
          const result = await apiService.synthesizeVoice(line, {
            voiceType,
            speechRate: convertedRate,
            sourceLine
          });

          if (result.success) {
            files.push({
              ...result.file,
              id: Date.now() + i // 添加唯一ID用于删除
            });
            message.success(`第 ${i + 1} 条语音合成成功`, 2);
          } else {
            message.warning(`第 ${i + 1} 条语音合成失败: ${result.error}`);
          }
        }
      }

      setProgress(100);
      setProgressText('语音合成完成！');

      if (files.length > 0) {
        setAudioFiles(files);
        message.success(`成功生成 ${files.length} 个语音文件`);
      } else {
        message.warning('没有成功生成任何语音文件');
      }
    } catch (error) {
      message.error(`语音合成出错: ${error.message}`);
    } finally {
      setSynthesizing(false);
      setTimeout(() => {
        setProgress(0);
        setProgressText('');
      }, 3000);
    }
  };

  const handlePreview = async () => {
    if (!translatedText.trim()) {
      message.warning('请先翻译文本再预览语音');
      return;
    }

    const firstLine = translatedText.split('\n')[0].trim();
    if (!firstLine) {
      message.warning('没有有效的文本可以预览');
      return;
    }

    setPreviewing(true);
    try {
      const convertedRate = convertSpeechRate(voiceType, speechRate);
      const result = await apiService.previewVoice(firstLine, {
        voiceType,
        speechRate: convertedRate
      });

      if (result.success) {
        message.info('正在加载预览音频...');
        await playAudio(result.audioUrl);
        message.success('预览播放完成');
      } else {
        message.error(`预览失败: ${result.error}`);
      }
    } catch (error) {
      message.error(`预览出错: ${error.message}`);
    } finally {
      setPreviewing(false);
    }
  };

  const handleDownload = (file) => {
    downloadFile(file.downloadUrl, file.name);
    message.success('文件下载已开始');
  };

  const handleDownloadAll = async () => {
    if (audioFiles.length === 0) {
      message.warning('没有可下载的文件');
      return;
    }

    setBatchDownloading(true);
    
    // 显示详细的进度信息
    const hideLoading = message.loading(`正在打包 ${audioFiles.length} 个文件为ZIP压缩包，请稍候...`, 0);

    try {
      // 提取文件名
      const filenames = audioFiles.map(file => file.name);
      
      // 调用批量下载API
      const result = await apiService.batchDownloadZip(filenames);
      
      hideLoading();
      
      if (result.success) {
        message.success(`ZIP文件下载成功：${result.filename}`, 3);
      } else {
        message.error(`ZIP下载失败: ${result.error}`);
        // 如果ZIP下载失败，回退到逐个下载
        message.info('正在尝试逐个下载文件...');
        audioFiles.forEach(file => {
          downloadFile(file.downloadUrl, file.name);
        });
      }
    } catch (error) {
      hideLoading();
      message.error(`批量下载出错: ${error.message}`);
      // 如果出错，回退到逐个下载
      message.info('正在尝试逐个下载文件...');
      audioFiles.forEach(file => {
        downloadFile(file.downloadUrl, file.name);
      });
    } finally {
      setBatchDownloading(false);
    }
  };

  // 删除单个文件
  const handleDeleteFile = (fileId) => {
    const updatedFiles = audioFiles.filter(file => file.id !== fileId);
    setAudioFiles(updatedFiles);
    message.success('文件已删除');
  };

  // 清空所有文件和批量数据
  const handleClearAll = () => {
    // 清空音频文件列表
    setAudioFiles([]);
    
    // 清空批量数据相关状态
    setProcessedData([]);
    setBatchData(null);
    
    // 重置批量处理相关状态
    setBatchGenerating(false);
    setBatchPreviewVisible(false);
    setBatchProcessing(false);
    
    message.success('已清空所有数据（音频文件和批量数据）');
  };

  // 下载完善后的JSON文件（完整版）
  const handleDownloadProcessedJson = () => {
    if (!processedData || processedData.length === 0) {
      message.warning('没有处理后的数据可下载');
      return;
    }

    try {
      // 构建完善后的JSON数据
      const enhancedData = {
        data: processedData.map(item => ({
          index: item.index,
          chinese: item.chinese,
          english: item.english,
          translated: item.translated || false,
          translationError: item.translationError || false,
          chineseVoice: item.chineseVoice,
          englishVoice: item.englishVoice,
          speechRate: item.speechRate
        })),
        metadata: {
          totalItems: processedData.length,
          testMode: testMode,
          originalDataCount: batchData ? batchData.data.length : 0,
          processedAt: new Date().toISOString(),
          settings: {
            defaultChineseVoice: 'aitong',
            defaultEnglishVoice: 'female',
            defaultSpeechRate: speechRate
          }
        }
      };

      // 创建下载链接
      const jsonString = JSON.stringify(enhancedData, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      
      // 生成文件名
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const modePrefix = testMode ? 'test' : 'full';
      const filename = `processed_voice_data_${modePrefix}_${timestamp}.json`;
      
      // 触发下载
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      message.success(`已下载完整版JSON文件: ${filename}`);
    } catch (error) {
      console.error('下载JSON文件失败:', error);
      message.error('下载JSON文件失败，请重试');
    }
  };

  // 下载简单版本的JSON文件（仅包含index、chinese、english）
  const handleDownloadSimpleJson = () => {
    if (!processedData || processedData.length === 0) {
      message.warning('没有处理后的数据可下载');
      return;
    }

    try {
      // 构建简单版本的JSON数据
      const simpleData = {
        data: processedData.map(item => ({
          index: item.index,
          chinese: item.chinese,
          english: item.english
        }))
      };

      // 创建下载链接
      const jsonString = JSON.stringify(simpleData, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      
      // 生成文件名
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const modePrefix = testMode ? 'test' : 'full';
      const filename = `simple_voice_data_${modePrefix}_${timestamp}.json`;
      
      // 触发下载
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      message.success(`已下载简单版JSON文件: ${filename}`);
    } catch (error) {
      console.error('下载简单版JSON文件失败:', error);
      message.error('下载简单版JSON文件失败，请重试');
    }
  };

  const handleTestConnection = async () => {
    if (!aliyunToken.trim()) {
      message.warning('请先填写Token');
      return;
    }

    setTestingConnection(true);
    try {
      const result = await apiService.testAliyunConnection(aliyunToken);
      if (result.success) {
        message.success('阿里云TTS连接测试成功');
      } else {
        message.error(`连接测试失败: ${result.error}`);
      }
    } catch (error) {
      message.error(`测试出错: ${error.message}`);
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      const result = await apiService.setAliyunConfig(aliyunToken);
      if (result.success) {
        message.success('阿里云TTS配置保存成功');
        setSettingsVisible(false);
      } else {
        message.error(`保存失败: ${result.error}`);
      }
    } catch (error) {
      message.error(`保存出错: ${error.message}`);
    }
  };

  const getVoiceIcon = (voiceCode) => {
    switch (voiceCode) {
      case 'girl':
        return '👩';
      case 'boy':
        return '👨';
      case 'danbao':
        return '🥚';
      case 'aitong':
        return '🎭';
      default:
        return '🎵';
    }
  };

  // 批量数据预览表格列定义
  const batchDataColumns = [
    {
      title: '序号',
      dataIndex: 'index',
      key: 'index',
      width: 60,
      align: 'center'
    },
    {
      title: '中文文本',
      dataIndex: 'chinese',
      key: 'chinese',
      width: 200,
      ellipsis: {
        showTitle: false
      },
      render: (text) => (
        <Tooltip 
          placement="topLeft" 
          title={text}
          overlayStyle={{ maxWidth: '400px' }}
          overlayInnerStyle={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
        >
          <span>{text}</span>
        </Tooltip>
      )
    },
    {
      title: '英文文本',
      dataIndex: 'english',
      key: 'english',
      width: 200,
      ellipsis: {
        showTitle: false
      },
              render: (text, record) => (
          <Tooltip 
            placement="topLeft" 
            title={text}
            overlayStyle={{ maxWidth: '400px' }}
            overlayInnerStyle={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
          >
            <span style={{ color: record.translated ? '#52c41a' : 'inherit' }}>
              {text}
              {record.translated && <span style={{ marginLeft: 4, fontSize: '12px' }}>(已翻译)</span>}
              {record.translationError && <span style={{ marginLeft: 4, fontSize: '12px', color: '#ff4d4f' }}>(翻译失败)</span>}
            </span>
          </Tooltip>
        )
    },
    {
      title: '中文发音人',
      dataIndex: 'chineseVoice',
      key: 'chineseVoice',
      width: 100,
      render: (voice) => (
        <Space align="center">
          <span>{getVoiceIcon(voice)}</span>
          <span>艾彤</span>
        </Space>
      )
    },
    {
      title: '英文发音人',
      dataIndex: 'englishVoice',
      key: 'englishVoice',
      width: 100,
      render: (voice) => (
        <Space align="center">
          <span>{getVoiceIcon(voice)}</span>
          <span>女声</span>
        </Space>
      )
    },
    {
      title: '语速',
      dataIndex: 'speechRate',
      key: 'speechRate',
      width: 80,
      align: 'center',
      render: (rate) => `${rate}x`
    }
  ];

  return (
    <>
      <Card
        title={
          <Space align="center">
            <SoundOutlined />
            语音合成
          </Space>
        }
        extra={
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={() => setSettingsVisible(true)}
          >
            设置
          </Button>
        }
      >
        {/* 批量上传区域 */}
        <Card 
          type="inner" 
          title={
            <Space align="center">
              <FileTextOutlined />
              批量语音生成
            </Space>
          }
          style={{ marginBottom: 16 }}
        >
          <Row gutter={16}>
            <Col span={16}>
              <Dragger {...handleFileUpload} style={{ marginBottom: 16 }}>
                <p className="ant-upload-drag-icon">
                  <UploadOutlined />
                </p>
                <p className="ant-upload-text">点击或拖拽JSON文件到此区域上传</p>
                                 <p className="ant-upload-hint">
                   支持单个JSON文件上传，格式：{`{"data": [{"chinese": "文本", "english": "文本"}]}`}
                 </p>
              </Dragger>
            </Col>
            <Col span={8}>
              <Space direction="vertical" style={{ width: '100%' }}>
                                 {processedData.length > 0 && batchData && (
                   <Button
                     type="primary"
                     icon={<EyeOutlined />}
                     onClick={() => setBatchPreviewVisible(true)}
                     style={{ width: '100%', marginBottom: 8 }}
                   >
                     查看处理结果 ({processedData.length}项)
                   </Button>
                 )}
                 {processedData.length > 0 && batchData && (
                   <Button
                     icon={<DownloadOutlined />}
                     onClick={handleDownloadProcessedJson}
                     style={{ width: '100%', marginBottom: 8 }}
                   >
                     下载完整版JSON
                   </Button>
                 )}
                 {processedData.length > 0 && batchData && (
                   <Button
                     icon={<DownloadOutlined />}
                     onClick={handleDownloadSimpleJson}
                     style={{ width: '100%' }}
                   >
                     下载简单版JSON
                   </Button>
                 )}
                 <div style={{ marginTop: 8 }}>
                   <label style={{ display: 'flex', alignItems: 'center', fontSize: '12px' }}>
                     <input
                       type="checkbox"
                       checked={testMode}
                       onChange={async (e) => {
                         const newTestMode = e.target.checked;
                         setTestMode(newTestMode);
                         
                         // 如果已有数据，重新处理
                         if (batchData) {
                           message.info(`切换到${newTestMode ? '测试' : '完整'}模式，正在重新处理数据...`);
                           setTimeout(() => reprocessBatchData(), 100);
                         }
                       }}
                       style={{ marginRight: 6 }}
                     />
                     测试模式（仅处理前5个数据项）
                   </label>
                 </div>
                 <Text type="secondary" style={{ fontSize: '12px' }}>
                   • 中文默认使用艾彤发音人<br/>
                   • 英文默认使用女声发音人<br/>
                   • 空的英文字段将自动翻译<br/>
                   • 语速默认为1.0倍速<br/>
                   • 可随时切换测试模式重新处理数据<br/>
                   • 支持下载完整版和简单版JSON文件
                 </Text>
              </Space>
            </Col>
          </Row>
        </Card>

        <Divider />

        {/* 原有的单个语音合成区域 */}
        <Title level={5}>单个语音合成</Title>
        
        {/* 语音参数设置 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>发音人</Text>
              <Select
                value={voiceType}
                onChange={handleVoiceTypeChange}
                style={{ width: '100%' }}
                placeholder="选择发音人"
              >
                {voices.map(voice => (
                  <Option key={voice.code} value={voice.code}>
                                    <Space align="center">
                  <span>{getVoiceIcon(voice.code)}</span>
                  {voice.name}
                  {voice.code === 'aitong' && (
                    <CloudOutlined style={{ color: '#1890ff' }} />
                  )}
                </Space>
                  </Option>
                ))}
              </Select>
            </Space>
          </Col>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>
                语速: {speechRate}x
                {voiceType === 'aitong' && (
                  <Text type="secondary" style={{ marginLeft: 8, fontSize: '12px' }}>
                    (阿里云TTS: {convertSpeechRate(voiceType, speechRate)})
                  </Text>
                )}
              </Text>
              <Slider
                min={0.5}
                max={2.0}
                step={0.1}
                value={speechRate}
                onChange={handleSpeechRateChange}
                marks={{
                  0.5: '0.5x',
                  1.0: '1.0x',
                  1.5: '1.5x',
                  2.0: '2.0x'
                }}
              />
              {voiceType === 'aitong' && (
                <Text type="secondary" style={{ fontSize: '11px' }}>
                  艾彤音色语速范围：-500~500，默认0（对应1.0x）
                </Text>
              )}
            </Space>
          </Col>
        </Row>

        {/* 操作按钮 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={12}>
            <Button
              type="primary"
              size="large"
              icon={<SoundOutlined />}
              onClick={handleSynthesize}
              loading={synthesizing}
              disabled={!translatedText.trim()}
              style={{ width: '100%' }}
            >
              {synthesizing ? '生成中...' : '生成语音'}
            </Button>
          </Col>
          <Col span={12}>
            <Button
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={handlePreview}
              loading={previewing}
              disabled={!translatedText.trim()}
              style={{ width: '100%' }}
            >
              {previewing ? '预览中...' : '预览语音'}
            </Button>
          </Col>
        </Row>

        {/* 进度条 */}
        {(progress > 0 || progressText) && (
          <div style={{ marginBottom: 16 }}>
            <Progress
              percent={progress}
              status={progress === 100 ? 'success' : 'active'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <Text type="secondary">{progressText}</Text>
          </div>
        )}

        {/* 音频文件列表 */}
        {audioFiles.length > 0 && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <Text strong>生成的语音文件 ({audioFiles.length})</Text>
              <Space align="center">
                <Button
                  type="primary"
                  size="small"
                  icon={<DownloadOutlined />}
                  onClick={handleDownloadAll}
                  loading={batchDownloading}
                >
                  {batchDownloading ? '打包中...' : '批量下载'}
                </Button>
                <Tooltip title="批量下载将自动打包为ZIP文件，避免多次选择保存位置">
                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                </Tooltip>
                <Popconfirm
                  title="确定要清空所有语音文件吗？"
                  description="此操作不可撤销，但不会删除已下载的文件。"
                  onConfirm={handleClearAll}
                  okText="确定"
                  cancelText="取消"
                  okType="danger"
                >
                  <Button
                    danger
                    size="small"
                    icon={<ClearOutlined />}
                  >
                    一键清空
                  </Button>
                </Popconfirm>
              </Space>
            </div>
            <List
              dataSource={audioFiles}
              renderItem={(file, index) => (
                <List.Item
                  actions={[
                    <Tooltip title="播放音频">
                      <Button
                        type="text"
                        icon={<PlayCircleOutlined />}
                        onClick={() => playAudio(file.url)}
                      />
                    </Tooltip>,
                    <Tooltip title="下载文件">
                      <Button
                        type="text"
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownload(file)}
                      />
                    </Tooltip>,
                    <Popconfirm
                      title="确定要删除这个语音文件吗？"
                      description="此操作不可撤销，但不会删除已下载的文件。"
                      onConfirm={() => handleDeleteFile(file.id)}
                      okText="确定"
                      cancelText="取消"
                      okType="danger"
                    >
                      <Tooltip title="删除文件">
                        <Button
                          type="text"
                          danger
                          icon={<DeleteOutlined />}
                        />
                      </Tooltip>
                    </Popconfirm>
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      <Avatar style={{ 
                        backgroundColor: file.type === 'chinese' ? '#52c41a' : '#1890ff' 
                      }}>
                        {file.type === 'chinese' ? '中' : file.type === 'english' ? '英' : index + 1}
                      </Avatar>
                    }
                    title={file.displayName || file.name}
                    description={
                      <Space align="center">
                        <Text type="secondary">大小: {file.size}</Text>
                        <Text type="secondary">时长: {file.duration}</Text>
                        {file.type && (
                          <Text type="secondary">
                            类型: {file.type === 'chinese' ? '中文' : file.type === 'english' ? '英文' : '单个'}
                          </Text>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </div>
        )}
      </Card>

      {/* 批量数据预览模态框 */}
      <Modal
        title={
          <Space align="center">
            <EyeOutlined />
            批量数据预览
          </Space>
        }
        open={batchPreviewVisible}
        onCancel={() => setBatchPreviewVisible(false)}
        width={1000}
        footer={[
          <Button key="cancel" onClick={() => setBatchPreviewVisible(false)}>
            取消
          </Button>,
          <Button
            key="generate"
            type="primary"
            icon={<ThunderboltOutlined />}
            loading={batchGenerating}
            onClick={handleBatchGenerate}
          >
            {batchGenerating ? '生成中...' : `一键生成音频${testMode ? ' (测试模式)' : ''}`}
          </Button>
        ]}
      >
                 <div style={{ marginBottom: 16 }}>
           <Text type="secondary">
             共 {processedData.length} 项数据，将生成 {processedData.length * 2} 个音频文件（中英文各一个）
           </Text>
           {testMode && batchData && batchData.data.length > 5 && (
             <div style={{ marginTop: 8, padding: 8, backgroundColor: '#fff7e6', border: '1px solid #ffd591', borderRadius: 4 }}>
               <Text type="warning" style={{ fontSize: '12px' }}>
                 ⚠️ 当前为测试模式，仅显示前5个数据项。关闭测试模式可处理全部 {batchData.data.length} 个数据项。
               </Text>
             </div>
           )}
           {!testMode && batchData && batchData.data.length > 5 && (
             <div style={{ marginTop: 8, padding: 8, backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 4 }}>
               <Text type="success" style={{ fontSize: '12px' }}>
                 ✅ 完整模式：正在处理全部 {batchData.data.length} 个数据项
               </Text>
             </div>
           )}
         </div>
        <Table
          dataSource={processedData}
          columns={batchDataColumns}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条数据`
          }}
          scroll={{ y: 400 }}
        />
      </Modal>

      {/* 设置模态框 */}
      <Modal
        title="语音合成设置"
        open={settingsVisible}
        onCancel={() => setSettingsVisible(false)}
        footer={null}
        width={600}
      >
        <Tabs defaultActiveKey="aliyun">
          <TabPane tab="阿里云TTS" key="aliyun">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Token配置</Text>
                <div style={{ marginTop: 8 }}>
                  <Input.TextArea
                    value={aliyunToken}
                    onChange={(e) => setAliyunToken(e.target.value)}
                    placeholder="请输入阿里云TTS Token"
                    rows={3}
                  />
                </div>
                <div style={{ marginTop: 8 }}>
                  <Space align="center">
                    <Button
                      type="primary"
                      icon={<CheckCircleOutlined />}
                      onClick={handleTestConnection}
                      loading={testingConnection}
                    >
                      测试连接
                    </Button>
                    <Button
                      type="default"
                      onClick={handleSaveSettings}
                    >
                      保存配置
                    </Button>
                  </Space>
                </div>
              </div>
              
              <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f6f8fa', borderRadius: 6 }}>
                <Text type="secondary">
                  <ExclamationCircleOutlined style={{ marginRight: 8 }} />
                  <strong>使用说明：</strong>
                </Text>
                <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                  <li>Token有效期为12小时，过期后需要重新配置</li>
                  <li>艾彤音色使用阿里云TTS服务，需要正确配置Token</li>
                  <li>其他音色（女声、男声、蛋宝）使用Google TTS服务</li>
                  <li>语速范围：1.0x-2.0x（艾彤音色会自动转换为阿里云格式）</li>
                </ul>
              </div>
            </Space>
          </TabPane>
        </Tabs>
      </Modal>
    </>
  );
};

export default VoiceSynthesis; 