<?php

namespace App\Policies;

use App\Models\Query;
use App\Models\User;

class QueryPolicy
{
    public function viewAny(User $user): bool
    {
        return true;
    }

    public function view(User $user, Query $query): bool
    {
        return $user->id === $query->user_id;
    }

    public function create(User $user): bool
    {
        return true;
    }

    public function update(User $user, Query $query): bool
    {
        return $user->id === $query->user_id;
    }

    public function delete(User $user, Query $query): bool
    {
        return $user->id === $query->user_id;
    }
}