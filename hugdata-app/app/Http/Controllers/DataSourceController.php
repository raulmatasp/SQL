<?php

namespace App\Http\Controllers;

use App\Models\DataSource;
use App\Models\Project;
use App\Services\DatabaseConnectionService;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class DataSourceController extends Controller
{
    private DatabaseConnectionService $dbService;

    public function __construct(DatabaseConnectionService $dbService)
    {
        $this->dbService = $dbService;
    }

    public function index(Request $request, Project $project): JsonResponse
    {
        $this->authorize('view', $project);

        $dataSources = $project->dataSources()
            ->latest()
            ->paginate(20);

        return response()->json($dataSources);
    }

    public function store(Request $request, Project $project): JsonResponse
    {
        $this->authorize('view', $project);

        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'type' => 'required|in:postgresql,mysql,bigquery,snowflake,sqlite',
            'connection_config' => 'required|array',
            'connection_config.host' => 'required_unless:type,sqlite|string',
            'connection_config.port' => 'nullable|integer',
            'connection_config.database' => 'required|string',
            'connection_config.username' => 'required_unless:type,sqlite|string',
            'connection_config.password' => 'required_unless:type,sqlite|string',
        ]);

        $dataSource = DataSource::create([
            ...$validated,
            'project_id' => $project->id,
            'status' => 'inactive',
        ]);

        return response()->json($dataSource, 201);
    }

    public function show(DataSource $dataSource): JsonResponse
    {
        $this->authorize('view', $dataSource);

        return response()->json($dataSource);
    }

    public function update(Request $request, DataSource $dataSource): JsonResponse
    {
        $this->authorize('update', $dataSource);

        $validated = $request->validate([
            'name' => 'sometimes|string|max:255',
            'type' => 'sometimes|in:postgresql,mysql,bigquery,snowflake,sqlite',
            'connection_config' => 'sometimes|array',
        ]);

        $dataSource->update($validated);

        return response()->json($dataSource);
    }

    public function destroy(DataSource $dataSource): JsonResponse
    {
        $this->authorize('delete', $dataSource);

        $dataSource->delete();

        return response()->json(['message' => 'Data source deleted successfully']);
    }

    public function testConnection(DataSource $dataSource): JsonResponse
    {
        $this->authorize('testConnection', $dataSource);

        try {
            $result = $this->dbService->testConnection($dataSource);
            
            if ($result['success']) {
                $dataSource->markAsConnected();
                return response()->json($result);
            } else {
                $dataSource->markAsDisconnected();
                return response()->json($result, 400);
            }
        } catch (\Exception $e) {
            $dataSource->markAsDisconnected();

            return response()->json([
                'success' => false,
                'message' => 'Connection failed: ' . $e->getMessage()
            ], 400);
        }
    }

    public function getSchema(DataSource $dataSource): JsonResponse
    {
        $this->authorize('getSchema', $dataSource);

        if (!$dataSource->isActive()) {
            return response()->json([
                'error' => 'Data source is not connected'
            ], 400);
        }

        try {
            $schema = $this->dbService->getSchema($dataSource);
            return response()->json($schema);
        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to retrieve schema: ' . $e->getMessage()
            ], 500);
        }
    }
}
