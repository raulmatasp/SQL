<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Third Party Services
    |--------------------------------------------------------------------------
    |
    | This file is for storing the credentials for third party services such
    | as Mailgun, Postmark, AWS and more. This file provides the de facto
    | location for this type of information, allowing packages to have
    | a conventional file to locate the various service credentials.
    |
    */

    'postmark' => [
        'token' => env('POSTMARK_TOKEN'),
    ],

    'ses' => [
        'key' => env('AWS_ACCESS_KEY_ID'),
        'secret' => env('AWS_SECRET_ACCESS_KEY'),
        'region' => env('AWS_DEFAULT_REGION', 'us-east-1'),
    ],

    'resend' => [
        'key' => env('RESEND_KEY'),
    ],

    'slack' => [
        'notifications' => [
            'bot_user_oauth_token' => env('SLACK_BOT_USER_OAUTH_TOKEN'),
            'channel' => env('SLACK_BOT_USER_DEFAULT_CHANNEL'),
        ],
    ],

    /*
    |--------------------------------------------------------------------------
    | HugData AI Services
    |--------------------------------------------------------------------------
    |
    | Configuration for HugData AI services integration
    |
    */

    'dagster' => [
        'base_url' => env('DAGSTER_API_URL', 'http://localhost:8003'),
        'webserver_url' => env('DAGSTER_WEBSERVER_URL', 'http://localhost:3000'),
        'timeout' => env('DAGSTER_TIMEOUT', 30),
        'enabled' => env('DAGSTER_ENABLED', true),
    ],

    'hugdata_ai' => [
        'base_url' => env('HUGDATA_AI_URL', 'http://localhost:8003'),
        'timeout' => env('HUGDATA_AI_TIMEOUT', 30),
        'api_token' => env('HUGDATA_AI_TOKEN', ''),
    ],

    'openai' => [
        'api_key' => env('OPENAI_API_KEY'),
        'model' => env('OPENAI_MODEL', 'gpt-3.5-turbo'),
        'timeout' => env('OPENAI_TIMEOUT', 30),
    ],

    'weaviate' => [
        'url' => env('WEAVIATE_URL', 'http://localhost:8080'),
        'timeout' => env('WEAVIATE_TIMEOUT', 30),
    ],

    'ai' => [
        'url' => env('AI_SERVICE_URL', 'http://localhost:8003'),
    ],

];
