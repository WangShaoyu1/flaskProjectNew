import numpy as np
import plotly.graph_objects as go

# 数据列表
data = [
    1840, 1835, 1830, 1816, 1805, 1795, 1762, 1762, 1751, 1749, 1747, 1744, 1741, 1740,
    1736, 1734, 1728, 1727, 1724, 1723, 1721, 1713, 1698, 1697, 1695, 1693, 1692, 1689,
    1688, 1685, 1684, 1683, 1683, 1682, 1681, 1680, 1676, 1663, 1659, 1658, 1658, 1655,
    1653, 1650, 1647, 1647, 1643, 1640, 1639, 1639, 1635, 1632, 1630, 1625, 1623, 1623,
    1623, 1622, 1619, 1618, 1612, 1610, 1604, 1604, 1598, 1595, 1588, 1588, 1581, 1578,
    1569, 1567, 1557, 1555, 1548, 1544, 1529, 1526, 1504, 1500, 1496, 1490, 1487, 1478,
    1463, 1447, 1431, 1421, 1415, 1410, 1376, 1372, 1366, 1361, 1350, 1323, 1292, 1118,
    1041
]

# 将数据转换为NumPy数组
data = np.array(data)

# 设定阈值范围和步长
thresholds = np.arange(900, 1650, 50)

# 计算每个阈值下大于该阈值的概率，并转换为百分比
probabilities_percentage = [(data > threshold).mean() * 100 for threshold in thresholds]

# 创建交互式图表
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=thresholds,
    y=probabilities_percentage,
    mode='lines+markers',
    text=[f'Threshold: {threshold}<br>Probability: {prob:.2f}%' for threshold, prob in zip(thresholds, probabilities_percentage)],
    hoverinfo='text'
))

fig.update_layout(
    title='Probability of Data Points Greater Than Threshold (Percentage)',
    xaxis_title='Threshold',
    yaxis_title='Probability (%)',
    xaxis=dict(tickmode='linear', tick0=900, dtick=50),
    yaxis=dict(tickmode='linear', tick0=0, dtick=10),
    hovermode='closest'
)

fig.show()
