<?php

namespace App\Jobs;

use App\Models\WorkflowRun;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class TriggerDagsterWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public function __construct(
        private string $workflowType,
        private array $inputData,
        private int $projectId,
        private int $userId,
        private ?int $workflowRunId = null
    ) {
        $this->onQueue('workflows');
    }

    public function handle(): void
    {
        try {
            // Create or update workflow run record
            $workflowRun = $this->workflowRunId 
                ? WorkflowRun::find($this->workflowRunId)
                : $this->createWorkflowRun();

            if (!$workflowRun) {
                throw new \Exception("Workflow run not found or could not be created");
            }

            Log::info('Triggering Dagster workflow', [
                'workflow_type' => $this->workflowType,
                'project_id' => $this->projectId,
                'workflow_run_id' => $workflowRun->id
            ]);

            // Prepare request payload
            $payload = $this->buildPayload($workflowRun);

            // Call Dagster API
            $response = Http::timeout(30)
                ->withHeaders(['Content-Type' => 'application/json'])
                ->post($this->getDagsterEndpoint(), $payload);

            if ($response->successful()) {
                $responseData = $response->json();
                
                $workflowRun->update([
                    'dagster_run_id' => $responseData['run_id'] ?? null,
                    'status' => 'started',
                    'started_at' => now()
                ]);

                Log::info('Dagster workflow started successfully', [
                    'dagster_run_id' => $responseData['run_id'] ?? null,
                    'workflow_run_id' => $workflowRun->id
                ]);

            } else {
                throw new \Exception("Dagster API request failed: " . $response->body());
            }

        } catch (\Exception $e) {
            Log::error('Dagster workflow trigger failed', [
                'error' => $e->getMessage(),
                'workflow_type' => $this->workflowType,
                'project_id' => $this->projectId
            ]);

            if (isset($workflowRun)) {
                $workflowRun->update([
                    'status' => 'failure',
                    'error_message' => $e->getMessage(),
                    'completed_at' => now()
                ]);
            }

            throw $e;
        }
    }

    private function createWorkflowRun(): WorkflowRun
    {
        return WorkflowRun::create([
            'workflow_type' => $this->workflowType,
            'project_id' => $this->projectId,
            'user_id' => $this->userId,
            'input_data' => $this->inputData,
            'status' => 'queued'
        ]);
    }

    private function buildPayload(WorkflowRun $workflowRun): array
    {
        $basePayload = [
            'workflow_type' => $this->workflowType,
            'project_id' => $this->projectId,
            'workflow_run_id' => $workflowRun->id,
            'user_id' => $this->userId,
            'tags' => [
                'project_id' => (string) $this->projectId,
                'user_id' => (string) $this->userId,
                'workflow_run_id' => (string) $workflowRun->id
            ]
        ];

        // Add workflow-specific configuration
        switch ($this->workflowType) {
            case 'schema_ingestion':
                return array_merge($basePayload, [
                    'config' => [
                        'database_schema' => [
                            'config' => [
                                'project_id' => $this->projectId
                            ]
                        ]
                    ]
                ]);

            case 'query_generation':
                return array_merge($basePayload, [
                    'config' => [
                        'sql_query_asset' => [
                            'config' => [
                                'user_query' => $this->inputData['user_query'] ?? '',
                                'project_id' => $this->projectId,
                                'max_results' => $this->inputData['max_results'] ?? 1000
                            ]
                        ]
                    ]
                ]);

            case 'full_pipeline':
                return array_merge($basePayload, [
                    'config' => [
                        'database_schema' => [
                            'config' => [
                                'project_id' => $this->projectId
                            ]
                        ],
                        'sql_query_asset' => [
                            'config' => [
                                'user_query' => $this->inputData['user_query'] ?? '',
                                'project_id' => $this->projectId,
                                'max_results' => $this->inputData['max_results'] ?? 1000
                            ]
                        ]
                    ]
                ]);

            default:
                return $basePayload;
        }
    }

    private function getDagsterEndpoint(): string
    {
        $baseUrl = config('services.dagster.base_url', 'http://localhost:8003');
        return "{$baseUrl}/dagster/trigger";
    }

    public function failed(\Throwable $exception): void
    {
        Log::error('Dagster workflow job failed permanently', [
            'error' => $exception->getMessage(),
            'workflow_type' => $this->workflowType,
            'project_id' => $this->projectId
        ]);

        if ($this->workflowRunId) {
            WorkflowRun::find($this->workflowRunId)?->update([
                'status' => 'failure',
                'error_message' => $exception->getMessage(),
                'completed_at' => now()
            ]);
        }
    }
}