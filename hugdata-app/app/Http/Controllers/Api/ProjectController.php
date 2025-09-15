<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Project;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;

class ProjectController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $projects = $request->user()->projects()->with('dataSources', 'mdlModels')->get();
        return response()->json($projects);
    }

    public function store(Request $request): JsonResponse
    {
        $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'configuration' => 'nullable|array',
        ]);

        $project = $request->user()->projects()->create($request->all());
        return response()->json($project, 201);
    }

    public function show(string $id): JsonResponse
    {
        $project = Project::with('dataSources', 'mdlModels', 'threads')->findOrFail($id);
        return response()->json($project);
    }

    public function update(Request $request, string $id): JsonResponse
    {
        $project = Project::findOrFail($id);
        $project->update($request->all());
        return response()->json($project);
    }

    public function destroy(string $id): JsonResponse
    {
        $project = Project::findOrFail($id);
        $project->delete();
        return response()->json(['message' => 'Project deleted']);
    }
}
