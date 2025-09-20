import React, { useState, useCallback } from 'react';
import { router } from '@inertiajs/react';
import { QueryInterface } from '@/components/QueryInterface';
import { QueryResult } from '@/components/QueryResult';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Database, Plus, Settings } from 'lucide-react';

interface Project {
  id: string;
  name: string;
  description?: string;
  data_sources?: DataSource[];
}

interface DataSource {
  id: string;
  name: string;
  type: string;
  status: string;
}

interface Thread {
  id: string;
  title?: string;
  created_at: string;
}

interface Query {
  id: string;
  question: string;
  sql?: string;
  sql_generation_reasoning?: string;
  status: 'pending' | 'completed' | 'failed' | 'stopped';
  error_message?: string;
  chart_schema?: Record<string, unknown>;
  chart_type?: string;
  execution_time_ms?: number;
  created_at: string;
  query_result?: {
    data: Record<string, unknown>[];
    columns: string[];
    row_count: number;
    execution_time_ms?: number;
  };
}

interface AnalyticsProps {
  project: Project;
  threads: Thread[];
  currentThread: Thread;
  queries: Query[];
  recentQueries: Query[];
}

export default function Analytics({
  project,
  threads,
  currentThread,
  queries,
  recentQueries
}: AnalyticsProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleQuerySubmit = useCallback(async (question: string) => {
    setIsLoading(true);

    try {
      const response = await fetch('/api/queries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRF-TOKEN': (document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement)?.content || '',
        },
        body: JSON.stringify({
          question,
          thread_id: currentThread.id,
          project_id: project.id,
        }),
      });

      if (response.ok) {
        // Refresh the page to show new query
        router.reload();
      } else {
        console.error('Failed to submit query');
      }
    } catch (error) {
      console.error('Error submitting query:', error);
    } finally {
      setIsLoading(false);
    }
  }, [currentThread.id, project.id]);

  const handleRetryQuery = useCallback((queryId: string) => {
    // Implement retry logic
    console.log('Retrying query:', queryId);
  }, []);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{project.name}</h1>
          <p className="text-muted-foreground mt-1">
            {project.description || 'Analytics and data exploration'}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            New Thread
          </Button>
        </div>
      </div>

      {/* Project Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Data Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {project.data_sources?.length || 0}
            </div>
            <div className="flex gap-1 mt-2">
              {project.data_sources?.map((ds) => (
                <Badge
                  key={ds.id}
                  variant={ds.status === 'active' ? 'default' : 'secondary'}
                  className="text-xs"
                >
                  {ds.type}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Threads</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{threads.length}</div>
            <p className="text-xs text-muted-foreground mt-2">
              Conversation sessions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recentQueries.length}</div>
            <p className="text-xs text-muted-foreground mt-2">
              Questions asked
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Query Interface */}
        <div className="lg:col-span-1">
          <QueryInterface
            projectId={project.id}
            threadId={currentThread.id}
            onQuerySubmit={handleQuerySubmit}
            isLoading={isLoading}
          />
        </div>

        {/* Right Column - Query Results */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Results</h2>
            {queries.length > 0 && (
              <Badge variant="outline">
                {queries.length} {queries.length === 1 ? 'query' : 'queries'}
              </Badge>
            )}
          </div>

          {queries.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12">
                  <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No queries yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Start by asking a question about your data in natural language.
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Try questions like "Show me sales by month" or "What are our top products?"
                  </p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              {queries.map((query) => (
                <QueryResult
                  key={query.id}
                  query={query}
                  result={query.query_result}
                  onRetry={() => handleRetryQuery(query.id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}