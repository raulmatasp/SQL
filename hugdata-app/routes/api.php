<?php

use App\Http\Controllers\AuthController;
use App\Http\Controllers\ProjectController;
use App\Http\Controllers\DataSourceController;
use App\Http\Controllers\QueryController;
use App\Http\Controllers\AIController;
use App\Http\Controllers\ChartController;
use App\Http\Controllers\Api\WorkflowController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');

// Authentication routes (no auth required)
Route::prefix('auth')->group(function () {
    Route::post('login', [AuthController::class, 'login']);
    Route::post('register', [AuthController::class, 'register']);
    Route::post('logout', [AuthController::class, 'logout'])->middleware('auth:sanctum');
    Route::get('user', [AuthController::class, 'user'])->middleware('auth:sanctum');
});

// Protected API routes
Route::prefix('v1')->middleware('auth:sanctum')->group(function () {
    // Projects
    Route::apiResource('projects', ProjectController::class);
    
    // Data Sources
    Route::apiResource('projects.data-sources', DataSourceController::class)
        ->names('data-sources')
        ->shallow();
    Route::post('data-sources/{dataSource}/test', [DataSourceController::class, 'testConnection'])
        ->name('data-sources.test');
    Route::get('data-sources/{dataSource}/schema', [DataSourceController::class, 'getSchema'])
        ->name('data-sources.schema');
    
    // Queries
    Route::prefix('queries')->group(function () {
        Route::post('natural-language', [QueryController::class, 'processNaturalLanguage']);
        Route::post('sql', [QueryController::class, 'executeSql']);
        Route::post('suggest-charts', [QueryController::class, 'suggestCharts']);
        Route::get('history', [QueryController::class, 'history']);
        Route::get('{query}', [QueryController::class, 'show']);
    });
    
    // AI Service endpoints
    Route::prefix('ai')->group(function () {
        Route::post('generate-sql', [AIController::class, 'generateSql']);
        Route::post('explain-query', [AIController::class, 'explainQuery']);
        Route::post('suggest-charts', [AIController::class, 'suggestCharts']);
    });
    
    // Chart endpoints
    Route::prefix('charts')->group(function () {
        Route::post('suggest', [ChartController::class, 'suggestCharts']);
        Route::post('generate', [ChartController::class, 'generateChart']);
        Route::post('analyze-trends', [ChartController::class, 'analyzeTrends']);
    });
    
    // Workflow endpoints
    Route::prefix('workflows')->group(function () {
        Route::post('trigger', [WorkflowController::class, 'trigger']);
        Route::get('/', [WorkflowController::class, 'index']);
        Route::get('analytics', [WorkflowController::class, 'analytics']);
        Route::get('{workflowRun}', [WorkflowController::class, 'status']);
        Route::post('{workflowRun}/cancel', [WorkflowController::class, 'cancel']);
    });
});

// Webhook endpoints (no auth required)
Route::prefix('webhooks')->group(function () {
    Route::post('workflows/{workflowRun}/status', [WorkflowController::class, 'updateStatus']);
});