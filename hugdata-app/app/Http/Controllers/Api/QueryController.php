<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Query;
use App\Models\Thread;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Str;

class QueryController extends Controller
{
    /**
     * Get queries for a thread
     */
    public function index(Request $request): JsonResponse
    {
        $threadId = $request->get('thread_id');
        $projectId = $request->get('project_id');

        $query = Query::query();

        if ($threadId) {
            $query->where('thread_id', $threadId);
        }

        if ($projectId) {
            $query->where('project_id', $projectId);
        }

        $queries = $query->with(['thread', 'queryResult'])
                        ->orderBy('created_at', 'desc')
                        ->paginate(20);

        return response()->json($queries);
    }

    /**
     * Create a new query (ask AI service)
     */
    public function store(Request $request): JsonResponse
    {
        $request->validate([
            'question' => 'required|string',
            'thread_id' => 'required|exists:threads,id',
            'project_id' => 'required|exists:projects,id',
            'mdl_hash' => 'nullable|string',
            'histories' => 'nullable|array',
        ]);

        // Create query record
        $query = Query::create([
            'query_id' => Str::uuid(),
            'question' => $request->question,
            'thread_id' => $request->thread_id,
            'project_id' => $request->project_id,
            'status' => 'pending',
        ]);

        // Call AI service
        try {
            $response = Http::post(config('services.hugdata_ai.base_url') . '/v1/asks', [
                'query' => $request->question,
                'mdl_hash' => $request->mdl_hash,
                'histories' => $request->histories ?? [],
            ]);

            if ($response->successful()) {
                $aiQueryId = $response->json('query_id');
                $query->update(['query_id' => $aiQueryId]);
            } else {
                $query->update([
                    'status' => 'failed',
                    'error_message' => 'AI service error: ' . $response->body(),
                ]);
            }
        } catch (\Exception $e) {
            $query->update([
                'status' => 'failed',
                'error_message' => 'Connection error: ' . $e->getMessage(),
            ]);
        }

        return response()->json($query, 201);
    }

    /**
     * Get query result from AI service
     */
    public function show(string $id): JsonResponse
    {
        $query = Query::with('queryResult')->findOrFail($id);

        // If we don't have results yet, try to fetch from AI service
        if (!$query->queryResult && $query->status === 'pending') {
            try {
                $response = Http::get(
                    config('services.hugdata_ai.base_url') . '/v1/asks/' . $query->query_id . '/result'
                );

                if ($response->successful()) {
                    $result = $response->json();
                    $query->update([
                        'sql' => $result['sql'] ?? null,
                        'sql_generation_reasoning' => $result['reasoning'] ?? null,
                        'status' => 'completed',
                    ]);

                    // Save query result if data exists
                    if (isset($result['data'])) {
                        $query->queryResult()->create([
                            'data' => $result['data'],
                            'columns' => $result['columns'] ?? [],
                            'row_count' => count($result['data']),
                        ]);
                    }
                }
            } catch (\Exception $e) {
                $query->update([
                    'status' => 'failed',
                    'error_message' => 'Failed to fetch result: ' . $e->getMessage(),
                ]);
            }
        }

        return response()->json($query->load('queryResult'));
    }

    /**
     * Stop a running query
     */
    public function update(Request $request, string $id): JsonResponse
    {
        $query = Query::findOrFail($id);

        if ($request->input('status') === 'stopped') {
            try {
                Http::patch(
                    config('services.hugdata_ai.base_url') . '/v1/asks/' . $query->query_id,
                    ['status' => 'stopped']
                );

                $query->update(['status' => 'stopped']);
            } catch (\Exception $e) {
                return response()->json(['error' => 'Failed to stop query'], 500);
            }
        }

        return response()->json($query);
    }

    /**
     * Delete a query
     */
    public function destroy(string $id): JsonResponse
    {
        $query = Query::findOrFail($id);
        $query->delete();

        return response()->json(['message' => 'Query deleted']);
    }
}
