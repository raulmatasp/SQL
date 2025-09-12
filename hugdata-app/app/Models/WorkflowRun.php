<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class WorkflowRun extends Model
{
    use HasFactory;

    protected $fillable = [
        'dagster_run_id',
        'status',
        'project_id',
        'user_id',
        'workflow_type',
        'input_data',
        'output_data',
        'error_message',
        'started_at',
        'completed_at'
    ];

    protected $casts = [
        'input_data' => 'array',
        'output_data' => 'array',
        'started_at' => 'datetime',
        'completed_at' => 'datetime'
    ];

    public function project(): BelongsTo
    {
        return $this->belongsTo(Project::class);
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function scopeByStatus($query, string $status)
    {
        return $query->where('status', $status);
    }

    public function scopeByWorkflowType($query, string $type)
    {
        return $query->where('workflow_type', $type);
    }

    public function isRunning(): bool
    {
        return in_array($this->status, ['started', 'in_progress']);
    }

    public function isCompleted(): bool
    {
        return $this->status === 'success';
    }

    public function hasFailed(): bool
    {
        return $this->status === 'failure';
    }
}