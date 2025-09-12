<?php

namespace App\Http\Controllers;

use App\Events\QueryShared;
use App\Events\UserJoinedQuery;
use App\Events\UserLeftQuery;
use App\Http\Requests\ShareQueryRequest;
use App\Models\Query;
use App\Models\QueryCollaboration;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;

class CollaborationController extends Controller
{
    public function __construct()
    {
        $this->middleware('auth:sanctum');
    }

    /**
     * Share a query with other users
     */
    public function shareQuery(ShareQueryRequest $request): JsonResponse
    {
        try {
            $user = Auth::user();
            $queryId = $request->validated('query_id');
            $participants = $request->validated('participants', []);
            $permissions = $request->validated('permissions', 'read');

            $query = Query::findOrFail($queryId);
            
            // Check if user owns the query or has edit permissions
            if ($query->user_id !== $user->id && !$this->hasEditPermission($user, $query)) {
                return response()->json(['error' => 'Unauthorized'], 403);
            }

            // Create or update collaboration
            $collaboration = QueryCollaboration::updateOrCreate(
                ['query_id' => $queryId],
                [
                    'owner_id' => $query->user_id,
                    'participants' => $participants,
                    'permissions' => $permissions,
                    'is_active' => true,
                    'expires_at' => $request->validated('expires_at'),
                ]
            );

            // Notify participants
            foreach ($participants as $participantEmail) {
                $participant = User::where('email', $participantEmail)->first();
                if ($participant) {
                    broadcast(new QueryShared($collaboration, $participant));
                }
            }

            Log::channel('hugdata')->info('Query shared', [
                'query_id' => $queryId,
                'shared_by' => $user->id,
                'participants' => $participants
            ]);

            return response()->json([
                'message' => 'Query shared successfully',
                'collaboration' => $collaboration->load(['query', 'owner']),
                'share_url' => route('queries.shared', $collaboration->uuid)
            ]);

        } catch (\Exception $e) {
            Log::channel('hugdata')->error('Failed to share query', [
                'error' => $e->getMessage(),
                'user_id' => Auth::id(),
                'query_id' => $request->input('query_id')
            ]);

            return response()->json(['error' => 'Failed to share query'], 500);
        }
    }

    /**
     * Join a shared query collaboration
     */
    public function joinQuery(Request $request, string $queryId): JsonResponse
    {
        try {
            $user = Auth::user();
            
            $collaboration = QueryCollaboration::where('query_id', $queryId)
                ->where('is_active', true)
                ->firstOrFail();

            // Check if user is allowed to join
            if (!$this->canJoinQuery($user, $collaboration)) {
                return response()->json(['error' => 'Access denied'], 403);
            }

            // Add user to active participants
            $collaboration->increment('active_participants');
            
            // Broadcast user joined event
            broadcast(new UserJoinedQuery($collaboration, $user));

            Log::channel('hugdata')->info('User joined query collaboration', [
                'query_id' => $queryId,
                'user_id' => $user->id,
                'collaboration_id' => $collaboration->id
            ]);

            return response()->json([
                'message' => 'Joined query collaboration',
                'collaboration' => $collaboration->load(['query', 'owner']),
                'participants' => $this->getActiveParticipants($collaboration)
            ]);

        } catch (\Exception $e) {
            Log::channel('hugdata')->error('Failed to join query collaboration', [
                'error' => $e->getMessage(),
                'user_id' => Auth::id(),
                'query_id' => $queryId
            ]);

            return response()->json(['error' => 'Failed to join collaboration'], 500);
        }
    }

    /**
     * Leave a query collaboration
     */
    public function leaveQuery(Request $request, string $queryId): JsonResponse
    {
        try {
            $user = Auth::user();
            
            $collaboration = QueryCollaboration::where('query_id', $queryId)
                ->where('is_active', true)
                ->firstOrFail();

            // Remove user from active participants
            $collaboration->decrement('active_participants');
            
            // Broadcast user left event
            broadcast(new UserLeftQuery($collaboration, $user));

            Log::channel('hugdata')->info('User left query collaboration', [
                'query_id' => $queryId,
                'user_id' => $user->id,
                'collaboration_id' => $collaboration->id
            ]);

            return response()->json([
                'message' => 'Left query collaboration'
            ]);

        } catch (\Exception $e) {
            Log::channel('hugdata')->error('Failed to leave query collaboration', [
                'error' => $e->getMessage(),
                'user_id' => Auth::id(),
                'query_id' => $queryId
            ]);

            return response()->json(['error' => 'Failed to leave collaboration'], 500);
        }
    }

    /**
     * Get shared queries for the current user
     */
    public function getSharedQueries(): JsonResponse
    {
        try {
            $user = Auth::user();
            
            $sharedQueries = QueryCollaboration::whereJsonContains('participants', $user->email)
                ->orWhere('owner_id', $user->id)
                ->where('is_active', true)
                ->with(['query', 'owner'])
                ->get();

            return response()->json([
                'shared_queries' => $sharedQueries
            ]);

        } catch (\Exception $e) {
            Log::channel('hugdata')->error('Failed to get shared queries', [
                'error' => $e->getMessage(),
                'user_id' => Auth::id()
            ]);

            return response()->json(['error' => 'Failed to get shared queries'], 500);
        }
    }

    /**
     * Update query content in real-time collaboration
     */
    public function updateQueryContent(Request $request, string $queryId): JsonResponse
    {
        try {
            $user = Auth::user();
            $content = $request->input('content');
            $version = $request->input('version', 1);

            $collaboration = QueryCollaboration::where('query_id', $queryId)
                ->where('is_active', true)
                ->firstOrFail();

            // Check permissions
            if (!$this->canEditQuery($user, $collaboration)) {
                return response()->json(['error' => 'No edit permission'], 403);
            }

            // Update query content
            $query = $collaboration->query;
            $query->update([
                'content' => $content,
                'version' => $version,
                'last_modified_by' => $user->id,
                'last_modified_at' => now()
            ]);

            // Broadcast content update
            broadcast(new \App\Events\QueryContentUpdated($collaboration, $user, $content, $version));

            return response()->json([
                'message' => 'Query content updated',
                'version' => $version + 1
            ]);

        } catch (\Exception $e) {
            Log::channel('hugdata')->error('Failed to update query content', [
                'error' => $e->getMessage(),
                'user_id' => Auth::id(),
                'query_id' => $queryId
            ]);

            return response()->json(['error' => 'Failed to update content'], 500);
        }
    }

    /**
     * Get collaboration details
     */
    public function getCollaboration(string $queryId): JsonResponse
    {
        try {
            $user = Auth::user();
            
            $collaboration = QueryCollaboration::where('query_id', $queryId)
                ->where('is_active', true)
                ->with(['query', 'owner'])
                ->firstOrFail();

            // Check access
            if (!$this->canViewQuery($user, $collaboration)) {
                return response()->json(['error' => 'Access denied'], 403);
            }

            return response()->json([
                'collaboration' => $collaboration,
                'participants' => $this->getActiveParticipants($collaboration),
                'permissions' => $this->getUserPermissions($user, $collaboration)
            ]);

        } catch (\Exception $e) {
            Log::channel('hugdata')->error('Failed to get collaboration details', [
                'error' => $e->getMessage(),
                'user_id' => Auth::id(),
                'query_id' => $queryId
            ]);

            return response()->json(['error' => 'Failed to get collaboration'], 500);
        }
    }

    /**
     * End collaboration
     */
    public function endCollaboration(string $queryId): JsonResponse
    {
        try {
            $user = Auth::user();
            
            $collaboration = QueryCollaboration::where('query_id', $queryId)
                ->where('owner_id', $user->id)
                ->firstOrFail();

            $collaboration->update(['is_active' => false]);

            // Broadcast collaboration ended
            broadcast(new \App\Events\CollaborationEnded($collaboration));

            return response()->json([
                'message' => 'Collaboration ended'
            ]);

        } catch (\Exception $e) {
            Log::channel('hugdata')->error('Failed to end collaboration', [
                'error' => $e->getMessage(),
                'user_id' => Auth::id(),
                'query_id' => $queryId
            ]);

            return response()->json(['error' => 'Failed to end collaboration'], 500);
        }
    }

    private function hasEditPermission(User $user, Query $query): bool
    {
        $collaboration = QueryCollaboration::where('query_id', $query->id)->first();
        
        if (!$collaboration) {
            return false;
        }

        return in_array($user->email, $collaboration->participants) && 
               in_array($collaboration->permissions, ['edit', 'admin']);
    }

    private function canJoinQuery(User $user, QueryCollaboration $collaboration): bool
    {
        return $collaboration->owner_id === $user->id || 
               in_array($user->email, $collaboration->participants);
    }

    private function canEditQuery(User $user, QueryCollaboration $collaboration): bool
    {
        return $collaboration->owner_id === $user->id || 
               (in_array($user->email, $collaboration->participants) && 
                in_array($collaboration->permissions, ['edit', 'admin']));
    }

    private function canViewQuery(User $user, QueryCollaboration $collaboration): bool
    {
        return $collaboration->owner_id === $user->id || 
               in_array($user->email, $collaboration->participants);
    }

    private function getActiveParticipants(QueryCollaboration $collaboration): array
    {
        // This would typically come from a Redis store or WebSocket connection tracking
        // For now, return the configured participants
        return User::whereIn('email', $collaboration->participants)
                   ->select('id', 'name', 'email', 'avatar')
                   ->get()
                   ->toArray();
    }

    private function getUserPermissions(User $user, QueryCollaboration $collaboration): array
    {
        if ($collaboration->owner_id === $user->id) {
            return ['read', 'edit', 'admin', 'share'];
        }

        if (in_array($user->email, $collaboration->participants)) {
            switch ($collaboration->permissions) {
                case 'admin':
                    return ['read', 'edit', 'admin', 'share'];
                case 'edit':
                    return ['read', 'edit'];
                default:
                    return ['read'];
            }
        }

        return [];
    }
}