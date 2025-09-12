<?php

namespace App\Http\Controllers;

use App\Models\Project;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;

class ProjectController extends Controller
{
    use AuthorizesRequests;

    public function index(Request $request): JsonResponse
    {
        // Skip authorization for now to test the endpoint
        // $this->authorize('viewAny', Project::class);
        
        $projects = $request->user()
            ->projects()
            ->with(['dataSources', 'queries' => fn($q) => $q->latest()->limit(5)])
            ->latest()
            ->paginate(20);

        return response()->json($projects);
    }

    public function store(Request $request): JsonResponse
    {
        // $this->authorize('create', Project::class);
        
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'settings' => 'nullable|array',
        ]);

        $project = Project::create([
            ...$validated,
            'user_id' => $request->user()->id,
            'settings' => $validated['settings'] ?? [],
        ]);

        $project->load(['dataSources', 'queries']);

        return response()->json($project, 201);
    }

    public function show(Request $request, Project $project): JsonResponse
    {
        // $this->authorize('view', $project);

        $project->load([
            'dataSources',
            'queries' => fn($q) => $q->latest()->limit(10),
            'semanticModels',
            'dashboards'
        ]);

        return response()->json($project);
    }

    public function update(Request $request, Project $project): JsonResponse
    {
        // $this->authorize('update', $project);

        $validated = $request->validate([
            'name' => 'sometimes|string|max:255',
            'description' => 'nullable|string',
            'settings' => 'nullable|array',
        ]);

        $project->update($validated);

        return response()->json($project);
    }

    public function destroy(Request $request, Project $project): JsonResponse
    {
        // $this->authorize('delete', $project);

        $project->delete();

        return response()->json(['message' => 'Project deleted successfully']);
    }
}
