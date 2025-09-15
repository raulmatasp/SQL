import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Copy, Download, RefreshCw } from 'lucide-react';

interface QueryResultProps {
  query: {
    id: string;
    question: string;
    sql?: string;
    sql_generation_reasoning?: string;
    status: 'pending' | 'completed' | 'failed' | 'stopped';
    error_message?: string;
    chart_schema?: any;
    chart_type?: string;
    execution_time_ms?: number;
    created_at: string;
  };
  result?: {
    data: any[];
    columns: string[];
    row_count: number;
    execution_time_ms?: number;
  };
  onRetry?: () => void;
}

export function QueryResult({ query, result, onRetry }: QueryResultProps) {
  const [copiedSql, setCopiedSql] = useState(false);

  const copyToClipboard = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedSql(true);
    setTimeout(() => setCopiedSql(false), 2000);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'stopped': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatExecutionTime = (ms?: number) => {
    if (!ms) return 'Unknown';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-base">{query.question}</CardTitle>
            <div className="flex items-center gap-2 mt-2">
              <Badge
                variant="secondary"
                className={getStatusColor(query.status)}
              >
                {query.status}
              </Badge>
              {query.execution_time_ms && (
                <Badge variant="outline">
                  {formatExecutionTime(query.execution_time_ms)}
                </Badge>
              )}
              <span className="text-xs text-muted-foreground">
                {new Date(query.created_at).toLocaleString()}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            {query.status === 'failed' && onRetry && (
              <Button variant="outline" size="sm" onClick={onRetry}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {query.status === 'pending' && (
          <div className="text-center py-8">
            <div className="inline-flex items-center px-4 py-2 font-semibold leading-6 text-sm shadow rounded-md text-white bg-indigo-500 transition ease-in-out duration-150">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing query...
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              This may take a few moments
            </p>
          </div>
        )}

        {query.status === 'failed' && (
          <div className="text-center py-8">
            <div className="text-red-600 mb-2">Query Failed</div>
            {query.error_message && (
              <p className="text-sm text-muted-foreground">
                {query.error_message}
              </p>
            )}
          </div>
        )}

        {query.status === 'completed' && (
          <Tabs defaultValue="data" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="data">Data</TabsTrigger>
              <TabsTrigger value="chart">Chart</TabsTrigger>
              <TabsTrigger value="sql">SQL</TabsTrigger>
              <TabsTrigger value="reasoning">Reasoning</TabsTrigger>
            </TabsList>

            <TabsContent value="data" className="mt-4">
              {result && result.data.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      {result.row_count} rows returned
                      {result.execution_time_ms && (
                        <> in {formatExecutionTime(result.execution_time_ms)}</>
                      )}
                    </p>
                    <Button variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Export CSV
                    </Button>
                  </div>

                  <ScrollArea className="h-[400px] border rounded-md">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          {result.columns.map((column) => (
                            <TableHead key={column} className="font-medium">
                              {column}
                            </TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {result.data.slice(0, 100).map((row, index) => (
                          <TableRow key={index}>
                            {result.columns.map((column) => (
                              <TableCell key={column} className="max-w-xs truncate">
                                {row[column] !== null ? String(row[column]) : '-'}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </ScrollArea>

                  {result.row_count > 100 && (
                    <p className="text-xs text-muted-foreground text-center">
                      Showing first 100 rows of {result.row_count} total rows
                    </p>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No data returned
                </div>
              )}
            </TabsContent>

            <TabsContent value="chart" className="mt-4">
              {query.chart_schema ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">
                      {query.chart_type || 'Chart'} Visualization
                    </p>
                  </div>
                  <div className="h-[400px] border rounded-md bg-gray-50 flex items-center justify-center">
                    <p className="text-muted-foreground">
                      Chart visualization would render here using Vega-Lite
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No chart available for this query
                </div>
              )}
            </TabsContent>

            <TabsContent value="sql" className="mt-4">
              {query.sql ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">Generated SQL</p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(query.sql || '')}
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      {copiedSql ? 'Copied!' : 'Copy'}
                    </Button>
                  </div>
                  <ScrollArea className="h-[300px]">
                    <pre className="p-4 bg-gray-50 rounded-md text-sm font-mono whitespace-pre-wrap">
                      {query.sql}
                    </pre>
                  </ScrollArea>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No SQL available
                </div>
              )}
            </TabsContent>

            <TabsContent value="reasoning" className="mt-4">
              {query.sql_generation_reasoning ? (
                <div className="space-y-4">
                  <p className="text-sm font-medium">AI Reasoning</p>
                  <div className="p-4 bg-gray-50 rounded-md">
                    <p className="text-sm whitespace-pre-wrap">
                      {query.sql_generation_reasoning}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No reasoning information available
                </div>
              )}
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}