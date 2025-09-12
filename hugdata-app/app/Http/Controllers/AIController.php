<?php

namespace App\Http\Controllers;

use App\Services\AIService;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class AIController extends Controller
{
    private AIService $aiService;

    public function __construct(AIService $aiService)
    {
        $this->aiService = $aiService;
    }

    public function generateSql(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'query' => 'required|string|max:1000',
            'schema' => 'required|array',
            'context' => 'nullable|array',
        ]);

        try {
            $result = $this->aiService->generateSQL(
                $validated['query'],
                $validated['context'] ?? [],
                $validated['schema']
            );

            return response()->json($result);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'SQL generation failed',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    public function explainQuery(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'sql' => 'required|string',
            'schema' => 'required|array',
        ]);

        try {
            $result = $this->aiService->explainQuery(
                $validated['sql'],
                $validated['schema']
            );

            return response()->json($result);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Query explanation failed',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    public function suggestCharts(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'data_sample' => 'required|array',
            'query_intent' => 'required|string',
        ]);

        try {
            $result = $this->aiService->suggestCharts(
                $validated['data_sample'],
                $validated['query_intent']
            );

            return response()->json($result);

        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Chart suggestion failed',
                'message' => $e->getMessage()
            ], 500);
        }
    }
}
