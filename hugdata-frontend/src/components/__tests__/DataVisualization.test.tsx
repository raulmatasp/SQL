import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import DataVisualization from '../DataVisualization';

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Bar: ({ data }: any) => <div data-testid="bar-chart">{JSON.stringify(data)}</div>,
  Line: ({ data }: any) => <div data-testid="line-chart">{JSON.stringify(data)}</div>,
  Pie: ({ data }: any) => <div data-testid="pie-chart">{JSON.stringify(data)}</div>,
}));

describe('DataVisualization Component', () => {
  const mockData = [
    { id: 1, name: 'John Doe', age: 25, department: 'Engineering', salary: 75000 },
    { id: 2, name: 'Jane Smith', age: 30, department: 'Marketing', salary: 65000 },
    { id: 3, name: 'Bob Johnson', age: 35, department: 'Engineering', salary: 85000 },
    { id: 4, name: 'Alice Wilson', age: 28, department: 'Sales', salary: 55000 },
  ];

  test('renders visualization options', () => {
    render(<DataVisualization data={mockData} />);
    
    expect(screen.getByText(/chart type/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('Table')).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Bar Chart' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Line Chart' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Pie Chart' })).toBeInTheDocument();
  });

  test('displays data as table by default', () => {
    render(<DataVisualization data={mockData} />);
    
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    expect(screen.getByText('Engineering')).toBeInTheDocument();
    expect(screen.getByText('Marketing')).toBeInTheDocument();
  });

  test('renders table headers correctly', () => {
    render(<DataVisualization data={mockData} />);
    
    expect(screen.getByText('id')).toBeInTheDocument();
    expect(screen.getByText('name')).toBeInTheDocument();
    expect(screen.getByText('age')).toBeInTheDocument();
    expect(screen.getByText('department')).toBeInTheDocument();
    expect(screen.getByText('salary')).toBeInTheDocument();
  });

  test('switches to bar chart view', () => {
    render(<DataVisualization data={mockData} />);
    
    const chartSelect = screen.getByDisplayValue('Table');
    fireEvent.change(chartSelect, { target: { value: 'bar' } });
    
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  test('switches to line chart view', () => {
    render(<DataVisualization data={mockData} />);
    
    const chartSelect = screen.getByDisplayValue('Table');
    fireEvent.change(chartSelect, { target: { value: 'line' } });
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  test('switches to pie chart view', () => {
    render(<DataVisualization data={mockData} />);
    
    const chartSelect = screen.getByDisplayValue('Table');
    fireEvent.change(chartSelect, { target: { value: 'pie' } });
    
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  test('shows column selector for chart configuration', () => {
    render(<DataVisualization data={mockData} />);
    
    const chartSelect = screen.getByDisplayValue('Table');
    fireEvent.change(chartSelect, { target: { value: 'bar' } });
    
    expect(screen.getByText(/x-axis/i)).toBeInTheDocument();
    expect(screen.getByText(/y-axis/i)).toBeInTheDocument();
  });

  test('handles empty data gracefully', () => {
    render(<DataVisualization data={[]} />);
    
    expect(screen.getByText(/no data to display/i)).toBeInTheDocument();
  });

  test('handles data with missing fields', () => {
    const incompleteData = [
      { id: 1, name: 'John' },
      { id: 2, age: 30 },
      { name: 'Jane', department: 'Marketing' },
    ];
    
    render(<DataVisualization data={incompleteData} />);
    
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('John')).toBeInTheDocument();
    expect(screen.getByText('Marketing')).toBeInTheDocument();
  });

  test('formats numeric data in table', () => {
    render(<DataVisualization data={mockData} />);
    
    expect(screen.getByText('75,000')).toBeInTheDocument();
    expect(screen.getByText('65,000')).toBeInTheDocument();
    expect(screen.getByText('85,000')).toBeInTheDocument();
  });

  test('provides data export functionality', () => {
    render(<DataVisualization data={mockData} />);
    
    expect(screen.getByRole('button', { name: /export csv/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /export json/i })).toBeInTheDocument();
  });

  test('handles CSV export', () => {
    // Mock URL.createObjectURL and document.createElement
    const mockCreateObjectURL = jest.fn(() => 'mock-url');
    const mockClick = jest.fn();
    const mockRemove = jest.fn();
    
    global.URL.createObjectURL = mockCreateObjectURL;
    const mockAnchor = {
      href: '',
      download: '',
      click: mockClick,
      remove: mockRemove,
    };
    jest.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any);

    render(<DataVisualization data={mockData} />);
    
    const exportButton = screen.getByRole('button', { name: /export csv/i });
    fireEvent.click(exportButton);
    
    expect(mockCreateObjectURL).toHaveBeenCalled();
    expect(mockClick).toHaveBeenCalled();
  });

  test('shows pagination for large datasets', () => {
    const largeData = Array.from({ length: 100 }, (_, i) => ({
      id: i + 1,
      name: `User ${i + 1}`,
      value: Math.random() * 1000,
    }));
    
    render(<DataVisualization data={largeData} />);
    
    expect(screen.getByText(/showing 1-50 of 100/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next page/i })).toBeInTheDocument();
  });

  test('supports sorting columns', () => {
    render(<DataVisualization data={mockData} />);
    
    const nameHeader = screen.getByText('name');
    fireEvent.click(nameHeader);
    
    // Check if data is sorted (first name should be Alice after sorting)
    const rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveTextContent('Alice Wilson');
  });

  test('supports filtering data', () => {
    render(<DataVisualization data={mockData} />);
    
    const filterInput = screen.getByPlaceholderText(/filter data/i);
    fireEvent.change(filterInput, { target: { value: 'Engineering' } });
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Bob Johnson')).toBeInTheDocument();
    expect(screen.queryByText('Jane Smith')).not.toBeInTheDocument();
    expect(screen.queryByText('Alice Wilson')).not.toBeInTheDocument();
  });

  test('aggregates data for charts', () => {
    render(<DataVisualization data={mockData} />);
    
    const chartSelect = screen.getByDisplayValue('Table');
    fireEvent.change(chartSelect, { target: { value: 'bar' } });
    
    const xAxisSelect = screen.getByDisplayValue(/select column/i);
    fireEvent.change(xAxisSelect, { target: { value: 'department' } });
    
    // The chart should aggregate data by department
    const chartData = screen.getByTestId('bar-chart');
    expect(chartData).toHaveTextContent('Engineering');
    expect(chartData).toHaveTextContent('Marketing');
    expect(chartData).toHaveTextContent('Sales');
  });
});