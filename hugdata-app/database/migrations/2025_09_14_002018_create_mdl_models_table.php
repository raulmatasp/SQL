<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('mdl_models', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->text('mdl_content'); // MDL (Modeling Definition Language) content
            $table->string('hash')->unique();
            $table->json('table_references');
            $table->text('description')->nullable();
            $table->enum('status', ['active', 'draft', 'archived'])->default('draft');
            $table->foreignId('project_id')->constrained()->onDelete('cascade');
            $table->foreignId('data_source_id')->constrained()->onDelete('cascade');
            $table->timestamps();

            $table->index(['project_id', 'status']);
            $table->index('hash');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('mdl_models');
    }
};
