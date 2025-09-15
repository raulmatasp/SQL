<?php

use App\Http\Controllers\Api\ProjectController;
use App\Http\Controllers\Api\QueryController;
use App\Http\Controllers\Api\ThreadController;
use App\Http\Controllers\Api\DataSourceController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->group(function () {
    Route::get('/user', function (Request $request) {
        return $request->user();
    });

    // Projects
    Route::apiResource('projects', ProjectController::class);

    // Data Sources
    Route::apiResource('projects.data-sources', DataSourceController::class);

    // Threads
    Route::apiResource('projects.threads', ThreadController::class);

    // Queries (AI integration)
    Route::apiResource('queries', QueryController::class);
    Route::get('threads/{thread}/queries', [QueryController::class, 'index']);
});