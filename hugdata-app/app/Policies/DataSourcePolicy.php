<?php

namespace App\Policies;

use App\Models\DataSource;
use App\Models\User;

class DataSourcePolicy
{
    public function viewAny(User $user): bool
    {
        return true;
    }

    public function view(User $user, DataSource $dataSource): bool
    {
        return $user->id === $dataSource->project->user_id;
    }

    public function create(User $user): bool
    {
        return true;
    }

    public function update(User $user, DataSource $dataSource): bool
    {
        return $user->id === $dataSource->project->user_id;
    }

    public function delete(User $user, DataSource $dataSource): bool
    {
        return $user->id === $dataSource->project->user_id;
    }

    public function testConnection(User $user, DataSource $dataSource): bool
    {
        return $user->id === $dataSource->project->user_id;
    }

    public function getSchema(User $user, DataSource $dataSource): bool
    {
        return $user->id === $dataSource->project->user_id;
    }
}