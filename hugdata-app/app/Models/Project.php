<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Project extends Model
{
    use HasFactory, HasUuids;
    
    protected $fillable = ['name', 'description', 'user_id', 'settings'];
    
    protected $casts = [
        'settings' => 'array',
    ];
    
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
    
    public function dataSources(): HasMany
    {
        return $this->hasMany(DataSource::class);
    }
    
    public function queries(): HasMany
    {
        return $this->hasMany(Query::class);
    }
    
    public function semanticModels(): HasMany
    {
        return $this->hasMany(SemanticModel::class);
    }
    
    public function dashboards(): HasMany
    {
        return $this->hasMany(Dashboard::class);
    }
}
