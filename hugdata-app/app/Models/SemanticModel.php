<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class SemanticModel extends Model
{
    use HasFactory, HasUuids;
    
    protected $fillable = [
        'project_id',
        'name',
        'table_name',
        'description',
        'definition'
    ];
    
    protected $casts = [
        'definition' => 'array'
    ];
    
    public function project(): BelongsTo
    {
        return $this->belongsTo(Project::class);
    }
    
    public function getCalculatedFields(): array
    {
        return $this->definition['calculated_fields'] ?? [];
    }
    
    public function getRelationships(): array
    {
        return $this->definition['relationships'] ?? [];
    }
    
    public function getColumns(): array
    {
        return $this->definition['columns'] ?? [];
    }
}
