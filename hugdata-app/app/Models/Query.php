<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Query extends Model
{
    use HasFactory, HasUuids;
    
    protected $fillable = [
        'project_id',
        'user_id',
        'natural_language',
        'generated_sql',
        'results',
        'status',
        'execution_time_ms',
        'error_message',
    ];
    
    protected $casts = [
        'results' => 'array',
        'execution_time_ms' => 'integer',
    ];
    
    public function project(): BelongsTo
    {
        return $this->belongsTo(Project::class);
    }
    
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
    
    public function isSuccessful(): bool
    {
        return $this->status === 'success';
    }
    
    public function isFailed(): bool
    {
        return $this->status === 'error';
    }
    
    public function isPending(): bool
    {
        return $this->status === 'pending';
    }
}
