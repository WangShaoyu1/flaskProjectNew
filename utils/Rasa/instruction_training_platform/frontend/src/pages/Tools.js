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
  Input
} from 'antd';
import { 
  UploadOutlined, 
  DownloadOutlined, 
  ToolOutlined,
  DatabaseOutlined,
  ExportOutlined,
  ImportOutlined
} from '@ant-design/icons';
import { toolsAPI } from '../api';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;

const Tools = () => {
  const [uploadLoading, setUploadLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [importModalVisible, setImportModalVisible] = useState(false);
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
      
      // 创建下载链接
      const dataStr = JSON.stringify(response.data.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      
      const link = document.createElement('a');
      link.href = url;
      link.download = `training_data_${format}_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      message.success('数据导出成功');
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
              <Card size="small" title="数据统计">
                <Button type="dashed" style={{ width: '100%', height: 60 }}>
                  <DatabaseOutlined style={{ fontSize: 20 }} />
                  <div>查看数据统计信息</div>
                </Button>
              </Card>

              <Card size="small" title="数据清理">
                <Button type="dashed" style={{ width: '100%', height: 60 }}>
                  <ToolOutlined style={{ fontSize: 20 }} />
                  <div>清理重复和无效数据</div>
                </Button>
              </Card>

              <Card size="small" title="数据验证">
                <Button type="dashed" style={{ width: '100%', height: 60 }}>
                  <DatabaseOutlined style={{ fontSize: 20 }} />
                  <div>验证数据格式和完整性</div>
                </Button>
              </Card>
            </Space>
          </Card>
        </TabPane>
      </Tabs>

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
    </div>
  );
};

export default Tools;

