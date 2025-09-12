<?php

namespace App\Http\Controllers;

use App\Models\DataSource;
use App\Models\Project;
use App\Models\Query;
use App\Services\AIService;
use App\Services\DatabaseConnectionService;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class QueryController extends Controller
{
    private AIService $aiService;
    private DatabaseConnectionService $dbService;

    public function __construct(AIService $aiService, DatabaseConnectionService $dbService)
    {
        $this->aiService = $aiService;
        $this->dbService = $dbService;
    }

    public function processNaturalLanguage(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'query' => 'required|string|max:1000',
            'project_id' => 'required|uuid|exists:projects,id',
            'data_source_id' => 'required|uuid|exists:data_sources,id'
        ]);

        try {
            $project = Project::findOrFail($validated['project_id']);
            $dataSource = DataSource::findOrFail($validated['data_source_id']);

            $this->authorize('view', $project);
            $this->authorize('view', $dataSource);

            if (!$dataSource->isActive()) {
                return response()->json([
                    'error' => 'Data source is not connected'
                ], 400);
            }

            // Get real database schema from data source
            $schema = $this->dbService->getSchema($dataSource);

            // Generate SQL using AI service
            $aiResult = $this->aiService->generateSQL(
                $validated['query'],
                ['project_id' => $project->id],
                $schema
            );

            $generatedSql = $aiResult['sql'];
            
            // Execute the SQL query using the database service
            $queryStart = microtime(true);
            $queryResult = $this->dbService->executeQuery($dataSource, $generatedSql);
            $executionTime = round((microtime(true) - $queryStart) * 1000, 2);

            if (!$queryResult['success']) {
                return response()->json([
                    'error' => 'Query execution failed',
                    'message' => $queryResult['error'] ?? 'Unknown error',
                    'sql' => $generatedSql,
                    'explanation' => $aiResult['explanation'] ?? 'AI-generated SQL query'
                ], 400);
            }

            // Store query history
            $query = Query::create([
                'project_id' => $project->id,
                'user_id' => $request->user()->id,
                'natural_language' => $validated['query'],
                'generated_sql' => $generatedSql,
                'results' => $queryResult['results'],
                'status' => 'success',
                'execution_time_ms' => $queryResult['execution_time_ms'] ?? $executionTime,
            ]);

            return response()->json([
                'query_id' => $query->id,
                'sql' => $generatedSql,
                'explanation' => $aiResult['explanation'] ?? 'AI-generated SQL query',
                'results' => $queryResult['results'],
                'execution_time_ms' => $queryResult['execution_time_ms'] ?? $executionTime,
                'row_count' => $queryResult['row_count'],
                'confidence' => $aiResult['confidence'] ?? 0.95
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Query processing failed',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    public function executeSql(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'sql' => 'required|string',
            'data_source_id' => 'required|uuid|exists:data_sources,id'
        ]);

        try {
            $dataSource = DataSource::findOrFail($validated['data_source_id']);
            
            $this->authorize('view', $dataSource);

            if (!$dataSource->isActive()) {
                return response()->json([
                    'error' => 'Data source is not connected'
                ], 400);
            }

            // Execute SQL using the database service
            $queryResult = $this->dbService->executeQuery($dataSource, $validated['sql']);
            
            if (!$queryResult['success']) {
                return response()->json([
                    'error' => 'SQL execution failed',
                    'message' => $queryResult['error'] ?? 'Unknown error',
                    'sql' => $validated['sql']
                ], 400);
            }

            return response()->json([
                'results' => $queryResult['results'],
                'execution_time_ms' => $queryResult['execution_time_ms'],
                'row_count' => $queryResult['row_count']
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'SQL execution failed',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    public function history(Request $request): JsonResponse
    {
        $queries = $request->user()
            ->queries()
            ->with('project')
            ->latest()
            ->paginate(20);

        return response()->json($queries);
    }

    public function show(Query $query): JsonResponse
    {
        $this->authorize('view', $query);

        return response()->json($query);
    }
}
