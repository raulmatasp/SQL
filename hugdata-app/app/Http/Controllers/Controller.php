<?php

namespace App\Http\Controllers;

/**
 * @OA\Info(
 *      version="1.0.0",
 *      title="HugData API",
 *      description="AI-powered SQL generation and database analytics platform",
 *      @OA\Contact(
 *          email="support@hugdata.com"
 *      )
 * )
 * 
 * @OA\Server(
 *      url=L5_SWAGGER_CONST_HOST,
 *      description="HugData API Server"
 * )
 * 
 * @OA\SecurityScheme(
 *      securityScheme="sanctum",
 *      in="header",
 *      name="Authorization",
 *      type="http",
 *      scheme="bearer",
 *      bearerFormat="JWT",
 * )
 */
abstract class Controller
{
    //
}
