<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class DataSource extends Model
{
    use HasFactory;

    protected $fillable = [
        'name',
        'type',
        'connection_params',
        'description',
        'status',
        'last_connected_at',
        'project_id',
    ];

    protected $casts = [
        'connection_params' => 'array',
        'last_connected_at' => 'datetime',
    ];

    public function project(): BelongsTo
    {
        return $this->belongsTo(Project::class);
    }

    public function mdlModels(): HasMany
    {
        return $this->hasMany(MdlModel::class);
    }
}
