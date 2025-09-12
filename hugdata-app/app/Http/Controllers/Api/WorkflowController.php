<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Jobs\TriggerDagsterWorkflow;
use App\Models\WorkflowRun;
use App\Models\Project;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Validator;

class WorkflowController extends Controller
{
    /**
     * Trigger a new Dagster workflow
     */
    public function trigger(Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'workflow_type' => 'required|string|in:schema_ingestion,query_generation,full_pipeline',
            'project_id' => 'required|exists:projects,id',
            'input_data' => 'array',
            'priority' => 'string|in:high,medium,low'
        ]);

        if ($validator->fails()) {
            return response()->json([
                'error' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $project = Project::findOrFail($request->project_id);
            
            // Create workflow run record
            $workflowRun = WorkflowRun::create([
                'workflow_type' => $request->workflow_type,
                'project_id' => $request->project_id,
                'user_id' => $request->user()->id,
                'input_data' => $request->input_data ?? [],
                'status' => 'queued'
            ]);

            // Dispatch background job to trigger Dagster
            TriggerDagsterWorkflow::dispatch(
                $request->workflow_type,
                $request->input_data ?? [],
                $request->project_id,
                $request->user()->id,
                $workflowRun->id
            )->onQueue($request->priority === 'high' ? 'workflows-high' : 'workflows');

            return response()->json([
                'workflow_run_id' => $workflowRun->id,
                'status' => 'queued',
                'message' => 'Workflow queued for execution'
            ], 202);

        } catch (\Exception $e) {
            Log::error('Workflow trigger failed', [
                'error' => $e->getMessage(),
                'request' => $request->all()
            ]);

            return response()->json([
                'error' => 'Failed to trigger workflow',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get workflow run status
     */
    public function status(WorkflowRun $workflowRun): JsonResponse
    {
        $this->authorize('view', $workflowRun);

        $response = [
            'id' => $workflowRun->id,
            'dagster_run_id' => $workflowRun->dagster_run_id,
            'status' => $workflowRun->status,
            'workflow_type' => $workflowRun->workflow_type,
            'project_id' => $workflowRun->project_id,
            'input_data' => $workflowRun->input_data,
            'output_data' => $workflowRun->output_data,
            'error_message' => $workflowRun->error_message,
            'started_at' => $workflowRun->started_at,
            'completed_at' => $workflowRun->completed_at,
            'created_at' => $workflowRun->created_at
        ];

        // If we have a Dagster run ID, fetch additional details
        if ($workflowRun->dagster_run_id && $workflowRun->isRunning()) {
            try {
                $dagsterStatus = $this->fetchDagsterStatus($workflowRun->dagster_run_id);
                $response['dagster_details'] = $dagsterStatus;
            } catch (\Exception $e) {
                Log::warning('Failed to fetch Dagster status', [
                    'dagster_run_id' => $workflowRun->dagster_run_id,
                    'error' => $e->getMessage()
                ]);
            }
        }

        return response()->json($response);
    }

    /**
     * List workflow runs for a project
     */
    public function index(Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'project_id' => 'exists:projects,id',
            'status' => 'string|in:queued,started,in_progress,success,failure',
            'workflow_type' => 'string|in:schema_ingestion,query_generation,full_pipeline',
            'limit' => 'integer|min:1|max:100'
        ]);

        if ($validator->fails()) {
            return response()->json([
                'error' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }

        $query = WorkflowRun::query()
            ->with(['project', 'user'])
            ->orderBy('created_at', 'desc');

        // Apply filters
        if ($request->project_id) {
            $query->where('project_id', $request->project_id);
        }

        if ($request->status) {
            $query->where('status', $request->status);
        }

        if ($request->workflow_type) {
            $query->where('workflow_type', $request->workflow_type);
        }

        // Only show workflows user has access to
        $query->whereHas('project', function ($q) use ($request) {
            $q->where('user_id', $request->user()->id);
        });

        $workflows = $query->paginate($request->get('limit', 20));

        return response()->json($workflows);
    }

    /**
     * Cancel a running workflow
     */
    public function cancel(WorkflowRun $workflowRun): JsonResponse
    {
        $this->authorize('update', $workflowRun);

        if (!$workflowRun->isRunning()) {
            return response()->json([
                'error' => 'Workflow is not running',
                'status' => $workflowRun->status
            ], 400);
        }

        try {
            // If we have a Dagster run ID, try to cancel it
            if ($workflowRun->dagster_run_id) {
                $this->cancelDagsterRun($workflowRun->dagster_run_id);
            }

            $workflowRun->update([
                'status' => 'failure',
                'error_message' => 'Cancelled by user',
                'completed_at' => now()
            ]);

            return response()->json([
                'message' => 'Workflow cancelled successfully',
                'status' => $workflowRun->status
            ]);

        } catch (\Exception $e) {
            Log::error('Workflow cancellation failed', [
                'workflow_run_id' => $workflowRun->id,
                'error' => $e->getMessage()
            ]);

            return response()->json([
                'error' => 'Failed to cancel workflow',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Webhook endpoint for Dagster status updates
     */
    public function updateStatus(WorkflowRun $workflowRun, Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'dagster_run_id' => 'string',
            'status' => 'string',
            'error_message' => 'string|nullable',
            'output_data' => 'array|nullable'
        ]);

        if ($validator->fails()) {
            return response()->json([
                'error' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $updates = [];

            if ($request->has('dagster_run_id')) {
                $updates['dagster_run_id'] = $request->dagster_run_id;
            }

            if ($request->has('status')) {
                $updates['status'] = $request->status;
                
                if ($request->status === 'started' && !$workflowRun->started_at) {
                    $updates['started_at'] = now();
                } elseif (in_array($request->status, ['success', 'failure'])) {
                    $updates['completed_at'] = now();
                }
            }

            if ($request->has('error_message')) {
                $updates['error_message'] = $request->error_message;
            }

            if ($request->has('output_data')) {
                $updates['output_data'] = $request->output_data;
            }

            $workflowRun->update($updates);

            return response()->json([
                'message' => 'Workflow status updated',
                'status' => $workflowRun->status
            ]);

        } catch (\Exception $e) {
            Log::error('Workflow status update failed', [
                'workflow_run_id' => $workflowRun->id,
                'error' => $e->getMessage(),
                'request' => $request->all()
            ]);

            return response()->json([
                'error' => 'Failed to update workflow status',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Get workflow analytics and statistics
     */
    public function analytics(Request $request): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'project_id' => 'exists:projects,id',
            'days' => 'integer|min:1|max:90'
        ]);

        if ($validator->fails()) {
            return response()->json([
                'error' => 'Validation failed',
                'errors' => $validator->errors()
            ], 422);
        }

        $days = $request->get('days', 30);
        $startDate = now()->subDays($days);

        $query = WorkflowRun::query()->where('created_at', '>=', $startDate);

        if ($request->project_id) {
            $query->where('project_id', $request->project_id);
        }

        // Only include workflows user has access to
        $query->whereHas('project', function ($q) use ($request) {
            $q->where('user_id', $request->user()->id);
        });

        $analytics = [
            'total_runs' => $query->count(),
            'success_rate' => $query->where('status', 'success')->count() / max($query->count(), 1) * 100,
            'average_execution_time' => $query->whereNotNull('started_at')
                ->whereNotNull('completed_at')
                ->selectRaw('AVG(TIMESTAMPDIFF(SECOND, started_at, completed_at)) as avg_seconds')
                ->value('avg_seconds'),
            'status_breakdown' => $query->groupBy('status')
                ->selectRaw('status, count(*) as count')
                ->pluck('count', 'status'),
            'workflow_type_breakdown' => $query->groupBy('workflow_type')
                ->selectRaw('workflow_type, count(*) as count')
                ->pluck('count', 'workflow_type'),
            'recent_failures' => WorkflowRun::where('status', 'failure')
                ->where('created_at', '>=', $startDate)
                ->with(['project'])
                ->orderBy('created_at', 'desc')
                ->limit(5)
                ->get()
                ->map(function ($run) {
                    return [
                        'id' => $run->id,
                        'workflow_type' => $run->workflow_type,
                        'project_name' => $run->project->name,
                        'error_message' => $run->error_message,
                        'created_at' => $run->created_at
                    ];
                })
        ];

        return response()->json($analytics);
    }

    /**
     * Fetch status from Dagster API
     */
    private function fetchDagsterStatus(string $dagsterRunId): array
    {
        $dagsterUrl = config('services.dagster.base_url');
        
        $response = Http::timeout(10)->get("{$dagsterUrl}/dagster/status/{$dagsterRunId}");
        
        if ($response->successful()) {
            return $response->json();
        }
        
        throw new \Exception("Failed to fetch Dagster status: " . $response->body());
    }

    /**
     * Cancel Dagster run
     */
    private function cancelDagsterRun(string $dagsterRunId): void
    {
        $dagsterUrl = config('services.dagster.base_url');
        
        $response = Http::timeout(10)->delete("{$dagsterUrl}/dagster/runs/{$dagsterRunId}");
        
        if (!$response->successful()) {
            throw new \Exception("Failed to cancel Dagster run: " . $response->body());
        }
    }
}