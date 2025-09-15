<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class MdlModel extends Model
{
    use HasFactory;

    protected $fillable = [
        'name',
        'mdl_content',
        'hash',
        'table_references',
        'description',
        'status',
        'project_id',
        'data_source_id',
    ];

    protected $casts = [
        'table_references' => 'array',
    ];

    public function project(): BelongsTo
    {
        return $this->belongsTo(Project::class);
    }

    public function dataSource(): BelongsTo
    {
        return $this->belongsTo(DataSource::class);
    }
}
