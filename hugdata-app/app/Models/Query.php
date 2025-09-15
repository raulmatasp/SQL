<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasOne;

class Query extends Model
{
    use HasFactory;

    protected $fillable = [
        'query_id',
        'question',
        'sql',
        'sql_generation_reasoning',
        'chart_schema',
        'chart_type',
        'suggested_tables',
        'status',
        'error_message',
        'trace_id',
        'execution_time_ms',
        'thread_id',
        'project_id',
    ];

    protected $casts = [
        'chart_schema' => 'array',
        'suggested_tables' => 'array',
    ];

    public function thread(): BelongsTo
    {
        return $this->belongsTo(Thread::class);
    }

    public function project(): BelongsTo
    {
        return $this->belongsTo(Project::class);
    }

    public function queryResult(): HasOne
    {
        return $this->hasOne(QueryResult::class);
    }
}
