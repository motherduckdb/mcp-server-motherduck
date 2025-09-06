import re
from typing import List
import mcp.types as types
from .. import DatasetPlugin

class TariffsPlugin(DatasetPlugin):
    """USITC Tariffs dataset plugin"""
    
    @property
    def name(self) -> str:
        return "tariffs"
    
    @property
    def description(self) -> str:
        return "USITC Annual Tariff Database"
    
    def get_specialized_tools(self) -> list[types.Tool]:
        """Tariff-specific tools"""
        return [
            types.Tool(
                name="get_tariff_rates",
                description="Get tariff rates for specific products by HTS code or description search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "product_code": {
                            "type": "string", 
                            "description": "HTS product code (e.g., '0101.21.00')"
                        },
                        "product_search": {
                            "type": "string",
                            "description": "Search term for product description (e.g., 'horses', 'automobiles')"
                        },
                        "country": {
                            "type": "string", 
                            "description": "Country name or code (optional)"
                        },
                        "year": {
                            "type": "integer", 
                            "description": "Specific year (2015-2024), defaults to latest available"
                        }
                    }
                }
            ),
            types.Tool(
                name="compare_tariff_rates",
                description="Compare tariff rates across years or for different products",
                inputSchema={
                    "type": "object", 
                    "properties": {
                        "product_code": {
                            "type": "string", 
                            "description": "HTS product code to compare"
                        },
                        "years": {
                            "type": "array", 
                            "items": {"type": "integer"},
                            "description": "Years to compare (e.g., [2020, 2021, 2022])"
                        },
                        "countries": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "Countries to compare (optional)"
                        }
                    },
                    "required": ["product_code"]
                }
            )
        ]
    
    def get_prompts(self) -> list[types.Prompt]:
        """Tariff-specific prompts"""
        return [
            types.Prompt(
                name="tariff-analysis-guide",
                description="Guide for analyzing tariff data and understanding trade patterns"
            ),
            types.Prompt(
                name="hts-code-lookup",
                description="Help with HTS (Harmonized Tariff Schedule) code lookups and product classification"
            )
        ]
    
    def is_dataset_table(self, table_name: str) -> bool:
        """Check if table is a tariff table"""
        return (table_name.startswith("tariff_") or 
                "trade" in table_name.lower() or
                "tariff" in table_name.lower())
    
    def extract_table_metadata(self, table_name: str) -> dict:
        """Extract year and other metadata from tariff table names"""
        # Pattern matches: tariff_2015_tariff_database_2015, tariff_2024_tariff_database_202405, etc.
        year_match = re.search(r'20\d{2}', table_name)
        
        # Try to detect the specific format variations we see in the logs
        metadata = {
            "dataset": "usitc",
            "type": "tariff_data"
        }
        
        if year_match:
            metadata["year"] = year_match.group(0)
        else:
            metadata["year"] = "Unknown"
        
        # Detect if it's a special database format
        if "database" in table_name:
            metadata["format"] = "database"
        elif "trade" in table_name:
            metadata["format"] = "trade"
        else:
            metadata["format"] = "standard"
            
        return metadata
    
    def format_table_list(self, tables: List[str]) -> str:
        """Format tariff table list with year information"""
        output = f"\n📊 {self.description} Tables:\n"
        
        # Sort tables by year for better presentation
        table_info = []
        for table in tables:
            if self.is_dataset_table(table):
                metadata = self.extract_table_metadata(table)
                year = metadata.get('year', 'Unknown')
                table_info.append((table, year))
        
        # Sort by year (newest first)
        table_info.sort(key=lambda x: x[1] if x[1] != 'Unknown' else '0000', reverse=True)
        
        for table, year in table_info:
            output += f"• {table} (Year: {year})\n"
        
        return output

    async def handle_tool_call(self, name: str, arguments: dict, db_client) -> List[types.TextContent]:
        """Handle tariff-specific tool calls"""
        try:
            if name == "get_tariff_rates":
                return await self._handle_get_tariff_rates(arguments, db_client)
            elif name == "compare_tariff_rates":
                return await self._handle_compare_tariff_rates(arguments, db_client)
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Unknown tool: {name}"
                )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Error in {name}: {str(e)}"
            )]
    
    async def handle_prompt_request(self, name: str, arguments: dict = None) -> types.GetPromptResult:
        """Handle tariff-specific prompt requests"""
        if name == "tariff-analysis-guide":
            return get_tariff_analysis_guide()
        elif name == "hts-code-lookup":
            return get_hts_code_help()
        else:
            raise ValueError(f"Unknown prompt: {name}")
    
    async def _handle_get_tariff_rates(self, arguments: dict, db_client) -> List[types.TextContent]:
        """Handle get_tariff_rates tool"""
        product_code = arguments.get("product_code")
        product_search = arguments.get("product_search")
        country = arguments.get("country")
        year = arguments.get("year")
        
        # Build query based on available parameters
        conditions = []
        
        if product_code:
            conditions.append(f"hts8 LIKE '{product_code}%'")
        elif product_search:
            conditions.append(f"lower(brief_description) LIKE '%{product_search.lower()}%'")
        else:
            return [types.TextContent(
                type="text",
                text="❌ Please provide either product_code or product_search"
            )]
        
        if country:
            conditions.append(f"lower(country) LIKE '%{country.lower()}%'")
        
        where_clause = " AND ".join(conditions)
        
        # Find appropriate table
        try:
            tables = await db_client.list_tables()
            tariff_tables = [t for t in tables if self.is_dataset_table(t)]
            
            if not tariff_tables:
                return [types.TextContent(
                    type="text",
                    text="❌ No tariff tables found in database"
                )]
            
            # Select table by year or use most recent
            target_table = None
            if year:
                # Look for table with specific year
                for table in tariff_tables:
                    metadata = self.extract_table_metadata(table)
                    if metadata.get("year") == str(year):
                        target_table = table
                        break
            
            if not target_table:
                # Use most recent table (assume reverse sorted)
                target_table = sorted(tariff_tables)[-1]
            
            # Build and execute query
            query = f"""
            SELECT hts8, brief_description, mfn_text_rate
            FROM {target_table}
            WHERE {where_clause}
            LIMIT 20
            """
            
            result = await db_client.execute_query(query)
            
            return [types.TextContent(
                type="text",
                text=f"🎯 Tariff rates from {target_table}:\n\n{result}"
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Query failed: {str(e)}"
            )]
    
    async def _handle_compare_tariff_rates(self, arguments: dict, db_client) -> List[types.TextContent]:
        """Handle compare_tariff_rates tool"""
        product_code = arguments.get("product_code")
        years = arguments.get("years", [])
        countries = arguments.get("countries", [])
        
        if not product_code:
            return [types.TextContent(
                type="text",
                text="❌ product_code is required for comparison"
            )]
        
        try:
            tables = await db_client.list_tables()
            tariff_tables = [t for t in tables if self.is_dataset_table(t)]
            
            if not years:
                # Use all available years
                years = []
                for table in tariff_tables:
                    metadata = self.extract_table_metadata(table)
                    year = metadata.get("year")
                    if year and year != "Unknown":
                        years.append(int(year))
                years = sorted(set(years))[-5:]  # Last 5 years
            
            # Build comparison query
            union_queries = []
            
            for year in years:
                # Find table for this year
                year_table = None
                for table in tariff_tables:
                    metadata = self.extract_table_metadata(table)
                    if metadata.get("year") == str(year):
                        year_table = table
                        break
                
                if year_table:
                    conditions = [f"hts8 = '{product_code}'"]
                    if countries:
                        country_conditions = [f"lower(country) LIKE '%{country.lower()}%'" for country in countries]
                        conditions.append(f"({' OR '.join(country_conditions)})")
                    
                    where_clause = " AND ".join(conditions)
                    
                    union_queries.append(f"""
                    SELECT '{year}' as year, hts8, brief_description, mfn_text_rate, country
                    FROM {year_table}
                    WHERE {where_clause}
                    """)
            
            if not union_queries:
                return [types.TextContent(
                    type="text",
                    text="❌ No matching tables found for specified years"
                )]
            
            query = " UNION ALL ".join(union_queries) + " ORDER BY year DESC"
            
            result = await db_client.execute_query(query)
            
            return [types.TextContent(
                type="text",
                text=f"📊 Tariff rate comparison for {product_code}:\n\n{result}"
            )]
            
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"❌ Comparison failed: {str(e)}"
            )]

def get_tariff_analysis_guide() -> types.GetPromptResult:
    """Get tariff analysis guidance"""
    guide_text = """Guide for analyzing USITC tariff data:

## Understanding the Data Structure

The USITC tariff database contains annual data with table names like:
- tariff_2015_tariff_database_2015
- tariff_2024_tariff_database_202405

Each table typically contains:
- HTS codes (Harmonized Tariff Schedule codes)
- Product descriptions
- MFN (Most Favored Nation) rates
- Special rates for specific countries
- Country-specific information

## Common Analysis Patterns

1. **Product Lookup**: Search by HTS code or product description
   ```sql
   SELECT hts8, brief_description, mfn_text_rate 
   FROM tariff_2024_tariff_database_202405 
   WHERE hts8 LIKE '0101%' OR lower(brief_description) LIKE '%horse%'
   ```

2. **Year-over-Year Comparison**: Compare rates across years
   ```sql
   SELECT '2023' as year, hts8, mfn_text_rate FROM tariff_2023_...
   UNION ALL
   SELECT '2024' as year, hts8, mfn_text_rate FROM tariff_2024_...
   WHERE hts8 = '0101.21.00'
   ```

3. **Product Category Analysis**: Find all products in a category
   ```sql
   SELECT hts8, brief_description, mfn_text_rate
   FROM tariff_2024_tariff_database_202405
   WHERE hts8 LIKE '01%'  -- Chapter 1: Live animals
   ```

## Tips for Effective Analysis

- Use list_tables to see available years
- Use get_schema to understand column names (they may vary by year)
- Use get_sample_data to see example records before writing complex queries
- HTS codes are hierarchical: 2-digit chapters, 4-digit headings, 6-digit subheadings, 8-digit statistical suffixes
- Product descriptions are searchable but use consistent terminology

## Common HTS Code Patterns

- 01: Live animals
- 02: Meat and edible meat offal  
- 03: Fish and crustaceans
- 84: Nuclear reactors, boilers, machinery
- 85: Electrical machinery and equipment
- 87: Vehicles (automobiles, etc.)

Always start with list_tables and get_schema to understand the current data structure!"""

    return types.GetPromptResult(
        description="Comprehensive guide for analyzing USITC tariff data",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text=guide_text),
            )
        ],
    )

def get_hts_code_help() -> types.GetPromptResult:
    """Get HTS code lookup help"""
    help_text = """HTS (Harmonized Tariff Schedule) Code System Guide:

## Understanding HTS Codes

HTS codes are 8-10 digit product classification codes used for international trade:

### Structure:
- **Chapters (2 digits)**: Broad product categories (01-99)
- **Headings (4 digits)**: More specific product groups  
- **Subheadings (6 digits)**: Detailed product types
- **Statistical Suffixes (8+ digits)**: Country-specific classifications

### Example: 8703.23.00
- 87: Vehicles other than railway/tramway
- 8703: Motor cars and vehicles for transport of persons
- 8703.23: Cylinder capacity > 1500cc but ≤ 3000cc
- 8703.23.00: Specific statistical classification

## Common Chapters:

**Live Animals & Animal Products (01-05)**
- 01: Live animals
- 02: Meat and edible meat offal
- 03: Fish, crustaceans, molluscs
- 04: Dairy products, eggs, honey
- 05: Other animal products

**Vegetable Products (06-14)**
- 06: Live trees, plants, bulbs, cut flowers
- 07: Edible vegetables
- 08: Edible fruit and nuts
- 09: Coffee, tea, spices
- 10: Cereals

**Machinery & Electronics (84-85)**
- 84: Nuclear reactors, boilers, machinery
- 85: Electrical machinery and equipment

**Transportation (86-89)**
- 86: Railway/tramway locomotives, rolling stock
- 87: Vehicles other than railway/tramway
- 88: Aircraft, spacecraft
- 89: Ships, boats

## Search Strategies:

1. **By Product Name**: Search brief_description column
2. **By Chapter**: Use HTS code patterns (e.g., '01%' for live animals)
3. **By Specific Code**: Exact HTS code lookup
4. **By Keyword**: Search product descriptions for terms

## Tips:
- Start broad (2-digit chapter) then narrow down
- Product descriptions use specific trade terminology
- Rates can vary significantly within a chapter
- Always check multiple years for rate changes"""

    return types.GetPromptResult(
        description="Guide to understanding and using HTS codes for product classification",
        messages=[
            types.PromptMessage(
                role="user", 
                content=types.TextContent(type="text", text=help_text),
            )
        ],
    )
