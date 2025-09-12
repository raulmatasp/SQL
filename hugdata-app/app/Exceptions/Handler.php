<?php

namespace App\Exceptions;

use Illuminate\Foundation\Exceptions\Handler as ExceptionHandler;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\ValidationException;
use Illuminate\Auth\AuthenticationException;
use Illuminate\Database\Eloquent\ModelNotFoundException;
use Illuminate\Support\Facades\Log;
use Symfony\Component\HttpKernel\Exception\HttpException;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;
use Throwable;

class Handler extends ExceptionHandler
{
    /**
     * The list of the inputs that are never flashed to the session on validation exceptions.
     */
    protected $dontFlash = [
        'current_password',
        'password',
        'password_confirmation',
    ];

    /**
     * Register the exception handling callbacks for the application.
     */
    public function register(): void
    {
        $this->reportable(function (Throwable $e) {
            if (app()->bound('sentry')) {
                app('sentry')->captureException($e);
            }
        });
    }

    /**
     * Render an exception into an HTTP response.
     */
    public function render($request, Throwable $e): JsonResponse|\Illuminate\Http\Response|\Symfony\Component\HttpFoundation\Response
    {
        // Always return JSON for API requests
        if ($request->is('api/*') || $request->wantsJson()) {
            return $this->renderJsonException($request, $e);
        }

        return parent::render($request, $e);
    }

    /**
     * Render exception as JSON response
     */
    private function renderJsonException(Request $request, Throwable $e): JsonResponse
    {
        $response = [
            'success' => false,
            'message' => $e->getMessage() ?: 'An error occurred',
        ];

        $statusCode = 500;

        // Handle specific exception types
        switch (true) {
            case $e instanceof ValidationException:
                $statusCode = 422;
                $response['message'] = 'Validation failed';
                $response['errors'] = $e->errors();
                break;

            case $e instanceof AuthenticationException:
                $statusCode = 401;
                $response['message'] = 'Authentication required';
                break;

            case $e instanceof ModelNotFoundException:
                $statusCode = 404;
                $response['message'] = 'Resource not found';
                break;

            case $e instanceof NotFoundHttpException:
                $statusCode = 404;
                $response['message'] = 'Route not found';
                break;

            case $e instanceof HttpException:
                $statusCode = $e->getStatusCode();
                break;

            case $e instanceof \PDOException:
                $statusCode = 500;
                $response['message'] = 'Database error occurred';
                $this->logDatabaseError($e, $request);
                break;

            case $e instanceof \Exception:
                $this->logApplicationError($e, $request);
                break;
        }

        // Add debug information in non-production environments
        if (config('app.debug') && !app()->environment('production')) {
            $response['debug'] = [
                'exception' => get_class($e),
                'file' => $e->getFile(),
                'line' => $e->getLine(),
                'trace' => collect($e->getTrace())->map(fn ($trace) => [
                    'file' => $trace['file'] ?? 'unknown',
                    'line' => $trace['line'] ?? 'unknown',
                    'function' => $trace['function'] ?? 'unknown',
                    'class' => $trace['class'] ?? null,
                ])->take(5)->toArray()
            ];
        }

        return response()->json($response, $statusCode);
    }

    /**
     * Log database errors with context
     */
    private function logDatabaseError(\PDOException $e, Request $request): void
    {
        Log::error('Database error occurred', [
            'error' => $e->getMessage(),
            'code' => $e->getCode(),
            'url' => $request->fullUrl(),
            'method' => $request->method(),
            'user_id' => $request->user()?->id,
            'ip' => $request->ip(),
            'user_agent' => $request->userAgent(),
            'file' => $e->getFile(),
            'line' => $e->getLine(),
        ]);
    }

    /**
     * Log application errors with context
     */
    private function logApplicationError(\Exception $e, Request $request): void
    {
        $level = $this->determineLogLevel($e);
        
        Log::log($level, 'Application error occurred', [
            'exception' => get_class($e),
            'error' => $e->getMessage(),
            'code' => $e->getCode(),
            'url' => $request->fullUrl(),
            'method' => $request->method(),
            'user_id' => $request->user()?->id,
            'ip' => $request->ip(),
            'user_agent' => $request->userAgent(),
            'file' => $e->getFile(),
            'line' => $e->getLine(),
            'request_data' => $this->sanitizeRequestData($request->all()),
        ]);
    }

    /**
     * Determine appropriate log level based on exception type
     */
    private function determineLogLevel(\Exception $e): string
    {
        if ($e instanceof HttpException) {
            $code = $e->getStatusCode();
            if ($code >= 500) {
                return 'error';
            } elseif ($code >= 400) {
                return 'warning';
            }
        }

        // Critical system errors
        if ($e instanceof \Error || str_contains($e->getMessage(), 'fatal')) {
            return 'critical';
        }

        return 'error';
    }

    /**
     * Sanitize request data for logging (remove sensitive information)
     */
    private function sanitizeRequestData(array $data): array
    {
        $sensitiveKeys = [
            'password',
            'password_confirmation',
            'current_password',
            'token',
            'api_key',
            'secret',
            'connection_config'
        ];

        foreach ($sensitiveKeys as $key) {
            if (isset($data[$key])) {
                $data[$key] = '[REDACTED]';
            }
        }

        // Sanitize nested arrays
        foreach ($data as $key => $value) {
            if (is_array($value)) {
                $data[$key] = $this->sanitizeRequestData($value);
            }
        }

        return $data;
    }

    /**
     * Report or log an exception.
     */
    public function report(Throwable $e): void
    {
        // Add structured logging for better monitoring
        if ($this->shouldReport($e)) {
            $context = [
                'exception' => get_class($e),
                'message' => $e->getMessage(),
                'file' => $e->getFile(),
                'line' => $e->getLine(),
                'user_id' => auth()->id(),
                'request_id' => request()->header('X-Request-ID'),
                'environment' => app()->environment(),
            ];

            // Add performance metrics if available
            if (defined('LARAVEL_START')) {
                $context['response_time'] = round((microtime(true) - LARAVEL_START) * 1000, 2);
            }

            Log::channel('application')->error('Exception reported', $context);
        }

        parent::report($e);
    }
}