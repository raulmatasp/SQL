import React, { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { queryService, dataSourceService, aiService, type DataSource } from '../services/api';
import ChartVisualization from './ChartVisualization';

interface QueryInterfaceProps {
  projectId: string;
}

interface QueryResult {
  query_id: string;
  sql: string;
  explanation: string;
  results: any[];
  execution_time_ms: number;
  row_count: number;
  confidence: number;
}

const QueryInterface: React.FC<QueryInterfaceProps> = ({ projectId }) => {
  const [naturalQuery, setNaturalQuery] = useState('');
  const [selectedDataSource, setSelectedDataSource] = useState<string>('');
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [sqlQuery, setSqlQuery] = useState('');
  const [showSqlEditor, setShowSqlEditor] = useState(false);
  const [showVisualization, setShowVisualization] = useState(true);

  // Fetch data sources for the project
  const { data: dataSources, isLoading: dataSourcesLoading } = useQuery<DataSource[]>({
    queryKey: ['dataSources', projectId],
    queryFn: () => dataSourceService.getAll(projectId),
    enabled: !!projectId,
  });

  // Auto-select first active data source
  useEffect(() => {
    if (dataSources && !selectedDataSource) {
      const activeDataSource = dataSources.find(ds => ds.status === 'active');
      if (activeDataSource) {
        setSelectedDataSource(activeDataSource.id);
      }
    }
  }, [dataSources, selectedDataSource]);

  // Natural language query mutation
  const naturalLanguageQuery = useMutation({
    mutationFn: (params: { query: string; projectId: string; dataSourceId: string }) =>
      queryService.processNaturalLanguage({
        query: params.query,
        project_id: params.projectId,
        data_source_id: params.dataSourceId,
      }),
    onSuccess: (result: QueryResult) => {
      setQueryResult(result);
      setSqlQuery(result.sql);
    },
  });

  // Direct SQL execution mutation
  const directSqlQuery = useMutation({
    mutationFn: (params: { sql: string; dataSourceId: string }) =>
      queryService.executeSql(params.sql, params.dataSourceId),
    onSuccess: (result) => {
      setQueryResult({
        query_id: '',
        sql: sqlQuery,
        explanation: 'Direct SQL execution',
        results: result.results,
        execution_time_ms: result.execution_time_ms,
        row_count: result.row_count,
        confidence: 1.0,
      });
    },
  });

  const handleNaturalLanguageSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!naturalQuery.trim() || !selectedDataSource) return;

    naturalLanguageQuery.mutate({
      query: naturalQuery.trim(),
      projectId,
      dataSourceId: selectedDataSource,
    });
  };

  const handleSqlSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sqlQuery.trim() || !selectedDataSource) return;

    directSqlQuery.mutate({
      sql: sqlQuery.trim(),
      dataSourceId: selectedDataSource,
    });
  };

  const handleSuggestionClick = (suggestion: string) => {
    setNaturalQuery(suggestion);
  };

  if (dataSourcesLoading) {
    return <div className="p-4">Loading data sources...</div>;
  }

  const activeDataSources = dataSources?.filter(ds => ds.status === 'active') || [];

  if (activeDataSources.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="text-gray-500 text-lg mb-2">No active data sources</div>
        <p className="text-gray-400">Please connect a data source to start querying data</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Query Interface</h1>
        <div className="flex items-center gap-4">
          <select
            value={selectedDataSource}
            onChange={(e) => setSelectedDataSource(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select Data Source</option>
            {activeDataSources.map((ds) => (
              <option key={ds.id} value={ds.id}>
                {ds.name} ({ds.type})
              </option>
            ))}
          </select>
          <div className="flex gap-2">
            <button
              onClick={() => setShowSqlEditor(!showSqlEditor)}
              className={`px-4 py-2 rounded-md ${
                showSqlEditor
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {showSqlEditor ? 'Natural Language' : 'SQL Editor'}
            </button>
            {queryResult && queryResult.results.length > 0 && (
              <button
                onClick={() => setShowVisualization(!showVisualization)}
                className={`px-4 py-2 rounded-md ${
                  showVisualization
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {showVisualization ? 'Hide Charts' : 'Show Charts'}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Query Input Panel */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            {!showSqlEditor ? (
              // Natural Language Interface
              <div className="space-y-4">
                <h2 className="text-lg font-medium text-gray-900">Ask a question about your data</h2>
                
                {/* Query Suggestions */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {[
                    'Show me the total revenue by month',
                    'What are the top 10 customers by sales?',
                    'List all orders from the last 30 days',
                    'Which products have the highest profit margins?',
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm hover:bg-blue-100"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>

                <form onSubmit={handleNaturalLanguageSubmit} className="space-y-4">
                  <textarea
                    value={naturalQuery}
                    onChange={(e) => setNaturalQuery(e.target.value)}
                    placeholder="Ask a question about your data in plain English..."
                    className="w-full h-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  />
                  <button
                    type="submit"
                    disabled={!naturalQuery.trim() || !selectedDataSource || naturalLanguageQuery.isPending}
                    className="w-full bg-blue-600 text-white py-3 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {naturalLanguageQuery.isPending ? 'Generating SQL...' : 'Generate & Execute Query'}
                  </button>
                </form>
              </div>
            ) : (
              // SQL Editor Interface
              <div className="space-y-4">
                <h2 className="text-lg font-medium text-gray-900">SQL Query Editor</h2>
                
                <form onSubmit={handleSqlSubmit} className="space-y-4">
                  <textarea
                    value={sqlQuery}
                    onChange={(e) => setSqlQuery(e.target.value)}
                    placeholder="Enter your SQL query here..."
                    className="w-full h-48 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  />
                  <button
                    type="submit"
                    disabled={!sqlQuery.trim() || !selectedDataSource || directSqlQuery.isPending}
                    className="w-full bg-green-600 text-white py-3 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {directSqlQuery.isPending ? 'Executing...' : 'Execute SQL'}
                  </button>
                </form>
              </div>
            )}

            {/* Error Display */}
            {(naturalLanguageQuery.error || directSqlQuery.error) && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                <div className="text-red-800">
                  {(naturalLanguageQuery.error as any)?.response?.data?.message || 
                   (directSqlQuery.error as any)?.response?.data?.message || 
                   'An error occurred'}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Query Info Panel */}
        <div className="space-y-6">
          {queryResult && (
            <>
              {/* Generated SQL */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Generated SQL</h3>
                <div className="bg-gray-50 p-3 rounded border">
                  <code className="text-sm text-gray-800 whitespace-pre-wrap">{queryResult.sql}</code>
                </div>
                {queryResult.confidence && (
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-sm text-gray-600">Confidence:</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${queryResult.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">{Math.round(queryResult.confidence * 100)}%</span>
                  </div>
                )}
              </div>

              {/* Query Statistics */}
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-900 mb-3">Query Statistics</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Execution Time:</span>
                    <span className="font-medium">{queryResult.execution_time_ms}ms</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Rows Returned:</span>
                    <span className="font-medium">{queryResult.row_count}</span>
                  </div>
                  {queryResult.explanation && (
                    <div className="pt-2 border-t">
                      <div className="text-gray-600 mb-1">Explanation:</div>
                      <div className="text-sm text-gray-800">{queryResult.explanation}</div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Chart Visualization */}
      {queryResult && queryResult.results.length > 0 && showVisualization && (
        <ChartVisualization
          data={queryResult.results}
          queryText={naturalQuery || 'Direct SQL query'}
        />
      )}

      {/* Results Display */}
      {queryResult && queryResult.results.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Query Results</h2>
          </div>
          <div className="p-4">
            <ResultsTable data={queryResult.results} />
          </div>
        </div>
      )}

      {queryResult && queryResult.results.length === 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <div className="text-gray-500">No results found</div>
        </div>
      )}
    </div>
  );
};

// Results Table Component
interface ResultsTableProps {
  data: any[];
}

const ResultsTable: React.FC<ResultsTableProps> = ({ data }) => {
  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);
  const maxRows = 100; // Limit display to prevent performance issues
  const displayData = data.slice(0, maxRows);

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column) => (
              <th
                key={column}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {displayData.map((row, index) => (
            <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {columns.map((column) => (
                <td key={column} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatCellValue(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > maxRows && (
        <div className="p-4 text-center text-gray-500 bg-gray-50 border-t">
          Showing {maxRows} of {data.length} rows
        </div>
      )}
    </div>
  );
};

// Helper function to format cell values
const formatCellValue = (value: any): string => {
  if (value === null || value === undefined) return '';
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
};

export default QueryInterface;