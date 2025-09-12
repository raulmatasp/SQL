import React, { useState, useCallback, useEffect } from 'react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Line, Pie } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface Widget {
  id: string;
  type: 'chart' | 'table' | 'metric' | 'text' | 'filter';
  title: string;
  config: any;
  position: { x: number; y: number; w: number; h: number };
  data?: any[];
  query?: string;
}

interface DashboardConfig {
  id: string;
  name: string;
  description?: string;
  widgets: Widget[];
  layout: 'grid' | 'free';
  theme: 'light' | 'dark';
  autoRefresh?: number;
}

const WIDGET_TYPES = [
  { type: 'chart', label: 'Chart', icon: '📊' },
  { type: 'table', label: 'Table', icon: '📋' },
  { type: 'metric', label: 'Metric', icon: '📈' },
  { type: 'text', label: 'Text', icon: '📝' },
  { type: 'filter', label: 'Filter', icon: '🔍' },
];

const CHART_TYPES = [
  { value: 'bar', label: 'Bar Chart' },
  { value: 'line', label: 'Line Chart' },
  { value: 'pie', label: 'Pie Chart' },
];

const DraggableWidget: React.FC<{
  widget: Widget;
  onUpdate: (id: string, updates: Partial<Widget>) => void;
  onDelete: (id: string) => void;
  isEditing: boolean;
}> = ({ widget, onUpdate, onDelete, isEditing }) => {
  const [, drag] = useDrag(() => ({
    type: 'widget',
    item: { id: widget.id },
  }));

  const [isConfigOpen, setIsConfigOpen] = useState(false);

  const renderWidget = () => {
    switch (widget.type) {
      case 'chart':
        return renderChart();
      case 'table':
        return renderTable();
      case 'metric':
        return renderMetric();
      case 'text':
        return renderText();
      case 'filter':
        return renderFilter();
      default:
        return <div>Unknown widget type</div>;
    }
  };

  const renderChart = () => {
    if (!widget.data || widget.data.length === 0) {
      return <div className="flex items-center justify-center h-full text-gray-500">No data</div>;
    }

    const chartData = {
      labels: widget.data.map((item: any) => item[widget.config.xAxis] || ''),
      datasets: [
        {
          label: widget.config.yAxis || 'Value',
          data: widget.data.map((item: any) => item[widget.config.yAxis] || 0),
          backgroundColor: widget.config.colors || ['rgba(54, 162, 235, 0.6)'],
          borderColor: widget.config.borderColors || ['rgba(54, 162, 235, 1)'],
          borderWidth: 1,
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: widget.title,
        },
      },
    };

    switch (widget.config.chartType) {
      case 'line':
        return <Line data={chartData} options={options} />;
      case 'pie':
        return <Pie data={chartData} options={options} />;
      default:
        return <Bar data={chartData} options={options} />;
    }
  };

  const renderTable = () => {
    if (!widget.data || widget.data.length === 0) {
      return <div className="text-gray-500">No data</div>;
    }

    const columns = widget.config.columns || Object.keys(widget.data[0]);
    
    return (
      <div className="overflow-auto h-full">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((column: string) => (
                <th key={column} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {widget.data.slice(0, widget.config.maxRows || 10).map((row: any, index: number) => (
              <tr key={index}>
                {columns.map((column: string) => (
                  <td key={column} className="px-4 py-2 whitespace-nowrap text-sm">
                    {row[column]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderMetric = () => {
    const value = widget.config.value || 0;
    const previousValue = widget.config.previousValue || 0;
    const change = ((value - previousValue) / previousValue * 100).toFixed(1);
    const isPositive = parseFloat(change) >= 0;

    return (
      <div className="flex flex-col justify-center items-center h-full">
        <div className="text-3xl font-bold text-gray-900">{value.toLocaleString()}</div>
        <div className="text-sm text-gray-500">{widget.config.subtitle || widget.title}</div>
        {previousValue > 0 && (
          <div className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? '↗' : '↘'} {change}%
          </div>
        )}
      </div>
    );
  };

  const renderText = () => {
    return (
      <div className="p-4 h-full overflow-auto">
        <div className="prose prose-sm">
          <div dangerouslySetInnerHTML={{ __html: widget.config.content || '' }} />
        </div>
      </div>
    );
  };

  const renderFilter = () => {
    return (
      <div className="p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {widget.title}
        </label>
        <select className="w-full px-3 py-2 border border-gray-300 rounded-md">
          <option value="">All</option>
          {widget.config.options?.map((option: any) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    );
  };

  return (
    <div
      ref={drag}
      className={`
        relative bg-white rounded-lg shadow border
        ${isEditing ? 'cursor-move hover:shadow-lg' : ''}
      `}
      style={{
        left: widget.position.x,
        top: widget.position.y,
        width: widget.position.w,
        height: widget.position.h,
        position: 'absolute',
      }}
    >
      {isEditing && (
        <div className="absolute top-2 right-2 flex space-x-1 z-10">
          <button
            onClick={() => setIsConfigOpen(true)}
            className="p-1 bg-blue-500 text-white rounded hover:bg-blue-600"
            title="Configure"
          >
            ⚙️
          </button>
          <button
            onClick={() => onDelete(widget.id)}
            className="p-1 bg-red-500 text-white rounded hover:bg-red-600"
            title="Delete"
          >
            ❌
          </button>
        </div>
      )}
      
      <div className="p-4 h-full">
        {renderWidget()}
      </div>

      {isConfigOpen && (
        <WidgetConfigModal
          widget={widget}
          onSave={(updates) => {
            onUpdate(widget.id, updates);
            setIsConfigOpen(false);
          }}
          onClose={() => setIsConfigOpen(false)}
        />
      )}
    </div>
  );
};

const WidgetConfigModal: React.FC<{
  widget: Widget;
  onSave: (updates: Partial<Widget>) => void;
  onClose: () => void;
}> = ({ widget, onSave, onClose }) => {
  const [config, setConfig] = useState(widget);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-medium mb-4">Configure Widget</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              type="text"
              value={config.title}
              onChange={(e) => setConfig({ ...config, title: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          {widget.type === 'chart' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Chart Type</label>
                <select
                  value={config.config.chartType || 'bar'}
                  onChange={(e) => setConfig({
                    ...config,
                    config: { ...config.config, chartType: e.target.value }
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  {CHART_TYPES.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Query</label>
                <textarea
                  value={config.query || ''}
                  onChange={(e) => setConfig({ ...config, query: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows={3}
                  placeholder="SELECT * FROM table_name"
                />
              </div>
            </>
          )}

          {widget.type === 'text' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
              <textarea
                value={config.config.content || ''}
                onChange={(e) => setConfig({
                  ...config,
                  config: { ...config.config, content: e.target.value }
                })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                rows={4}
              />
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(config)}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

const DashboardBuilder: React.FC = () => {
  const [dashboard, setDashboard] = useState<DashboardConfig>({
    id: 'new-dashboard',
    name: 'New Dashboard',
    widgets: [],
    layout: 'free',
    theme: 'light',
  });
  
  const [isEditing, setIsEditing] = useState(true);
  const [selectedWidgetType, setSelectedWidgetType] = useState<string>('');

  const [, drop] = useDrop(() => ({
    accept: 'widget',
    drop: (item: { id: string }, monitor) => {
      const offset = monitor.getSourceClientOffset();
      if (offset) {
        moveWidget(item.id, offset.x, offset.y);
      }
    },
  }));

  const addWidget = useCallback((type: string) => {
    const newWidget: Widget = {
      id: `widget-${Date.now()}`,
      type: type as any,
      title: `New ${type}`,
      config: {},
      position: { x: 100, y: 100, w: 300, h: 200 },
    };

    setDashboard(prev => ({
      ...prev,
      widgets: [...prev.widgets, newWidget],
    }));
  }, []);

  const updateWidget = useCallback((id: string, updates: Partial<Widget>) => {
    setDashboard(prev => ({
      ...prev,
      widgets: prev.widgets.map(widget =>
        widget.id === id ? { ...widget, ...updates } : widget
      ),
    }));
  }, []);

  const deleteWidget = useCallback((id: string) => {
    setDashboard(prev => ({
      ...prev,
      widgets: prev.widgets.filter(widget => widget.id !== id),
    }));
  }, []);

  const moveWidget = useCallback((id: string, x: number, y: number) => {
    updateWidget(id, {
      position: { ...dashboard.widgets.find(w => w.id === id)!.position, x, y }
    });
  }, [dashboard.widgets, updateWidget]);

  const saveDashboard = useCallback(async () => {
    try {
      // Save to backend
      const response = await fetch('/api/dashboards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dashboard),
      });
      
      if (response.ok) {
        alert('Dashboard saved successfully!');
      } else {
        alert('Failed to save dashboard');
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('Failed to save dashboard');
    }
  }, [dashboard]);

  const exportDashboard = useCallback(() => {
    const dataStr = JSON.stringify(dashboard, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${dashboard.name.replace(/\s+/g, '-').toLowerCase()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }, [dashboard]);

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-screen flex flex-col bg-gray-100">
        {/* Header */}
        <div className="bg-white shadow-sm border-b p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <input
                type="text"
                value={dashboard.name}
                onChange={(e) => setDashboard(prev => ({ ...prev, name: e.target.value }))}
                className="text-xl font-semibold bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2"
              />
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className={`px-3 py-1 rounded text-sm ${
                    isEditing ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'
                  }`}
                >
                  {isEditing ? 'Exit Edit' : 'Edit'}
                </button>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={saveDashboard}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              >
                Save
              </button>
              <button
                onClick={exportDashboard}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Export
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          {isEditing && (
            <div className="w-64 bg-white shadow-sm border-r p-4 overflow-y-auto">
              <h3 className="text-lg font-medium mb-4">Add Widgets</h3>
              
              <div className="space-y-2">
                {WIDGET_TYPES.map(widget => (
                  <button
                    key={widget.type}
                    onClick={() => addWidget(widget.type)}
                    className="w-full p-3 text-left border rounded-lg hover:bg-gray-50 flex items-center space-x-2"
                  >
                    <span className="text-lg">{widget.icon}</span>
                    <span>{widget.label}</span>
                  </button>
                ))}
              </div>

              <div className="mt-8">
                <h4 className="text-md font-medium mb-2">Dashboard Settings</h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-gray-700 mb-1">Theme</label>
                    <select
                      value={dashboard.theme}
                      onChange={(e) => setDashboard(prev => ({ ...prev, theme: e.target.value as any }))}
                      className="w-full px-2 py-1 border rounded text-sm"
                    >
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-700 mb-1">Auto Refresh (seconds)</label>
                    <input
                      type="number"
                      value={dashboard.autoRefresh || ''}
                      onChange={(e) => setDashboard(prev => ({ 
                        ...prev, 
                        autoRefresh: e.target.value ? parseInt(e.target.value) : undefined 
                      }))}
                      className="w-full px-2 py-1 border rounded text-sm"
                      placeholder="0 = disabled"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Canvas */}
          <div 
            ref={drop}
            className="flex-1 relative overflow-auto"
            style={{ minHeight: '100%' }}
          >
            {dashboard.widgets.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-500">
                <div className="text-center">
                  <div className="text-4xl mb-4">📊</div>
                  <div className="text-lg mb-2">No widgets yet</div>
                  <div className="text-sm">
                    {isEditing ? 'Add widgets from the sidebar to get started' : 'Switch to edit mode to add widgets'}
                  </div>
                </div>
              </div>
            ) : (
              dashboard.widgets.map(widget => (
                <DraggableWidget
                  key={widget.id}
                  widget={widget}
                  onUpdate={updateWidget}
                  onDelete={deleteWidget}
                  isEditing={isEditing}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </DndProvider>
  );
};

export default DashboardBuilder;