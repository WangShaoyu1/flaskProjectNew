import React, { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Modal, Form, Input, Select, message, 
  Row, Col, Statistic, List, Badge, Tabs, Alert, Popconfirm,
  Tag, Space, Tooltip, Steps, Timeline, Descriptions, Divider, App
} from 'antd';
import {
  BranchesOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  SwapOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  FileTextOutlined,
  DiffOutlined,
  StarOutlined,
  StarFilled,
  DownloadOutlined,
  UploadOutlined,
  CompareOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { versionAPI, trainingAPI, apiUtils } from '../api-v2';
import { formatLocalTime } from '../utils/timeUtils';
import { safeTableDataSource } from '../utils/dataSourceUtils';



const VersionManagement = ({ currentLibrary }) => {
  const [loading, setLoading] = useState(false);
  const [versions, setVersions] = useState([]);
  const [activeVersion, setActiveVersion] = useState(null);
  const [comparisonData, setComparisonData] = useState(null);
  
  // 模态框状态
  const [versionDetailModalVisible, setVersionDetailModalVisible] = useState(false);
  const [compareModalVisible, setCompareModalVisible] = useState(false);
  const [currentVersion, setCurrentVersion] = useState(null);
  
  // 筛选状态
  const [statusFilter, setStatusFilter] = useState('all');
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });

  // 检查是否选择了指令库
  if (!currentLibrary) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <BranchesOutlined style={{ fontSize: '64px', color: '#ccc', marginBottom: '16px' }} />
          <h3>请先选择指令库</h3>
          <p style={{ color: '#666' }}>在开始版本管理之前，请先在指令库管理页面选择一个指令库。</p>
        </div>
      </Card>
    );
  }

  // 获取版本列表
  const fetchVersions = async (params = {}) => {
    setLoading(true);
    try {
      const queryParams = {
        library_id: currentLibrary.id,
        page: pagination.current,
        size: pagination.pageSize,
        status_filter: statusFilter === 'all' ? null : statusFilter,
        ...params
      };
      
      const response = await versionAPI.getVersions(apiUtils.buildParams(queryParams));
      const { versions: versionList, total } = response.data;
      
      setVersions(versionList || []);
      setPagination(prev => ({ ...prev, total }));
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取版本列表失败'));
    } finally {
      setLoading(false);
    }
  };

  // 获取当前激活版本
  const fetchActiveVersion = async () => {
    try {
      const response = await versionAPI.getActiveVersion(currentLibrary.id);
      setActiveVersion(response.data.version);
    } catch (error) {
      console.error('获取激活版本失败:', error);
    }
  };

  useEffect(() => {
    if (currentLibrary) {
      fetchVersions();
      fetchActiveVersion();
    }
  }, [currentLibrary, pagination.current, pagination.pageSize, statusFilter]);

  // 激活版本
  const handleActivateVersion = async (versionId) => {
    try {
      setLoading(true);
      await versionAPI.activateVersion(versionId);
      message.success('版本激活成功');
      
      // 刷新数据
      fetchVersions();
      fetchActiveVersion();
    } catch (error) {
      message.error(apiUtils.handleError(error, '版本激活失败'));
    } finally {
      setLoading(false);
    }
  };

  // 查看版本详情
  const viewVersionDetail = async (version) => {
    try {
      const response = await versionAPI.getVersionDetail(version.id);
      setCurrentVersion(response.data);
      setVersionDetailModalVisible(true);
    } catch (error) {
      message.error(apiUtils.handleError(error, '获取版本详情失败'));
    }
  };

  // 删除版本
  const handleDeleteVersion = async (versionId) => {
    try {
      await versionAPI.deleteVersion(versionId);
      message.success('版本删除成功');
      fetchVersions();
      fetchActiveVersion();
    } catch (error) {
      message.error(apiUtils.handleError(error, '删除版本失败'));
    }
  };

  // 版本对比
  const handleVersionCompare = async (baseVersionId, compareVersionId) => {
    try {
      setLoading(true);
      const response = await versionAPI.compareVersions({
        library_id: currentLibrary.id,
        base_version_id: baseVersionId,
        compare_version_id: compareVersionId
      });
      
      setComparisonData(response.data);
      setCompareModalVisible(true);
    } catch (error) {
      message.error(apiUtils.handleError(error, '版本对比失败'));
    } finally {
      setLoading(false);
    }
  };

  // 筛选处理
  const handleStatusFilterChange = (status) => {
    setStatusFilter(status);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  // 版本表格列定义
  const versionColumns = [
    {
      title: '版本',
      dataIndex: 'version_number',
      key: 'version_number',
      width: 100,
      render: (version, record) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Tag color="blue" style={{ marginRight: 8 }}>v{version}</Tag>
          {record.is_active && (
            <StarFilled style={{ color: '#faad14', fontSize: '16px' }} />
          )}
        </div>
      ),
    },
    {
      title: '训练状态',
      dataIndex: 'training_status',
      key: 'training_status',
      width: 120,
      render: (status) => {
        const statusConfig = {
          'preparing': { color: 'processing', text: '准备中', icon: <ClockCircleOutlined /> },
          'training': { color: 'processing', text: '训练中', icon: <ClockCircleOutlined /> },
          'success': { color: 'success', text: '成功', icon: <CheckCircleOutlined /> },
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
      title: '模型信息',
      key: 'model_info',
      width: 200,
      render: (_, record) => (
        <div>
          <div>意图: {record.intent_count || 0} 个</div>
          <div>词槽: {record.slot_count || 0} 个</div>
          <div>样本: {record.training_data_count || 0} 条</div>
        </div>
      ),
    },
    {
      title: '训练时间',
      key: 'training_time',
      width: 200,
      render: (_, record) => (
        <div>
          <div>开始: {formatLocalTime(record.start_time)}</div>
          <div>完成: {formatLocalTime(record.complete_time)}</div>
          {record.start_time && record.complete_time && (
            <div>耗时: {Math.round((new Date(record.complete_time) - new Date(record.start_time)) / 60000)} 分钟</div>
          )}
        </div>
      ),
    },
    {
      title: '激活状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive) => (
        <Badge 
          status={isActive ? 'success' : 'default'} 
          text={isActive ? '已激活' : '未激活'} 
        />
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => viewVersionDetail(record)}
            />
          </Tooltip>
          
          {record.training_status === 'success' && !record.is_active && (
            <Tooltip title="激活版本">
              <Button
                type="text"
                icon={<PlayCircleOutlined />}
                onClick={() => handleActivateVersion(record.id)}
              />
            </Tooltip>
          )}
          
          <Tooltip title="版本对比">
            <Button
              type="text"
              icon={<SwapOutlined />}
              onClick={() => {
                // 这里可以打开版本选择对比框
                console.log('版本对比:', record.id);
              }}
            />
          </Tooltip>
          
          <Popconfirm
            title="确定要删除这个版本吗？"
            description="删除后将无法恢复，如果是激活版本将无法删除。"
            onConfirm={() => handleDeleteVersion(record.id)}
            okText="确定"
            cancelText="取消"
            disabled={record.is_active}
          >
            <Tooltip title={record.is_active ? '激活版本无法删除' : '删除版本'}>
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                disabled={record.is_active}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 分页处理
  const handleTableChange = (pagination) => {
    setPagination(pagination);
  };

  return (
    <div className="version-management">
      {/* 统计信息 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="总版本数"
              value={pagination.total}
              prefix={<BranchesOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="成功版本"
              value={versions.filter(v => v.training_status === 'success').length}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="失败版本"
              value={versions.filter(v => v.training_status === 'failed').length}
              prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="当前激活版本"
              value={activeVersion ? `v${activeVersion.version_number}` : '无'}
              prefix={<StarFilled style={{ color: '#faad14' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 当前激活版本信息 */}
      {activeVersion && (
        <Alert
          message={`当前激活版本: v${activeVersion.version_number}`}
          description={
            <div>
              状态: {activeVersion.training_status} | 
              意图数量: {activeVersion.intent_count} | 
              词槽数量: {activeVersion.slot_count} | 
              创建时间: {formatLocalTime(activeVersion.created_time)}
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
          action={
            <Button size="small" onClick={() => viewVersionDetail(activeVersion)}>
              查看详情
            </Button>
          }
        />
      )}

      {/* 操作栏 */}
      <Card style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <span>状态筛选:</span>
              <Select
                value={statusFilter}
                onChange={handleStatusFilterChange}
                style={{ width: 120 }}
              >
                <Select.Option value="all">全部</Select.Option>
                <Select.Option value="success">成功</Select.Option>
                <Select.Option value="failed">失败</Select.Option>
                <Select.Option value="training">训练中</Select.Option>
                <Select.Option value="preparing">准备中</Select.Option>
              </Select>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                icon={<SwapOutlined />}
                onClick={() => setCompareModalVisible(true)}
              >
                版本对比
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  fetchVersions();
                  fetchActiveVersion();
                }}
              >
                刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 版本时间轴 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={8}>
          <Card title="版本时间线">
            <Timeline>
              {versions.slice(0, 8).map((version) => (
                <Timeline.Item
                  key={version.id}
                  color={
                    version.training_status === 'success' ? 'green' : 
                    version.training_status === 'failed' ? 'red' : 'blue'
                  }
                  dot={
                    version.is_active ? <StarFilled style={{ color: '#faad14' }} /> :
                    version.training_status === 'success' ? <CheckCircleOutlined /> :
                    version.training_status === 'failed' ? <CloseCircleOutlined /> :
                    <ClockCircleOutlined />
                  }
                >
                  <div>
                    <strong>v{version.version_number}</strong>
                    {version.is_active && <Tag color="gold" style={{ marginLeft: 8 }}>激活</Tag>}
                    <Badge 
                      status={version.training_status === 'success' ? 'success' : 
                              version.training_status === 'failed' ? 'error' : 'processing'} 
                      text={version.training_status === 'success' ? '成功' : 
                            version.training_status === 'failed' ? '失败' : '进行中'}
                      style={{ marginLeft: 8 }}
                    />
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                                          {formatLocalTime(version.start_time) || '未开始'}
                  </div>
                  {version.intent_count && (
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      意图: {version.intent_count} | 词槽: {version.slot_count}
                    </div>
                  )}
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card title="版本性能对比图表">
            <div style={{ textAlign: 'center', padding: '60px', color: '#999' }}>
              <BarChartOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
              <h3>版本性能趋势图</h3>
              <p>性能对比图表功能开发中...</p>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 版本列表表格 */}
      <Card title={`版本列表 - ${currentLibrary.name}`}>
        <Table
          columns={versionColumns}
          dataSource={safeTableDataSource(versions)}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个版本`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* 版本详情模态框 */}
      <Modal
        title={`版本详情 - v${currentVersion?.version_number}`}
        open={versionDetailModalVisible}
        onCancel={() => setVersionDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {currentVersion && (
          <Tabs 
            defaultActiveKey="1"
            items={[
              {
                key: '1',
                label: '基本信息',
                children: (
                  <div>
                    <Descriptions bordered column={2}>
                      <Descriptions.Item label="版本号">v{currentVersion.version_number}</Descriptions.Item>
                      <Descriptions.Item label="训练状态">
                        <Badge 
                          status={currentVersion.training_status === 'success' ? 'success' : 
                                  currentVersion.training_status === 'failed' ? 'error' : 'processing'} 
                          text={currentVersion.training_status} 
                        />
                      </Descriptions.Item>
                      <Descriptions.Item label="意图数量">{currentVersion.intent_count}</Descriptions.Item>
                      <Descriptions.Item label="词槽数量">{currentVersion.slot_count}</Descriptions.Item>
                      <Descriptions.Item label="训练样本">{currentVersion.training_data_count}</Descriptions.Item>
                      <Descriptions.Item label="激活状态">
                        {currentVersion.is_active ? 
                          <Badge status="success" text="已激活" /> : 
                          <Badge status="default" text="未激活" />
                        }
                      </Descriptions.Item>
                      <Descriptions.Item label="开始时间">
                        {formatLocalTime(currentVersion.start_time)}
                      </Descriptions.Item>
                      <Descriptions.Item label="完成时间">
                        {formatLocalTime(currentVersion.complete_time)}
                      </Descriptions.Item>
                      <Descriptions.Item label="模型文件路径" span={2}>
                        {currentVersion.model_file_path || '-'}
                      </Descriptions.Item>
                    </Descriptions>

                    {currentVersion.training_status === 'success' && !currentVersion.is_active && (
                      <div style={{ marginTop: 16, textAlign: 'center' }}>
                        <Button
                          type="primary"
                          icon={<PlayCircleOutlined />}
                          onClick={() => {
                            handleActivateVersion(currentVersion.id);
                            setVersionDetailModalVisible(false);
                          }}
                        >
                          激活此版本
                        </Button>
                      </div>
                    )}
                  </div>
                )
              },
              {
                key: '2',
                label: '训练配置',
                children: (
                  <div style={{ padding: '20px', background: '#fafafa', borderRadius: 6 }}>
                    <h4>配置快照:</h4>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                      {currentVersion.config_snapshot || '暂无配置信息'}
                    </pre>
                  </div>
                )
              },
              {
                key: '3',
                label: '训练日志',
                children: (
                  <div style={{ padding: '20px', background: '#f6f6f6', borderRadius: 6, maxHeight: '400px', overflow: 'auto' }}>
                    <pre style={{ margin: 0, fontSize: '12px', whiteSpace: 'pre-wrap' }}>
                      {currentVersion.training_log || '暂无日志信息'}
                    </pre>
                  </div>
                )
              },
              {
                key: '4',
                label: '错误信息',
                children: (
                  currentVersion.error_message ? (
                    <Alert
                      message="训练错误信息"
                      description={
                        <div style={{ padding: '10px', background: '#fff2f0', borderRadius: 4 }}>
                          <pre style={{ margin: 0, fontSize: '12px', whiteSpace: 'pre-wrap' }}>
                            {currentVersion.error_message}
                          </pre>
                        </div>
                      }
                      type="error"
                      showIcon
                    />
                  ) : (
                    <div style={{ textAlign: 'center', padding: '50px', color: '#999' }}>
                      <CheckCircleOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                      <h3>无错误信息</h3>
                      <p>此版本训练过程中未发生错误</p>
                    </div>
                  )
                )
              }
            ]}
          />
        )}
      </Modal>

      {/* 版本对比模态框 */}
      <Modal
        title="版本对比分析"
        open={compareModalVisible}
        onCancel={() => setCompareModalVisible(false)}
        footer={null}
        width={900}
      >
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <DiffOutlined style={{ fontSize: '48px', color: '#ccc', marginBottom: '16px' }} />
          <h3>版本对比功能</h3>
          <p style={{ color: '#666' }}>版本对比分析功能开发中...</p>
          <Space>
            <Select placeholder="选择基准版本" style={{ width: 200 }}>
              {versions.filter(v => v.training_status === 'success').map(v => (
                <Select.Option key={v.id} value={v.id}>
                  v{v.version_number}
                </Select.Option>
              ))}
            </Select>
            <span>vs</span>
            <Select placeholder="选择对比版本" style={{ width: 200 }}>
              {versions.filter(v => v.training_status === 'success').map(v => (
                <Select.Option key={v.id} value={v.id}>
                  v{v.version_number}
                </Select.Option>
              ))}
            </Select>
          </Space>
          <div style={{ marginTop: 24 }}>
            <Button type="primary" icon={<DiffOutlined />}>
              开始对比
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default VersionManagement; 