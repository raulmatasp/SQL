import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  ArcElement,
  ChartOptions,
} from 'chart.js';
import { Bar, Line, Pie, Doughnut } from 'react-chartjs-2';
import { aiService } from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  LineElement,
  PointElement,
  ArcElement
);

interface ChartSuggestion {
  chart_type: string;
  configuration: {
    xAxis: string;
    yAxis: string;
    title: string;
    [key: string]: any;
  };
  confidence: number;
}

interface ChartVisualizationProps {
  data: any[];
  queryText: string;
  onChartGenerated?: (success: boolean) => void;
}

const ChartVisualization: React.FC<ChartVisualizationProps> = ({
  data,
  queryText,
  onChartGenerated,
}) => {
  const [suggestions, setSuggestions] = useState<ChartSuggestion[]>([]);
  const [selectedChart, setSelectedChart] = useState<ChartSuggestion | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (data && data.length > 0) {
      generateChartSuggestions();
    }
  }, [data, queryText]);

  const generateChartSuggestions = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Take first few rows as sample
      const dataSample = data.slice(0, Math.min(10, data.length));
      
      const chartSuggestions = await aiService.suggestCharts(dataSample, queryText);
      setSuggestions(chartSuggestions);
      
      // Auto-select the highest confidence suggestion
      if (chartSuggestions.length > 0) {
        const bestSuggestion = chartSuggestions.reduce((best, current) => 
          current.confidence > best.confidence ? current : best
        );
        setSelectedChart(bestSuggestion);
      }
      
      onChartGenerated?.(true);
    } catch (err) {
      console.error('Chart suggestion failed:', err);
      setError('Failed to generate chart suggestions');
      onChartGenerated?.(false);
      
      // Fallback: create a simple chart suggestion based on data analysis
      createFallbackSuggestion();
    } finally {
      setIsLoading(false);
    }
  };

  const createFallbackSuggestion = () => {
    if (!data || data.length === 0) return;

    const columns = Object.keys(data[0]);
    const numericColumns = columns.filter(col => 
      data.some(row => typeof row[col] === 'number' && !isNaN(row[col]))
    );
    const textColumns = columns.filter(col => 
      col !== numericColumns[0] && typeof data[0][col] === 'string'
    );

    let chartType = 'bar';
    let xAxis = textColumns[0] || columns[0];
    let yAxis = numericColumns[0] || columns[1];

    // Determine chart type based on data characteristics
    if (numericColumns.length >= 2) {
      chartType = 'line';
    } else if (textColumns.length === 0) {
      chartType = 'pie';
      xAxis = columns[0];
      yAxis = columns[1];
    }

    const fallbackSuggestion: ChartSuggestion = {
      chart_type: chartType,
      configuration: {
        xAxis,
        yAxis,
        title: `${chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart`,
      },
      confidence: 0.7,
    };

    setSuggestions([fallbackSuggestion]);
    setSelectedChart(fallbackSuggestion);
  };

  const processChartData = (suggestion: ChartSuggestion) => {
    if (!data || data.length === 0) return null;

    const { chart_type, configuration } = suggestion;
    const { xAxis, yAxis, title } = configuration;

    if (chart_type === 'pie' || chart_type === 'doughnut') {
      // For pie charts, aggregate data by categories
      const aggregated: { [key: string]: number } = {};
      
      data.forEach(row => {
        const category = String(row[xAxis] || 'Unknown');
        const value = Number(row[yAxis]) || 0;
        aggregated[category] = (aggregated[category] || 0) + value;
      });

      return {
        labels: Object.keys(aggregated),
        datasets: [{
          label: yAxis,
          data: Object.values(aggregated),
          backgroundColor: [
            '#3B82F6', '#EF4444', '#10B981', '#F59E0B', 
            '#8B5CF6', '#EC4899', '#6B7280', '#84CC16'
          ].slice(0, Object.keys(aggregated).length),
          borderWidth: 1,
        }],
      };
    } else {
      // For bar/line charts
      const labels = data.map(row => String(row[xAxis] || 'Unknown'));
      const values = data.map(row => Number(row[yAxis]) || 0);

      return {
        labels,
        datasets: [{
          label: yAxis,
          data: values,
          backgroundColor: chart_type === 'line' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.8)',
          borderColor: '#3B82F6',
          borderWidth: 2,
          fill: chart_type === 'line' ? true : false,
        }],
      };
    }
  };

  const getChartOptions = (suggestion: ChartSuggestion): ChartOptions<any> => {
    const { chart_type, configuration } = suggestion;
    const { title } = configuration;

    const baseOptions: ChartOptions<any> = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: title,
          font: {
            size: 16,
            weight: 'bold',
          },
        },
        tooltip: {
          mode: 'index',
          intersect: false,
        },
      },
    };

    if (chart_type === 'line' || chart_type === 'bar') {
      return {
        ...baseOptions,
        scales: {
          x: {
            display: true,
            title: {
              display: true,
              text: configuration.xAxis,
            },
          },
          y: {
            display: true,
            title: {
              display: true,
              text: configuration.yAxis,
            },
          },
        },
        interaction: {
          intersect: false,
        },
      };
    }

    return baseOptions;
  };

  const renderChart = (suggestion: ChartSuggestion) => {
    const chartData = processChartData(suggestion);
    const options = getChartOptions(suggestion);
    
    if (!chartData) return null;

    switch (suggestion.chart_type) {
      case 'bar':
        return <Bar data={chartData} options={options} />;
      case 'line':
        return <Line data={chartData} options={options} />;
      case 'pie':
        return <Pie data={chartData} options={options} />;
      case 'doughnut':
        return <Doughnut data={chartData} options={options} />;
      default:
        return <Bar data={chartData} options={options} />;
    }
  };

  if (!data || data.length === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-medium text-gray-900">Data Visualization</h2>
        {isLoading && (
          <div className="text-sm text-gray-500">Generating charts...</div>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          {error}
        </div>
      )}

      {suggestions.length > 0 && (
        <>
          {/* Chart Type Selector */}
          <div className="mb-6">
            <div className="flex flex-wrap gap-2 mb-3">
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => setSelectedChart(suggestion)}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    selectedChart === suggestion
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {suggestion.chart_type.charAt(0).toUpperCase() + suggestion.chart_type.slice(1)}
                  <span className="ml-1 text-xs opacity-75">
                    ({Math.round(suggestion.confidence * 100)}%)
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Chart Display */}
          {selectedChart && (
            <div className="relative h-96 mb-4">
              {renderChart(selectedChart)}
            </div>
          )}

          {/* Chart Info */}
          {selectedChart && (
            <div className="text-sm text-gray-600 space-y-1">
              <div>
                <span className="font-medium">Chart Type:</span> {selectedChart.chart_type}
              </div>
              <div>
                <span className="font-medium">X-Axis:</span> {selectedChart.configuration.xAxis}
              </div>
              <div>
                <span className="font-medium">Y-Axis:</span> {selectedChart.configuration.yAxis}
              </div>
              <div>
                <span className="font-medium">Confidence:</span> {Math.round(selectedChart.confidence * 100)}%
              </div>
            </div>
          )}
        </>
      )}

      {!isLoading && suggestions.length === 0 && !error && (
        <div className="text-center text-gray-500 py-8">
          <div className="text-lg mb-2">No chart suggestions available</div>
          <p className="text-sm">The data format might not be suitable for visualization</p>
        </div>
      )}
    </div>
  );
};

export default ChartVisualization;