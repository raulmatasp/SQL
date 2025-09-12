<?php

use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

Route::get('/', function () {
    return Inertia::render('welcome');
})->name('home');

Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('dashboard', function () {
        return Inertia::render('dashboard');
    })->name('dashboard');
});

// Swagger UI route
Route::get('/docs', function () {
    return view('l5-swagger::index');
});

// API docs JSON endpoint
Route::get('/docs/api-docs.json', function () {
    $jsonPath = storage_path('api-docs/api-docs.json');
    if (file_exists($jsonPath)) {
        return response()->file($jsonPath, [
            'Content-Type' => 'application/json'
        ]);
    }
    return response()->json(['error' => 'API documentation not found'], 404);
});

require __DIR__.'/settings.php';
require __DIR__.'/auth.php';
