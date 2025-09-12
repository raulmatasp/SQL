<?php

namespace App\Services;

use Illuminate\Http\Client\Response;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class AIService
{
    private string $aiServiceUrl;

    public function __construct()
    {
        $this->aiServiceUrl = config('services.ai.url', 'http://localhost:8003');
    }

    public function generateSQL(string $query, array $context, array $databaseSchema): array
    {
        try {
            $response = Http::timeout(30)->post($this->aiServiceUrl . '/generate-sql', [
                'query' => $query,
                'context' => $context,
                'database_schema' => $databaseSchema,
                'project_id' => $context['project_id'] ?? null
            ]);

            if ($response->successful()) {
                return $response->json();
            }

            Log::error('AI Service SQL generation failed', [
                'status' => $response->status(),
                'response' => $response->body()
            ]);

            // Return fallback response
            return [
                'sql' => "SELECT * FROM users LIMIT 10;",
                'confidence' => 0.3,
                'explanation' => 'Fallback query due to AI service unavailable',
                'reasoning_steps' => ['AI service unavailable, using fallback']
            ];
        } catch (\Exception $e) {
            Log::error('AI Service connection error', ['error' => $e->getMessage()]);
            
            // Return fallback response on connection error
            return [
                'sql' => "SELECT * FROM users LIMIT 10;",
                'confidence' => 0.3,
                'explanation' => 'Fallback query due to AI service connection error',
                'reasoning_steps' => ['AI service connection error, using fallback']
            ];
        }
    }

    public function explainQuery(string $sql, array $schema): array
    {
        try {
            $response = Http::timeout(30)->post($this->aiServiceUrl . '/explain-query', [
                'sql' => $sql,
                'schema' => $schema
            ]);

            if ($response->successful()) {
                return $response->json();
            }

            throw new \Exception('Failed to explain query');
        } catch (\Exception $e) {
            Log::error('AI Service explain query error', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    public function suggestCharts(array $dataSample, string $queryIntent): array
    {
        try {
            $response = Http::timeout(30)->post($this->aiServiceUrl . '/suggest-charts', [
                'data_sample' => $dataSample,
                'query_intent' => $queryIntent
            ]);

            if ($response->successful()) {
                return $response->json();
            }

            throw new \Exception('Failed to suggest charts');
        } catch (\Exception $e) {
            Log::error('AI Service chart suggestion error', ['error' => $e->getMessage()]);
            throw $e;
        }
    }

    /**
     * Index database schema for semantic search
     */
    public function indexSchema(array $schema, string $projectId): bool
    {
        try {
            $response = Http::timeout(30)->post($this->aiServiceUrl . '/index-schema', [
                'schema' => $schema,
                'project_id' => $projectId
            ]);

            return $response->successful();
        } catch (\Exception $e) {
            Log::error('AI Service schema indexing error', ['error' => $e->getMessage()]);
            return false;
        }
    }

    /**
     * Check if AI service is healthy
     */
    public function isHealthy(): bool
    {
        try {
            $response = Http::timeout(5)->get($this->aiServiceUrl . '/health');
            
            return $response->successful() && 
                   $response->json('status') === 'healthy';
        } catch (\Exception $e) {
            return false;
        }
    }

    private function getSchemaForContext(array $context): array
    {
        if (!isset($context['data_source_id'])) {
            return [];
        }

        // This would connect to the data source and get schema
        // For now, return empty array
        return [];
    }
}