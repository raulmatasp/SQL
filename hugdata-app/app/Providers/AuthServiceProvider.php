<?php

namespace App\Providers;

use App\Models\DataSource;
use App\Models\Project;
use App\Models\Query;
use App\Policies\DataSourcePolicy;
use App\Policies\ProjectPolicy;
use App\Policies\QueryPolicy;
use Illuminate\Foundation\Support\Providers\AuthServiceProvider as ServiceProvider;

class AuthServiceProvider extends ServiceProvider
{
    protected $policies = [
        Project::class => ProjectPolicy::class,
        DataSource::class => DataSourcePolicy::class,
        Query::class => QueryPolicy::class,
    ];

    public function boot(): void
    {
        //
    }
}