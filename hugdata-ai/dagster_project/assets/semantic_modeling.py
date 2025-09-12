from dagster import asset, AssetExecutionContext
from typing import Dict, Any, List
from ..resources.database import DatabaseResource
from ..resources.llm_provider import LLMProviderResource

@asset(deps=["database_schema"], group_name="semantic_processing")
def semantic_model(
    context: AssetExecutionContext,
    database_schema: Dict[str, Any],
    database_resource: DatabaseResource,
    llm_provider_resource: LLMProviderResource
) -> Dict[str, Any]:
    """
    Create semantic business logic layer on top of raw database schema
    
    This asset processes the database schema to:
    - Discover business relationships and entities
    - Generate calculated fields and metrics
    - Create semantic mappings for natural language queries
    - Build hierarchical business models
    """
    context.log.info("Starting semantic model generation")
    
    project_id = database_schema.get("metadata", {}).get("project_id", "default")
    tables = database_schema.get("tables", {})
    relationships = database_schema.get("relationships", [])
    
    try:
        # 1. Analyze business entities and relationships
        entities = _discover_business_entities(tables, relationships)
        context.log.info(f"Discovered {len(entities)} business entities")
        
        # 2. Generate calculated fields using AI
        calculated_fields = _generate_calculated_fields(entities, llm_provider_resource, context)
        context.log.info(f"Generated {len(calculated_fields)} calculated fields")
        
        # 3. Create business metrics and KPIs
        business_metrics = _create_business_metrics(entities, calculated_fields)
        context.log.info(f"Created {len(business_metrics)} business metrics")
        
        # 4. Build semantic relationships
        semantic_relationships = _build_semantic_relationships(entities, relationships)
        
        # 5. Generate natural language mappings
        nl_mappings = _generate_natural_language_mappings(entities, llm_provider_resource, context)
        
        semantic_model = {
            "project_id": project_id,
            "entities": entities,
            "calculated_fields": calculated_fields,
            "business_metrics": business_metrics,
            "semantic_relationships": semantic_relationships,
            "natural_language_mappings": nl_mappings,
            "metadata": {
                "generated_at": context.instance.get_current_timestamp(),
                "entity_count": len(entities),
                "metric_count": len(business_metrics),
                "mapping_count": len(nl_mappings)
            }
        }
        
        context.log.info("Semantic model generation completed successfully")
        return semantic_model
        
    except Exception as e:
        context.log.error(f"Semantic model generation failed: {str(e)}")
        raise e

def _discover_business_entities(tables: Dict[str, Any], relationships: List[Dict]) -> List[Dict]:
    """Discover and classify business entities from database schema"""
    
    entities = []
    
    for table_name, table_info in tables.items():
        # Classify table as business entity
        entity_type = _classify_entity_type(table_name, table_info)
        
        # Extract business attributes
        attributes = []
        for column in table_info.get("columns", []):
            attr_type = _classify_attribute_type(column)
            attributes.append({
                "name": column.get("name"),
                "type": column.get("type"),
                "business_type": attr_type,
                "nullable": column.get("nullable", True),
                "description": _generate_attribute_description(column.get("name"), attr_type)
            })
        
        entity = {
            "name": table_name,
            "display_name": _generate_display_name(table_name),
            "entity_type": entity_type,
            "attributes": attributes,
            "primary_key": _find_primary_key(table_info),
            "description": _generate_entity_description(table_name, entity_type)
        }
        
        entities.append(entity)
    
    return entities

def _classify_entity_type(table_name: str, table_info: Dict) -> str:
    """Classify table as specific business entity type"""
    name_lower = table_name.lower()
    
    # Core business entities
    if "user" in name_lower or "customer" in name_lower or "client" in name_lower:
        return "customer"
    elif "order" in name_lower or "purchase" in name_lower or "transaction" in name_lower:
        return "transaction"
    elif "product" in name_lower or "item" in name_lower or "inventory" in name_lower:
        return "product"
    elif "payment" in name_lower or "billing" in name_lower or "invoice" in name_lower:
        return "financial"
    elif "employee" in name_lower or "staff" in name_lower:
        return "human_resource"
    elif "campaign" in name_lower or "marketing" in name_lower:
        return "marketing"
    elif "support" in name_lower or "ticket" in name_lower or "issue" in name_lower:
        return "support"
    # Lookup/reference tables
    elif "category" in name_lower or "type" in name_lower or "status" in name_lower:
        return "reference"
    # Log/audit tables
    elif "log" in name_lower or "audit" in name_lower or "history" in name_lower:
        return "audit"
    else:
        return "general"

def _classify_attribute_type(column: Dict) -> str:
    """Classify column as business attribute type"""
    name_lower = column.get("name", "").lower()
    col_type = column.get("type", "").lower()
    
    # Identifiers
    if name_lower == "id" or name_lower.endswith("_id"):
        return "identifier"
    # Names and titles
    elif "name" in name_lower or "title" in name_lower:
        return "name"
    # Contact information
    elif "email" in name_lower:
        return "email"
    elif "phone" in name_lower:
        return "phone"
    elif "address" in name_lower:
        return "address"
    # Temporal data
    elif "date" in name_lower or "time" in name_lower or "timestamp" in col_type:
        return "temporal"
    # Financial data
    elif "amount" in name_lower or "price" in name_lower or "cost" in name_lower or "revenue" in name_lower:
        return "monetary"
    elif "quantity" in name_lower or "count" in name_lower:
        return "quantity"
    # Status and categories
    elif "status" in name_lower or "state" in name_lower:
        return "status"
    elif "category" in name_lower or "type" in name_lower:
        return "category"
    # Descriptions and content
    elif "description" in name_lower or "content" in name_lower or "text" in col_type:
        return "description"
    # Boolean flags
    elif "is_" in name_lower or "has_" in name_lower or "boolean" in col_type:
        return "flag"
    else:
        return "general"

def _generate_calculated_fields(entities: List[Dict], llm_provider: LLMProviderResource, context: AssetExecutionContext) -> List[Dict]:
    """Generate calculated fields using AI analysis"""
    
    calculated_fields = []
    
    for entity in entities[:3]:  # Limit to prevent excessive API calls
        try:
            prompt = f"""
Analyze this business entity and suggest 3-5 useful calculated fields:

Entity: {entity['display_name']} ({entity['entity_type']})
Attributes: {[attr['name'] + ' (' + attr['business_type'] + ')' for attr in entity['attributes']]}

Suggest calculated fields that would be valuable for business analysis.
Format each as:
FIELD_NAME: description | formula_hint | business_value

Example:
CUSTOMER_LIFETIME_VALUE: Total revenue per customer | SUM(order_total) | Revenue optimization
"""
            
            response = llm_provider.generate(prompt, max_tokens=500, temperature=0.3)
            
            # Parse response and extract calculated fields
            fields = _parse_calculated_fields_response(response, entity)
            calculated_fields.extend(fields)
            
        except Exception as e:
            context.log.warning(f"Failed to generate calculated fields for {entity['name']}: {e}")
    
    return calculated_fields

def _parse_calculated_fields_response(response: str, entity: Dict) -> List[Dict]:
    """Parse LLM response to extract calculated field definitions"""
    
    fields = []
    lines = response.split('\n')
    
    for line in lines:
        if ':' in line and '|' in line:
            try:
                parts = line.split('|')
                if len(parts) >= 3:
                    name_desc = parts[0].split(':', 1)
                    if len(name_desc) == 2:
                        field = {
                            "name": name_desc[0].strip(),
                            "entity": entity['name'],
                            "description": name_desc[1].strip(),
                            "formula_hint": parts[1].strip(),
                            "business_value": parts[2].strip(),
                            "type": "calculated"
                        }
                        fields.append(field)
            except Exception:
                continue
    
    return fields

def _create_business_metrics(entities: List[Dict], calculated_fields: List[Dict]) -> List[Dict]:
    """Create standard business metrics and KPIs"""
    
    metrics = []
    
    # Find relevant entities for common metrics
    customer_entities = [e for e in entities if e['entity_type'] == 'customer']
    transaction_entities = [e for e in entities if e['entity_type'] == 'transaction']
    product_entities = [e for e in entities if e['entity_type'] == 'product']
    
    # Revenue metrics
    if transaction_entities:
        metrics.extend([
            {
                "name": "total_revenue",
                "display_name": "Total Revenue",
                "category": "financial",
                "aggregation": "sum",
                "entity": transaction_entities[0]['name'],
                "field": "amount",
                "description": "Sum of all transaction amounts"
            },
            {
                "name": "average_order_value",
                "display_name": "Average Order Value",
                "category": "financial", 
                "aggregation": "average",
                "entity": transaction_entities[0]['name'],
                "field": "amount",
                "description": "Average value per transaction"
            }
        ])
    
    # Customer metrics
    if customer_entities:
        metrics.extend([
            {
                "name": "total_customers",
                "display_name": "Total Customers",
                "category": "customer",
                "aggregation": "count",
                "entity": customer_entities[0]['name'],
                "field": "id",
                "description": "Total number of customers"
            },
            {
                "name": "new_customers",
                "display_name": "New Customers",
                "category": "customer",
                "aggregation": "count",
                "entity": customer_entities[0]['name'],
                "field": "id",
                "filter": "created_at >= date_trunc('month', current_date)",
                "description": "New customers this month"
            }
        ])
    
    # Product metrics
    if product_entities:
        metrics.append({
            "name": "total_products",
            "display_name": "Total Products",
            "category": "product",
            "aggregation": "count",
            "entity": product_entities[0]['name'],
            "field": "id",
            "description": "Total number of products"
        })
    
    return metrics

def _build_semantic_relationships(entities: List[Dict], relationships: List[Dict]) -> List[Dict]:
    """Build semantic relationships with business context"""
    
    semantic_relationships = []
    
    for rel in relationships:
        # Enhanced relationship with semantic meaning
        semantic_rel = {
            "from_entity": rel.get("from_table"),
            "to_entity": rel.get("to_table"),
            "relationship_type": rel.get("type", "references"),
            "semantic_meaning": _infer_relationship_meaning(rel),
            "cardinality": _infer_cardinality(rel),
            "business_rule": _generate_business_rule(rel)
        }
        
        semantic_relationships.append(semantic_rel)
    
    return semantic_relationships

def _generate_natural_language_mappings(entities: List[Dict], llm_provider: LLMProviderResource, context: AssetExecutionContext) -> List[Dict]:
    """Generate natural language to SQL mappings for common queries"""
    
    mappings = []
    
    # Common query patterns
    patterns = [
        "show me all customers",
        "what is the total revenue",
        "how many orders this month",
        "top selling products",
        "customer growth over time"
    ]
    
    for pattern in patterns:
        try:
            # Generate mapping for each pattern
            mapping = {
                "pattern": pattern,
                "intent": _classify_query_intent(pattern),
                "entities_involved": _identify_relevant_entities(pattern, entities),
                "complexity": "simple"
            }
            mappings.append(mapping)
            
        except Exception as e:
            context.log.warning(f"Failed to generate mapping for pattern '{pattern}': {e}")
    
    return mappings

# Helper functions
def _generate_display_name(table_name: str) -> str:
    """Generate human-readable display name"""
    return table_name.replace('_', ' ').title()

def _find_primary_key(table_info: Dict) -> str:
    """Find primary key column"""
    for column in table_info.get("columns", []):
        if column.get("primary_key", False) or column.get("name") == "id":
            return column.get("name")
    return "id"

def _generate_entity_description(table_name: str, entity_type: str) -> str:
    """Generate description for business entity"""
    type_descriptions = {
        "customer": "Customer information and profile data",
        "transaction": "Business transactions and orders",
        "product": "Product catalog and inventory",
        "financial": "Financial and billing information",
        "reference": "Lookup and reference data",
        "audit": "System logs and audit trails"
    }
    return type_descriptions.get(entity_type, f"Data related to {table_name}")

def _generate_attribute_description(name: str, attr_type: str) -> str:
    """Generate description for attribute"""
    type_descriptions = {
        "identifier": "Unique identifier",
        "name": "Name or title",
        "email": "Email address",
        "temporal": "Date/time information",
        "monetary": "Financial amount",
        "status": "Status or state",
        "category": "Category classification"
    }
    return type_descriptions.get(attr_type, f"Data field: {name}")

def _infer_relationship_meaning(rel: Dict) -> str:
    """Infer semantic meaning of database relationship"""
    from_table = rel.get("from_table", "")
    to_table = rel.get("to_table", "")
    
    if "user" in to_table.lower() and "order" in from_table.lower():
        return "customer places orders"
    elif "product" in to_table.lower() and "order" in from_table.lower():
        return "order contains products"
    else:
        return f"{from_table} belongs to {to_table}"

def _infer_cardinality(rel: Dict) -> str:
    """Infer relationship cardinality"""
    # Basic heuristics - could be enhanced with actual FK analysis
    return "many-to-one"

def _generate_business_rule(rel: Dict) -> str:
    """Generate business rule for relationship"""
    return f"Each {rel.get('from_table')} must reference a valid {rel.get('to_table')}"

def _classify_query_intent(pattern: str) -> str:
    """Classify natural language query intent"""
    pattern_lower = pattern.lower()
    
    if "show" in pattern_lower or "list" in pattern_lower:
        return "retrieve"
    elif "total" in pattern_lower or "sum" in pattern_lower:
        return "aggregate"
    elif "count" in pattern_lower or "how many" in pattern_lower:
        return "count"
    elif "top" in pattern_lower or "best" in pattern_lower:
        return "ranking"
    elif "over time" in pattern_lower or "trend" in pattern_lower:
        return "trend"
    else:
        return "general"

def _identify_relevant_entities(pattern: str, entities: List[Dict]) -> List[str]:
    """Identify which entities are relevant for a query pattern"""
    pattern_lower = pattern.lower()
    relevant = []
    
    for entity in entities:
        entity_name = entity['name'].lower()
        entity_type = entity['entity_type']
        
        if entity_name in pattern_lower or entity_type in pattern_lower:
            relevant.append(entity['name'])
    
    return relevant