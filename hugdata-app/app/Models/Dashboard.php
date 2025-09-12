<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Dashboard extends Model
{
    use HasFactory, HasUuids;
    
    protected $fillable = [
        'project_id',
        'name',
        'description',
        'configuration'
    ];
    
    protected $casts = [
        'configuration' => 'array'
    ];
    
    public function project(): BelongsTo
    {
        return $this->belongsTo(Project::class);
    }
    
    public function getWidgets(): array
    {
        return $this->configuration['widgets'] ?? [];
    }
    
    public function getLayout(): array
    {
        return $this->configuration['layout'] ?? [];
    }
    
    public function addWidget(array $widget): self
    {
        $widgets = $this->getWidgets();
        $widgets[] = $widget;
        
        $configuration = $this->configuration;
        $configuration['widgets'] = $widgets;
        
        $this->configuration = $configuration;
        return $this;
    }
}
