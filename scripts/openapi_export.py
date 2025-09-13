#!/usr/bin/env python3
"""
OpenAPI Export Script

This script exports the FastAPI OpenAPI schema to a static JSON file.
It can be run during build processes to generate documentation.
"""

import json
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from app import app
except ImportError as e:
    print(f"Error importing app: {e}")
    print("Make sure you're running this script from the project root")
    sys.exit(1)


def export_openapi_schema(output_path: str = "openapi.json") -> None:
    """
    Export the OpenAPI schema to a JSON file.
    
    Args:
        output_path: Path where to save the OpenAPI JSON file
    """
    try:
        # Get the OpenAPI schema from the FastAPI app
        openapi_schema = app.openapi()
        
        # Create output directory if it doesn't exist
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the schema to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        
        print(f"✅ OpenAPI schema exported successfully to: {output_file.absolute()}")
        print(f"📊 Schema contains {len(openapi_schema.get('paths', {}))} endpoints")
        print(f"🔧 Schema version: {openapi_schema.get('openapi', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error exporting OpenAPI schema: {e}")
        sys.exit(1)


def main():
    """Main function to handle command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Export FastAPI OpenAPI schema to JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        default="openapi.json",
        help="Output file path (default: openapi.json)"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print the JSON output"
    )
    
    args = parser.parse_args()
    
    # Export the schema
    export_openapi_schema(args.output)
    
    # If pretty print is requested, also show a summary
    if args.pretty:
        try:
            with open(args.output, 'r') as f:
                schema = json.load(f)
            
            print("\n📋 Schema Summary:")
            print(f"  Title: {schema.get('info', {}).get('title', 'N/A')}")
            print(f"  Version: {schema.get('info', {}).get('version', 'N/A')}")
            print(f"  Description: {schema.get('info', {}).get('description', 'N/A')[:100]}...")
            
            paths = schema.get('paths', {})
            print(f"\n🛣️  Endpoints ({len(paths)}):")
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        summary = details.get('summary', 'No summary')
                        print(f"    {method.upper()} {path} - {summary}")
            
            components = schema.get('components', {})
            schemas = components.get('schemas', {})
            print(f"\n📝 Data Models ({len(schemas)}):")
            for name, details in schemas.items():
                print(f"    {name} - {details.get('description', 'No description')[:50]}...")
                
        except Exception as e:
            print(f"Warning: Could not display schema summary: {e}")


if __name__ == "__main__":
    main()