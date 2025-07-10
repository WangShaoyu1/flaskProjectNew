import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Select, DatePicker, Space, Spin } from 'antd';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { 
  BarChartOutlined, 
  LineChartOutlined, 
  PieChartOutlined,
  RadarChartOutlined 
} from '@ant-design/icons';

const { RangePicker } = DatePicker;

const DataVisualization = ({ 
  data, 
  type = 'bar', 
  title, 
  height = 300,
  loading = false,
  showControls = true 
}) => {
  const [chartType, setChartType] = useState(type);
  const [dateRange, setDateRange] = useState(null);

  // 颜色配置
  const colors = [
    '#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', 
    '#fa8c16', '#13c2c2', '#eb2f96', '#2f54eb', '#52c41a'
  ];

  // 渲染柱状图
  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="value" fill="#1890ff" />
        {data && data[0] && Object.keys(data[0]).filter(key => key !== 'name').map((key, index) => (
          <Bar key={key} dataKey={key} fill={colors[index % colors.length]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );

  // 渲染折线图
  const renderLineChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        {data && data[0] && Object.keys(data[0]).filter(key => key !== 'name').map((key, index) => (
          <Line 
            key={key} 
            type="monotone" 
            dataKey={key} 
            stroke={colors[index % colors.length]}
            strokeWidth={2}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );

  // 渲染饼图
  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          outerRadius={Math.min(height / 3, 100)}
          fill="#8884d8"
          dataKey="value"
        >
          {data && data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );

  // 渲染面积图
  const renderAreaChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Legend />
        {data && data[0] && Object.keys(data[0]).filter(key => key !== 'name').map((key, index) => (
          <Area 
            key={key}
            type="monotone" 
            dataKey={key} 
            stackId="1"
            stroke={colors[index % colors.length]}
            fill={colors[index % colors.length]}
            fillOpacity={0.6}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
  );

  // 渲染雷达图
  const renderRadarChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="subject" />
        <PolarRadiusAxis />
        <Radar
          name="Score"
          dataKey="A"
          stroke="#1890ff"
          fill="#1890ff"
          fillOpacity={0.3}
        />
        <Tooltip />
      </RadarChart>
    </ResponsiveContainer>
  );

  // 根据类型渲染图表
  const renderChart = () => {
    if (!data || data.length === 0) {
      return (
        <div style={{ 
          height, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: '#999'
        }}>
          暂无数据
        </div>
      );
    }

    switch (chartType) {
      case 'line':
        return renderLineChart();
      case 'pie':
        return renderPieChart();
      case 'area':
        return renderAreaChart();
      case 'radar':
        return renderRadarChart();
      default:
        return renderBarChart();
    }
  };

  return (
    <Card
      title={title}
      extra={showControls && (
        <Space>
          <Select
            value={chartType}
            onChange={setChartType}
            style={{ width: 120 }}
          >
            <Select.Option value="bar">
              <BarChartOutlined /> 柱状图
            </Select.Option>
            <Select.Option value="line">
              <LineChartOutlined /> 折线图
            </Select.Option>
            <Select.Option value="pie">
              <PieChartOutlined /> 饼图
            </Select.Option>
            <Select.Option value="area">
              <BarChartOutlined /> 面积图
            </Select.Option>
            <Select.Option value="radar">
              <RadarChartOutlined /> 雷达图
            </Select.Option>
          </Select>
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
            placeholder={['开始日期', '结束日期']}
          />
        </Space>
      )}
    >
      <Spin spinning={loading}>
        {renderChart()}
      </Spin>
    </Card>
  );
};

// 预定义的图表组件
export const TrainingTrendChart = ({ data, loading }) => (
  <DataVisualization
    data={data}
    type="line"
    title="训练趋势分析"
    height={300}
    loading={loading}
  />
);

export const IntentDistributionChart = ({ data, loading }) => (
  <DataVisualization
    data={data}
    type="pie"
    title="意图分布统计"
    height={300}
    loading={loading}
  />
);

export const AccuracyComparisonChart = ({ data, loading }) => (
  <DataVisualization
    data={data}
    type="bar"
    title="版本准确率对比"
    height={300}
    loading={loading}
  />
);

export const PerformanceRadarChart = ({ data, loading }) => (
  <DataVisualization
    data={data}
    type="radar"
    title="模型性能雷达图"
    height={300}
    loading={loading}
  />
);

export default DataVisualization; 