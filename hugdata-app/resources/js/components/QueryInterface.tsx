import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Loader2, Play } from 'lucide-react';

interface QueryInterfaceProps {
  projectId: string;
  threadId: string;
  onQuerySubmit: (query: string) => void;
  isLoading?: boolean;
}

interface QueryHistory {
  id: string;
  question: string;
  sql?: string;
  status: 'pending' | 'completed' | 'failed';
  createdAt: string;
}

export function QueryInterface({
  onQuerySubmit,
  isLoading = false
}: QueryInterfaceProps) {
  const [query, setQuery] = useState('');
  const [queryHistory, setQueryHistory] = useState<QueryHistory[]>([]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onQuerySubmit(query.trim());

      // Add to history
      const newQuery: QueryHistory = {
        id: Date.now().toString(),
        question: query.trim(),
        status: 'pending',
        createdAt: new Date().toISOString(),
      };
      setQueryHistory(prev => [newQuery, ...prev]);
      setQuery('');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Query Input */}
      <Card>
        <CardHeader>
          <CardTitle>Ask a Question</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask questions about your data in natural language..."
              className="min-h-[100px] resize-none"
              disabled={isLoading}
            />
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                {query.length}/1000 characters
              </div>
              <Button
                type="submit"
                disabled={!query.trim() || isLoading}
                className="min-w-[100px]"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Ask
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Query History */}
      {queryHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Queries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {queryHistory.map((item) => (
                <div
                  key={item.id}
                  className="flex items-start justify-between p-3 border rounded-lg"
                >
                  <div className="flex-1">
                    <p className="font-medium text-sm">{item.question}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(item.createdAt).toLocaleString()}
                    </p>
                    {item.sql && (
                      <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono">
                        {item.sql}
                      </div>
                    )}
                  </div>
                  <Badge
                    variant="secondary"
                    className={getStatusColor(item.status)}
                  >
                    {item.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Examples */}
      <Card>
        <CardHeader>
          <CardTitle>Example Questions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {[
              "Show me total sales by month",
              "Which products have the highest revenue?",
              "What are the top 10 customers by order value?",
              "Compare sales performance across regions",
              "Show customer acquisition trends",
              "What is the average order value?"
            ].map((example, index) => (
              <button
                key={index}
                onClick={() => setQuery(example)}
                className="p-2 text-left text-sm border rounded hover:bg-gray-50 transition-colors"
                disabled={isLoading}
              >
                {example}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}