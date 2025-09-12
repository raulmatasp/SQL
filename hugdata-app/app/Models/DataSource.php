<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class DataSource extends Model
{
    use HasFactory, HasUuids;
    
    protected $fillable = [
        'project_id', 
        'name', 
        'type', 
        'connection_config', 
        'status', 
        'last_connected_at'
    ];
    
    protected $casts = [
        'connection_config' => 'encrypted:array',
        'last_connected_at' => 'datetime',
    ];
    
    public function project(): BelongsTo
    {
        return $this->belongsTo(Project::class);
    }
    
    public function isActive(): bool
    {
        return $this->status === 'active';
    }
    
    public function markAsConnected(): void
    {
        $this->update([
            'status' => 'active',
            'last_connected_at' => now(),
        ]);
    }
    
    public function markAsDisconnected(): void
    {
        $this->update(['status' => 'inactive']);
    }
}
