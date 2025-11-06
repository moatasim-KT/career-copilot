/**
 * Data Visualization Components
 * 
 * Enterprise-grade chart components using Recharts with responsive design,
 * accessibility, and customizable themes.
 * 
 * @module components/charts/DataVisualization
 */

'use client';

import {
    LineChart,
    Line,
    BarChart,
    Bar,
    PieChart,
    Pie,
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    Cell,
} from 'recharts';

import { tokens } from '@/lib/designTokens';

export interface ChartDataPoint {
    name: string;
    value?: number;
    [key: string]: string | number | undefined;
}

export interface ChartProps {
    data: ChartDataPoint[];
    height?: number;
    colors?: string[];
    className?: string;
}

const DEFAULT_COLORS = [
    tokens.colors.primary[500],
    tokens.colors.secondary[500],
    tokens.colors.info.DEFAULT,
    tokens.colors.success.DEFAULT,
    tokens.colors.warning.DEFAULT,
    tokens.colors.error.DEFAULT,
];

/**
 * Custom Tooltip Component
 */
function CustomTooltip({ active, payload, label }: any) {
    if (!active || !payload?.length) return null;

    return (
        <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
            <p className="mb-2 font-semibold text-gray-900">{label}</p>
            {payload.map((entry: any, index: number) => (
                <div key={index} className="flex items-center gap-2">
                    <div
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: entry.color }}
                    />
                    <span className="text-sm text-gray-600">{entry.name}:</span>
                    <span className="text-sm font-medium text-gray-900">
                        {typeof entry.value === 'number'
                            ? entry.value.toLocaleString()
                            : entry.value}
                    </span>
                </div>
            ))}
        </div>
    );
}

/**
 * Line Chart Component
 * 
 * @example
 * ```tsx
 * <LineChartComponent
 *   data={[
 *     { name: 'Jan', applications: 12, interviews: 3 },
 *     { name: 'Feb', applications: 19, interviews: 5 },
 *   ]}
 *   dataKeys={['applications', 'interviews']}
 * />
 * ```
 */
export function LineChartComponent({
    data,
    dataKeys,
    height = 300,
    colors = DEFAULT_COLORS,
    className = '',
}: ChartProps & { dataKeys: string[] }) {
    return (
        <div className={`w-full ${className}`}>
            <ResponsiveContainer width="100%" height={height}>
                <LineChart
                    data={data}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" stroke={tokens.colors.border.DEFAULT} />
                    <XAxis dataKey="name" stroke={tokens.colors.text.secondary} />
                    <YAxis stroke={tokens.colors.text.secondary} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    {dataKeys.map((key, index) => (
                        <Line
                            key={key}
                            type="monotone"
                            dataKey={key}
                            stroke={colors[index % colors.length]}
                            strokeWidth={2}
                            dot={{ r: 4 }}
                            activeDot={{ r: 6 }}
                        />
                    ))}
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}

/**
 * Bar Chart Component
 * 
 * @example
 * ```tsx
 * <BarChartComponent
 *   data={[
 *     { name: 'Week 1', applications: 5 },
 *     { name: 'Week 2', applications: 8 },
 *   ]}
 *   dataKeys={['applications']}
 * />
 * ```
 */
export function BarChartComponent({
    data,
    dataKeys,
    height = 300,
    colors = DEFAULT_COLORS,
    className = '',
}: ChartProps & { dataKeys: string[] }) {
    return (
        <div className={`w-full ${className}`}>
            <ResponsiveContainer width="100%" height={height}>
                <BarChart
                    data={data}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                    <CartesianGrid strokeDasharray="3 3" stroke={tokens.colors.border.DEFAULT} />
                    <XAxis dataKey="name" stroke={tokens.colors.text.secondary} />
                    <YAxis stroke={tokens.colors.text.secondary} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    {dataKeys.map((key, index) => (
                        <Bar
                            key={key}
                            dataKey={key}
                            fill={colors[index % colors.length]}
                            radius={[8, 8, 0, 0]}
                        />
                    ))}
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}

/**
 * Pie Chart Component
 * 
 * @example
 * ```tsx
 * <PieChartComponent
 *   data={[
 *     { name: 'Applied', value: 45 },
 *     { name: 'Interviewing', value: 15 },
 *     { name: 'Offered', value: 5 },
 *   ]}
 * />
 * ```
 */
export function PieChartComponent({
    data,
    height = 300,
    colors = DEFAULT_COLORS,
    className = '',
}: ChartProps) {
    const RADIAN = Math.PI / 180;
    const renderCustomizedLabel = ({
        cx,
        cy,
        midAngle,
        innerRadius,
        outerRadius,
        percent,
    }: any) => {
        const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);

        return (
            <text
                x={x}
                y={y}
                fill="white"
                textAnchor={x > cx ? 'start' : 'end'}
                dominantBaseline="central"
                className="text-sm font-semibold"
            >
                {`${(percent * 100).toFixed(0)}%`}
            </text>
        );
    };

    return (
        <div className={`w-full ${className}`}>
            <ResponsiveContainer width="100%" height={height}>
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={renderCustomizedLabel}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                        ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                </PieChart>
            </ResponsiveContainer>
        </div>
    );
}

/**
 * Area Chart Component
 * 
 * @example
 * ```tsx
 * <AreaChartComponent
 *   data={[
 *     { name: 'Jan', applications: 12, interviews: 3 },
 *     { name: 'Feb', applications: 19, interviews: 5 },
 *   ]}
 *   dataKeys={['applications', 'interviews']}
 * />
 * ```
 */
export function AreaChartComponent({
    data,
    dataKeys,
    height = 300,
    colors = DEFAULT_COLORS,
    className = '',
}: ChartProps & { dataKeys: string[] }) {
    return (
        <div className={`w-full ${className}`}>
            <ResponsiveContainer width="100%" height={height}>
                <AreaChart
                    data={data}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                    <defs>
                        {dataKeys.map((key, index) => (
                            <linearGradient
                                key={key}
                                id={`color-${key}`}
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >
                                <stop
                                    offset="5%"
                                    stopColor={colors[index % colors.length]}
                                    stopOpacity={0.8}
                                />
                                <stop
                                    offset="95%"
                                    stopColor={colors[index % colors.length]}
                                    stopOpacity={0.1}
                                />
                            </linearGradient>
                        ))}
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={tokens.colors.border.DEFAULT} />
                    <XAxis dataKey="name" stroke={tokens.colors.text.secondary} />
                    <YAxis stroke={tokens.colors.text.secondary} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    {dataKeys.map((key, index) => (
                        <Area
                            key={key}
                            type="monotone"
                            dataKey={key}
                            stroke={colors[index % colors.length]}
                            fillOpacity={1}
                            fill={`url(#color-${key})`}
                        />
                    ))}
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
}

/**
 * Multi-Chart Dashboard Component
 * 
 * @example
 * ```tsx
 * <ChartDashboard
 *   charts={[
 *     {
 *       type: 'line',
 *       title: 'Applications Over Time',
 *       data: monthlyData,
 *       dataKeys: ['applications'],
 *     },
 *     {
 *       type: 'pie',
 *       title: 'Status Distribution',
 *       data: statusData,
 *     },
 *   ]}
 * />
 * ```
 */
export function ChartDashboard({
    charts,
    className = '',
}: {
    charts: Array<{
        type: 'line' | 'bar' | 'pie' | 'area';
        title: string;
        data: ChartDataPoint[];
        dataKeys?: string[];
        height?: number;
    }>;
    className?: string;
}) {
    return (
        <div className={`grid gap-6 md:grid-cols-2 ${className}`}>
            {charts.map((chart, index) => (
                <div
                    key={index}
                    className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
                >
                    <h3 className="mb-4 text-lg font-semibold text-gray-900">
                        {chart.title}
                    </h3>
                    {chart.type === 'line' && chart.dataKeys && (
                        <LineChartComponent
                            data={chart.data}
                            dataKeys={chart.dataKeys}
                            height={chart.height}
                        />
                    )}
                    {chart.type === 'bar' && chart.dataKeys && (
                        <BarChartComponent
                            data={chart.data}
                            dataKeys={chart.dataKeys}
                            height={chart.height}
                        />
                    )}
                    {chart.type === 'pie' && (
                        <PieChartComponent data={chart.data} height={chart.height} />
                    )}
                    {chart.type === 'area' && chart.dataKeys && (
                        <AreaChartComponent
                            data={chart.data}
                            dataKeys={chart.dataKeys}
                            height={chart.height}
                        />
                    )}
                </div>
            ))}
        </div>
    );
}
