<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class QueryResult extends Model
{
    use HasFactory;

    protected $fillable = [
        'data',
        'columns',
        'row_count',
        'execution_time_ms',
        'data_size_bytes',
        'status',
        'error_details',
        'query_id',
    ];

    protected $casts = [
        'data' => 'array',
        'columns' => 'array',
    ];

    public function query(): BelongsTo
    {
        return $this->belongsTo(Query::class);
    }
}
