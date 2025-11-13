# Automated Documentation Generation

This document outlines the automated tools and scripts for generating, validating, and maintaining documentation in the Career Copilot project.

## Overview

The automated documentation system includes:

- **Code Analysis**: Extract API endpoints, models, and dependencies
- **API Documentation**: Generate OpenAPI specs and documentation
- **Architecture Diagrams**: Auto-update Mermaid diagrams from code
- **Validation**: Check documentation accuracy and completeness
- **CI/CD Integration**: Automated documentation updates in pipelines

## Code Analysis Tools

### API Endpoint Discovery

#### Backend API Scanner
```python
# scripts/analyze_api_endpoints.py
#!/usr/bin/env python3
"""
Automated API endpoint discovery and documentation generation.
Scans FastAPI routes and generates comprehensive API documentation.
"""

import os
import sys
import inspect
import importlib
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from dataclasses import dataclass, asdict

@dataclass
class APIEndpoint:
    """API endpoint metadata"""
    path: str
    method: str
    summary: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Dict[str, Any]]
    tags: List[str]
    file_path: str
    line_number: int

@dataclass
class APIModule:
    """API module containing multiple endpoints"""
    name: str
    endpoints: List[APIEndpoint]
    dependencies: List[str]

class APIAnalyzer:
    """Analyzes FastAPI applications to extract endpoint information"""

    def __init__(self, app_path: str):
        self.app_path = Path(app_path)
        self.endpoints: List[APIEndpoint] = []

    def analyze_app(self) -> List[APIModule]:
        """Analyze the entire FastAPI application"""
        modules = []

        # Find all API route files
        api_files = self._find_api_files()

        for api_file in api_files:
            module = self._analyze_api_file(api_file)
            if module:
                modules.append(module)

        return modules

    def _find_api_files(self) -> List[Path]:
        """Find all API route files"""
        api_files = []
        api_dir = self.app_path / "app" / "api"

        if api_dir.exists():
            for file_path in api_dir.rglob("*.py"):
                if file_path.name != "__init__.py":
                    api_files.append(file_path)

        return api_files

    def _analyze_api_file(self, file_path: Path) -> Optional[APIModule]:
        """Analyze a single API file"""
        try:
            # Import the module
            module_name = self._get_module_name(file_path)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            endpoints = []
            dependencies = []

            # Extract router information
            if hasattr(module, 'router'):
                router = module.router
                endpoints = self._extract_router_endpoints(router, file_path)

            # Extract dependencies
            dependencies = self._extract_dependencies(module)

            if endpoints:
                return APIModule(
                    name=module_name,
                    endpoints=endpoints,
                    dependencies=dependencies
                )

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

        return None

    def _extract_router_endpoints(self, router, file_path: Path) -> List[APIEndpoint]:
        """Extract endpoints from FastAPI router"""
        endpoints = []

        for route in router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                for method in route.methods:
                    endpoint = APIEndpoint(
                        path=route.path,
                        method=method,
                        summary=getattr(route, 'summary', ''),
                        description=getattr(route, 'description', ''),
                        parameters=self._extract_parameters(route),
                        request_body=self._extract_request_body(route),
                        responses=self._extract_responses(route),
                        tags=getattr(route, 'tags', []),
                        file_path=str(file_path),
                        line_number=getattr(route, 'line_number', 0)
                    )
                    endpoints.append(endpoint)

        return endpoints

    def _extract_parameters(self, route) -> List[Dict[str, Any]]:
        """Extract parameter information from route"""
        parameters = []

        # Extract path parameters
        if hasattr(route, 'path'):
            import re
            path_params = re.findall(r'\{([^}]+)\}', route.path)
            for param in path_params:
                parameters.append({
                    'name': param,
                    'in': 'path',
                    'required': True,
                    'schema': {'type': 'string'}
                })

        # Extract query parameters from function signature
        if hasattr(route, 'endpoint'):
            sig = inspect.signature(route.endpoint)
            for param_name, param in sig.parameters.items():
                if param_name not in ['request', 'response', 'db'] and param.default != inspect.Parameter.empty:
                    parameters.append({
                        'name': param_name,
                        'in': 'query',
                        'required': param.default == inspect.Parameter.empty,
                        'schema': {'type': 'string'}
                    })

        return parameters

    def _extract_request_body(self, route) -> Optional[Dict[str, Any]]:
        """Extract request body information"""
        # This would need more sophisticated analysis of Pydantic models
        # For now, return None - would be enhanced with model analysis
        return None

    def _extract_responses(self, route) -> Dict[str, Dict[str, Any]]:
        """Extract response information"""
        responses = {
            '200': {
                'description': 'Successful response'
            }
        }

        # Add error responses
        if hasattr(route, 'responses'):
            responses.update(route.responses)

        return responses

    def _extract_dependencies(self, module) -> List[str]:
        """Extract module dependencies"""
        dependencies = []

        try:
            source = inspect.getsource(module)
            import_lines = [line for line in source.split('\n') if line.strip().startswith('from') or line.strip().startswith('import')]

            for line in import_lines:
                if 'app.' in line:
                    # Extract internal dependencies
                    parts = line.replace('from ', '').replace('import ', '').split()
                    dep = parts[0]
                    if dep.startswith('app.'):
                        dependencies.append(dep)

        except Exception:
            pass

        return list(set(dependencies))

    def _get_module_name(self, file_path: Path) -> str:
        """Get module name from file path"""
        relative_path = file_path.relative_to(self.app_path)
        return str(relative_path).replace('/', '.').replace('.py', '')

def main():
    """Main entry point"""
    analyzer = APIAnalyzer('backend')

    print("🔍 Analyzing API endpoints...")
    modules = analyzer.analyze_app()

    # Generate documentation
    output = {
        'generated_at': '2024-01-15T10:00:00Z',
        'modules': [asdict(module) for module in modules]
    }

    # Save to file
    output_path = Path('docs/api/endpoints.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Generated API documentation for {len(modules)} modules")

    # Generate Markdown documentation
    generate_markdown_docs(modules)

def generate_markdown_docs(modules: List[APIModule]):
    """Generate Markdown documentation from modules"""
    docs_path = Path('docs/api')
    docs_path.mkdir(parents=True, exist_ok=True)

    # Generate index
    with open(docs_path / 'README.md', 'w') as f:
        f.write("# API Documentation\n\n")
        f.write("This documentation is automatically generated from the codebase.\n\n")
        f.write("## Modules\n\n")

        for module in modules:
            f.write(f"- [{module.name}]({module.name}.md)\n")

        f.write(f"\n*Generated on: {modules[0].endpoints[0].generated_at if modules else 'N/A'}*\n")

    # Generate module documentation
    for module in modules:
        with open(docs_path / f"{module.name}.md", 'w') as f:
            f.write(f"# {module.name}\n\n")

            if module.dependencies:
                f.write("## Dependencies\n\n")
                for dep in module.dependencies:
                    f.write(f"- `{dep}`\n")
                f.write("\n")

            f.write("## Endpoints\n\n")

            for endpoint in module.endpoints:
                f.write(f"### {endpoint.method} {endpoint.path}\n\n")

                if endpoint.summary:
                    f.write(f"**{endpoint.summary}**\n\n")

                if endpoint.description:
                    f.write(f"{endpoint.description}\n\n")

                if endpoint.parameters:
                    f.write("**Parameters:**\n\n")
                    for param in endpoint.parameters:
                        required = " (required)" if param.get('required') else ""
                        f.write(f"- `{param['name']}` ({param['in']}){required}\n")
                    f.write("\n")

                if endpoint.responses:
                    f.write("**Responses:**\n\n")
                    for status, response in endpoint.responses.items():
                        f.write(f"- `{status}`: {response.get('description', 'No description')}\n")
                    f.write("\n")

                f.write(f"*Defined in: `{endpoint.file_path}:{endpoint.line_number}`*\n\n")
                f.write("---\n\n")

if __name__ == '__main__':
    main()
```

#### Frontend Component Scanner
```typescript
// scripts/analyze-components.ts
#!/usr/bin/env node
/**
 * Automated React component analysis and documentation generation.
 * Scans TypeScript/React files and generates component documentation.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as ts from 'typescript';

interface ComponentInfo {
  name: string;
  filePath: string;
  props: PropInfo[];
  description?: string;
  examples: string[];
  dependencies: string[];
}

interface PropInfo {
  name: string;
  type: string;
  required: boolean;
  defaultValue?: string;
  description?: string;
}

class ComponentAnalyzer {
  private components: ComponentInfo[] = [];

  analyzeProject(rootPath: string): ComponentInfo[] {
    this.components = [];
    this.scanDirectory(rootPath);
    return this.components;
  }

  private scanDirectory(dirPath: string): void {
    const items = fs.readdirSync(dirPath);

    for (const item of items) {
      const fullPath = path.join(dirPath, item);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory() && !this.shouldSkipDirectory(item)) {
        this.scanDirectory(fullPath);
      } else if (stat.isFile() && this.isReactFile(item)) {
        this.analyzeFile(fullPath);
      }
    }
  }

  private shouldSkipDirectory(dirName: string): boolean {
    return ['node_modules', '.next', 'build', 'dist', '.git'].includes(dirName);
  }

  private isReactFile(fileName: string): boolean {
    return fileName.endsWith('.tsx') || fileName.endsWith('.jsx');
  }

  private analyzeFile(filePath: string): void {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const component = this.extractComponentInfo(content, filePath);

      if (component) {
        this.components.push(component);
      }
    } catch (error) {
      console.error(`Error analyzing ${filePath}:`, error);
    }
  }

  private extractComponentInfo(content: string, filePath: string): ComponentInfo | null {
    // Use TypeScript compiler API for better analysis
    const sourceFile = ts.createSourceFile(
      filePath,
      content,
      ts.ScriptTarget.Latest,
      true
    );

    let componentName: string | null = null;
    const props: PropInfo[] = [];
    let description = '';
    const examples: string[] = [];
    const dependencies: string[] = [];

    // Extract imports for dependencies
    ts.forEachChild(sourceFile, (node) => {
      if (ts.isImportDeclaration(node)) {
        const moduleSpecifier = node.moduleSpecifier.getText().replace(/['"]/g, '');
        if (moduleSpecifier.startsWith('./') || moduleSpecifier.startsWith('../')) {
          dependencies.push(moduleSpecifier);
        }
      }
    });

    // Find component declaration
    ts.forEachChild(sourceFile, (node) => {
      if (ts.isFunctionDeclaration(node) || ts.isArrowFunction(node) || ts.isVariableDeclaration(node)) {
        const name = this.getNodeName(node);
        if (name && this.isReactComponent(content, name)) {
          componentName = name;

          // Extract JSDoc comments
          const jsDoc = this.getJSDocComments(node);
          if (jsDoc) {
            description = jsDoc;
          }

          // Extract props from function parameters or interface
          const componentProps = this.extractProps(node, sourceFile);
          props.push(...componentProps);

          // Extract examples from comments
          const fileExamples = this.extractExamples(content);
          examples.push(...fileExamples);
        }
      }
    });

    if (componentName) {
      return {
        name: componentName,
        filePath,
        props,
        description,
        examples,
        dependencies
      };
    }

    return null;
  }

  private getNodeName(node: ts.Node): string | null {
    if (ts.isFunctionDeclaration(node) && node.name) {
      return node.name.text;
    }

    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name)) {
      return node.name.text;
    }

    return null;
  }

  private isReactComponent(content: string, name: string): boolean {
    // Check if component uses React patterns
    const patterns = [
      `export.*${name}`,
      `function ${name}`,
      `const ${name}`,
      `${name}.propTypes`,
      `React\\.forwardRef.*${name}`,
    ];

    return patterns.some(pattern => new RegExp(pattern).test(content));
  }

  private getJSDocComments(node: ts.Node): string {
    const jsDoc = (node as any).jsDoc;
    if (jsDoc && jsDoc.length > 0) {
      return jsDoc[0].comment || '';
    }
    return '';
  }

  private extractProps(node: ts.Node, sourceFile: ts.SourceFile): PropInfo[] {
    const props: PropInfo[] = [];

    // Look for interface or type alias with Props
    ts.forEachChild(sourceFile, (child) => {
      if (ts.isInterfaceDeclaration(child) || ts.isTypeAliasDeclaration(child)) {
        const name = child.name.text;
        if (name.includes('Props') || name.includes('Prop')) {
          if (ts.isInterfaceDeclaration(child)) {
            for (const member of child.members) {
              if (ts.isPropertySignature(member)) {
                const prop = this.extractPropFromSignature(member);
                if (prop) {
                  props.push(prop);
                }
              }
            }
          }
        }
      }
    });

    // Also check function parameters
    if (ts.isFunctionDeclaration(node) || ts.isArrowFunction(node)) {
      const parameters = node.parameters;
      for (const param of parameters) {
        if (ts.isParameter(param) && param.name && ts.isIdentifier(param.name)) {
          const paramName = param.name.text;
          if (paramName !== 'children' && !paramName.startsWith('_')) {
            props.push({
              name: paramName,
              type: param.type ? param.type.getText() : 'any',
              required: !param.questionToken && !param.initializer,
              description: this.getParamDescription(node, paramName)
            });
          }
        }
      }
    }

    return props;
  }

  private extractPropFromSignature(member: ts.PropertySignature): PropInfo | null {
    if (member.name && ts.isIdentifier(member.name)) {
      return {
        name: member.name.text,
        type: member.type ? member.type.getText() : 'any',
        required: !member.questionToken,
        defaultValue: member.initializer ? member.initializer.getText() : undefined,
        description: this.getJSDocComments(member)
      };
    }
    return null;
  }

  private getParamDescription(node: ts.Node, paramName: string): string {
    const jsDoc = this.getJSDocComments(node);
    // Simple extraction - could be enhanced with proper JSDoc parsing
    const lines = jsDoc.split('\n');
    for (const line of lines) {
      if (line.includes(`@${paramName}`) || line.includes(`@param ${paramName}`)) {
        return line.replace(`@${paramName}`, '').replace(`@param ${paramName}`, '').trim();
      }
    }
    return '';
  }

  private extractExamples(content: string): string[] {
    const examples: string[] = [];
    const exampleRegex = /\/\/\s*@example\s*\n([\s\S]*?)(?=\n\s*(\/\/\s*@|\n\s*$))/g;

    let match;
    while ((match = exampleRegex.exec(content)) !== null) {
      examples.push(match[1].trim());
    }

    return examples;
  }
}

function generateMarkdownDocs(components: ComponentInfo[]): void {
  const docsDir = path.join('docs', 'components');
  fs.mkdirSync(docsDir, { recursive: true });

  // Generate index
  const indexContent = `# Component Documentation

This documentation is automatically generated from the React component codebase.

## Components

${components.map(comp => `- [${comp.name}](${comp.name}.md)`).join('\n')}

*Generated on: ${new Date().toISOString()}*
`;

  fs.writeFileSync(path.join(docsDir, 'README.md'), indexContent);

  // Generate individual component docs
  for (const component of components) {
    const content = `# ${component.name}

**File:** \`${component.filePath}\`

${component.description ? `## Description\n\n${component.description}\n\n` : ''}

## Props

${component.props.length > 0 ?
  component.props.map(prop => `
### \`${prop.name}\`
- **Type:** \`${prop.type}\`
- **Required:** ${prop.required ? 'Yes' : 'No'}
${prop.defaultValue ? `- **Default:** \`${prop.defaultValue}\`` : ''}
${prop.description ? `- **Description:** ${prop.description}` : ''}
`).join('\n') :
  'No props defined.'
}

${component.dependencies.length > 0 ? `
## Dependencies

${component.dependencies.map(dep => `- \`${dep}\``).join('\n')}
` : ''}

${component.examples.length > 0 ? `
## Examples

${component.examples.map((example, i) => `
### Example ${i + 1}

\`\`\`tsx
${example}
\`\`\`
`).join('\n')}
` : ''}

---
*Auto-generated from component source*
`;

    const fileName = `${component.name}.md`;
    fs.writeFileSync(path.join(docsDir, fileName), content);
  }
}

function main(): void {
  const analyzer = new ComponentAnalyzer();
  console.log('🔍 Analyzing React components...');

  const components = analyzer.analyzeProject('frontend/src');

  console.log(`✅ Found ${components.length} components`);

  // Save JSON data
  const outputPath = path.join('docs', 'components.json');
  fs.writeFileSync(outputPath, JSON.stringify({
    generated_at: new Date().toISOString(),
    components: components
  }, null, 2));

  // Generate Markdown docs
  generateMarkdownDocs(components);

  console.log('✅ Generated component documentation');
}

// Run if called directly
if (require.main === module) {
  main();
}
```

### Database Schema Analyzer

#### Schema Documentation Generator
```python
# scripts/analyze_database_schema.py
#!/usr/bin/env python3
"""
Automated database schema analysis and documentation generation.
Analyzes SQLAlchemy models and generates comprehensive schema documentation.
"""

import os
import sys
import inspect
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
import json
from dataclasses import dataclass, asdict
from datetime import datetime

# Add backend to path
sys.path.insert(0, 'backend')

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship

@dataclass
class TableInfo:
    """Database table metadata"""
    name: str
    class_name: str
    file_path: str
    columns: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    indexes: List[Dict[str, Any]]
    description: str = ""

@dataclass
class SchemaInfo:
    """Complete database schema information"""
    tables: List[TableInfo]
    generated_at: str

class SchemaAnalyzer:
    """Analyzes SQLAlchemy models to extract schema information"""

    def __init__(self, models_path: str):
        self.models_path = Path(models_path)
        self.tables: List[TableInfo] = []

    def analyze_schema(self) -> SchemaInfo:
        """Analyze all SQLAlchemy models"""
        self.tables = []

        # Find all model files
        model_files = self._find_model_files()

        for model_file in model_files:
            tables = self._analyze_model_file(model_file)
            self.tables.extend(tables)

        return SchemaInfo(
            tables=self.tables,
            generated_at=datetime.utcnow().isoformat()
        )

    def _find_model_files(self) -> List[Path]:
        """Find all model definition files"""
        model_files = []

        if self.models_path.exists():
            for file_path in self.models_path.rglob("*.py"):
                if file_path.name != "__init__.py":
                    model_files.append(file_path)

        return model_files

    def _analyze_model_file(self, file_path: Path) -> List[TableInfo]:
        """Analyze a single model file"""
        tables = []

        try:
            # Import the module
            module_name = self._get_module_name(file_path)
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find all SQLAlchemy model classes
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and
                    hasattr(obj, '__tablename__') and
                    hasattr(obj, '__table__')):

                    table_info = self._analyze_model_class(obj, file_path)
                    if table_info:
                        tables.append(table_info)

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

        return tables

    def _analyze_model_class(self, model_class: Type, file_path: Path) -> Optional[TableInfo]:
        """Analyze a single SQLAlchemy model class"""
        try:
            table_name = getattr(model_class, '__tablename__', None)
            if not table_name:
                return None

            # Extract columns
            columns = self._extract_columns(model_class)

            # Extract relationships
            relationships = self._extract_relationships(model_class)

            # Extract indexes
            indexes = self._extract_indexes(model_class)

            # Extract description from docstring
            description = getattr(model_class, '__doc__', '') or ''

            return TableInfo(
                name=table_name,
                class_name=model_class.__name__,
                file_path=str(file_path),
                columns=columns,
                relationships=relationships,
                indexes=indexes,
                description=description.strip()
            )

        except Exception as e:
            print(f"Error analyzing model {model_class.__name__}: {e}")
            return None

    def _extract_columns(self, model_class: Type) -> List[Dict[str, Any]]:
        """Extract column information from model"""
        columns = []

        # Get table columns
        table = getattr(model_class, '__table__', None)
        if table:
            for column in table.columns:
                column_info = {
                    'name': column.name,
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'primary_key': column.primary_key,
                    'unique': column.unique,
                    'default': str(column.default) if column.default else None,
                    'foreign_keys': [fk.target_fullname for fk in column.foreign_keys]
                }
                columns.append(column_info)

        return columns

    def _extract_relationships(self, model_class: Type) -> List[Dict[str, Any]]:
        """Extract relationship information"""
        relationships = []

        # Check for relationship attributes
        for attr_name in dir(model_class):
            if not attr_name.startswith('_'):
                attr_value = getattr(model_class, attr_name)
                if hasattr(attr_value, 'mapper') and hasattr(attr_value, 'table'):
                    # This is a relationship
                    relationship_info = {
                        'name': attr_name,
                        'target_table': attr_value.table.name,
                        'relationship_type': 'one-to-many',  # Default assumption
                        'backref': getattr(attr_value, 'backref', None)
                    }
                    relationships.append(relationship_info)

        return relationships

    def _extract_indexes(self, model_class: Type) -> List[Dict[str, Any]]:
        """Extract index information"""
        indexes = []

        table = getattr(model_class, '__table__', None)
        if table and hasattr(table, 'indexes'):
            for index in table.indexes:
                index_info = {
                    'name': index.name,
                    'columns': [col.name for col in index.columns],
                    'unique': index.unique
                }
                indexes.append(index_info)

        return indexes

    def _get_module_name(self, file_path: Path) -> str:
        """Get module name from file path"""
        return str(file_path).replace('/', '.').replace('.py', '')

def generate_markdown_docs(schema: SchemaInfo):
    """Generate Markdown documentation from schema"""
    docs_path = Path('docs/database')
    docs_path.mkdir(parents=True, exist_ok=True)

    # Generate index
    with open(docs_path / 'README.md', 'w') as f:
        f.write("# Database Schema Documentation\n\n")
        f.write("This documentation is automatically generated from SQLAlchemy models.\n\n")
        f.write("## Tables\n\n")

        for table in schema.tables:
            f.write(f"- [{table.name}]({table.name}.md) - {table.class_name}\n")

        f.write(f"\n## Summary\n\n")
        f.write(f"- **Total Tables:** {len(schema.tables)}\n")
        f.write(f"- **Generated:** {schema.generated_at}\n")

    # Generate table documentation
    for table in schema.tables:
        with open(docs_path / f"{table.name}.md", 'w') as f:
            f.write(f"# {table.name}\n\n")
            f.write(f"**Model Class:** `{table.class_name}`\n\n")
            f.write(f"**File:** `{table.file_path}`\n\n")

            if table.description:
                f.write(f"## Description\n\n{table.description}\n\n")

            f.write("## Columns\n\n")
            f.write("| Column | Type | Nullable | Primary Key | Unique | Default | Foreign Keys |\n")
            f.write("|--------|------|----------|-------------|--------|---------|--------------|\n")

            for col in table.columns:
                fk_str = ', '.join(col['foreign_keys']) if col['foreign_keys'] else '-'
                f.write(f"| {col['name']} | {col['type']} | {col['nullable']} | {col['primary_key']} | {col['unique']} | {col['default'] or '-'} | {fk_str} |\n")

            f.write("\n")

            if table.relationships:
                f.write("## Relationships\n\n")
                for rel in table.relationships:
                    f.write(f"- **{rel['name']}**: {rel['relationship_type']} relationship with `{rel['target_table']}`\n")
                f.write("\n")

            if table.indexes:
                f.write("## Indexes\n\n")
                for idx in table.indexes:
                    unique_str = " (unique)" if idx['unique'] else ""
                    f.write(f"- **{idx['name']}**: {', '.join(idx['columns'])}{unique_str}\n")
                f.write("\n")

            f.write("---\n\n")
            f.write("*Auto-generated from SQLAlchemy model*")

def main():
    """Main entry point"""
    analyzer = SchemaAnalyzer('backend/app/models')

    print("🔍 Analyzing database schema...")
    schema = analyzer.analyze_schema()

    # Save JSON data
    output_path = Path('docs/database/schema.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(asdict(schema), f, indent=2)

    print(f"✅ Analyzed {len(schema.tables)} database tables")

    # Generate Markdown documentation
    generate_markdown_docs(schema)

    print("✅ Generated database schema documentation")

if __name__ == '__main__':
    main()
```

## API Documentation Generation

### OpenAPI Specification Generator

#### Enhanced OpenAPI Generator
```python
# scripts/generate_openapi_docs.py
#!/usr/bin/env python3
"""
Enhanced OpenAPI specification generator for FastAPI applications.
Generates comprehensive API documentation with examples and validation.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import yaml

# Add backend to path
sys.path.insert(0, 'backend')

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.main import app  # Import the FastAPI app

def enhance_openapi_spec(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance the OpenAPI spec with additional metadata and examples"""

    # Add server information
    openapi_schema['servers'] = [
        {
            'url': 'https://api.careercopilot.com',
            'description': 'Production server'
        },
        {
            'url': 'http://localhost:8000',
            'description': 'Development server'
        }
    ]

    # Add security schemes
    openapi_schema['components']['securitySchemes'] = {
        'bearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT'
        }
    }

    # Apply security globally
    openapi_schema['security'] = [
        {'bearerAuth': []}
    ]

    # Enhance path operations with examples
    for path, methods in openapi_schema['paths'].items():
        for method, operation in methods.items():
            enhance_operation_with_examples(operation, path, method)

    # Add custom tags
    openapi_schema['tags'] = [
        {
            'name': 'Authentication',
            'description': 'User authentication and authorization'
        },
        {
            'name': 'Users',
            'description': 'User management operations'
        },
        {
            'name': 'Jobs',
            'description': 'Job posting management'
        },
        {
            'name': 'Applications',
            'description': 'Job application tracking'
        },
        {
            'name': 'Analytics',
            'description': 'Application analytics and insights'
        }
    ]

    return openapi_schema

def enhance_operation_with_examples(operation: Dict[str, Any], path: str, method: str):
    """Add request/response examples to an operation"""

    # Add request examples
    if 'requestBody' in operation:
        content = operation['requestBody'].get('content', {})
        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            examples = generate_request_examples(path, method, schema)
            if examples:
                content['application/json']['examples'] = examples

    # Add response examples
    if 'responses' in operation:
        for status_code, response in operation['responses'].items():
            if status_code.startswith('2'):  # Success responses
                content = response.get('content', {})
                if 'application/json' in content:
                    examples = generate_response_examples(path, method, status_code)
                    if examples:
                        content['application/json']['examples'] = examples

def generate_request_examples(path: str, method: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate request examples based on path and schema"""

    examples = {}

    # Authentication examples
    if '/auth/login' in path:
        examples['user_login'] = {
            'summary': 'User login',
            'value': {
                'username': 'user@example.com',
                'password': 'securepassword123'
            }
        }

    elif '/auth/register' in path:
        examples['user_registration'] = {
            'summary': 'User registration',
            'value': {
                'email': 'newuser@example.com',
                'password': 'securepassword123',
                'full_name': 'John Doe'
            }
        }

    # Job examples
    elif '/jobs' in path and method == 'post':
        examples['create_job'] = {
            'summary': 'Create job posting',
            'value': {
                'title': 'Senior Software Engineer',
                'company': 'Tech Corp',
                'description': 'We are looking for a senior software engineer...',
                'location': 'San Francisco, CA',
                'salary_range': '$120k - $160k',
                'job_type': 'full-time',
                'requirements': ['5+ years experience', 'React', 'Node.js']
            }
        }

    # Application examples
    elif '/applications' in path and method == 'post':
        examples['create_application'] = {
            'summary': 'Create job application',
            'value': {
                'job_id': 123,
                'cover_letter': 'I am excited to apply for this position...',
                'resume_url': 'https://example.com/resume.pdf',
                'availability_date': '2024-02-01'
            }
        }

    return examples

def generate_response_examples(path: str, method: str, status_code: str) -> Dict[str, Any]:
    """Generate response examples"""

    examples = {}

    # Authentication responses
    if '/auth/login' in path and status_code == '200':
        examples['successful_login'] = {
            'summary': 'Successful login',
            'value': {
                'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                'token_type': 'bearer',
                'expires_in': 3600,
                'user': {
                    'id': 123,
                    'email': 'user@example.com',
                    'full_name': 'John Doe'
                }
            }
        }

    # Job responses
    elif '/jobs' in path and method == 'get' and status_code == '200':
        examples['job_list'] = {
            'summary': 'Job listings',
            'value': {
                'items': [
                    {
                        'id': 1,
                        'title': 'Software Engineer',
                        'company': 'Tech Corp',
                        'location': 'Remote',
                        'salary_range': '$80k - $120k',
                        'posted_date': '2024-01-15T10:00:00Z',
                        'status': 'active'
                    }
                ],
                'total': 1,
                'page': 1,
                'page_size': 20
            }
        }

    # Application responses
    elif '/applications' in path and method == 'get' and status_code == '200':
        examples['application_list'] = {
            'summary': 'Application list',
            'value': {
                'items': [
                    {
                        'id': 1,
                        'job_id': 123,
                        'job_title': 'Software Engineer',
                        'company': 'Tech Corp',
                        'status': 'under_review',
                        'applied_date': '2024-01-15T10:00:00Z',
                        'last_updated': '2024-01-16T14:30:00Z'
                    }
                ],
                'total': 1
            }
        }

    return examples

def generate_postman_collection(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Postman collection from OpenAPI spec"""

    collection = {
        'info': {
            'name': 'Career Copilot API',
            'description': 'API collection for Career Copilot application',
            'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
        },
        'item': [],
        'variable': [
            {
                'key': 'baseUrl',
                'value': 'http://localhost:8000',
                'type': 'string'
            },
            {
                'key': 'token',
                'value': '',
                'type': 'string'
            }
        ]
    }

    # Convert OpenAPI paths to Postman requests
    for path, methods in openapi_schema['paths'].items():
        for method, operation in methods.items():
            request = {
                'name': operation.get('summary', f'{method.upper()} {path}'),
                'request': {
                    'method': method.upper(),
                    'header': [
                        {
                            'key': 'Content-Type',
                            'value': 'application/json'
                        }
                    ],
                    'url': {
                        'raw': '{{baseUrl}}' + path,
                        'host': ['{{baseUrl}}'],
                        'path': path.split('/')[1:]  # Remove leading slash
                    }
                }
            }

            # Add authorization header for protected routes
            if not any(tag in ['Authentication'] for tag in operation.get('tags', [])):
                request['request']['header'].append({
                    'key': 'Authorization',
                    'value': 'Bearer {{token}}'
                })

            # Add request body if present
            if 'requestBody' in operation:
                content = operation['requestBody'].get('content', {})
                if 'application/json' in content:
                    examples = content.get('examples', {})
                    if examples:
                        # Use first example
                        example_name = list(examples.keys())[0]
                        request['request']['body'] = {
                            'mode': 'raw',
                            'raw': json.dumps(examples[example_name]['value'], indent=2)
                        }

            collection['item'].append(request)

    return collection

def main():
    """Generate comprehensive API documentation"""

    print("🔍 Generating OpenAPI specification...")

    # Generate base OpenAPI spec
    openapi_schema = get_openapi(
        title="Career Copilot API",
        version="1.0.0",
        description="AI-powered job application tracking and career management platform",
        routes=app.routes,
    )

    # Enhance the specification
    enhanced_schema = enhance_openapi_spec(openapi_schema)

    # Save OpenAPI JSON
    docs_path = Path('docs/api')
    docs_path.mkdir(parents=True, exist_ok=True)

    with open(docs_path / 'openapi.json', 'w') as f:
        json.dump(enhanced_schema, f, indent=2)

    # Save OpenAPI YAML
    with open(docs_path / 'openapi.yaml', 'w') as f:
        yaml.dump(enhanced_schema, f, default_flow_style=False)

    print("✅ Generated OpenAPI specification")

    # Generate Postman collection
    postman_collection = generate_postman_collection(enhanced_schema)

    with open(docs_path / 'postman_collection.json', 'w') as f:
        json.dump(postman_collection, f, indent=2)

    print("✅ Generated Postman collection")

    # Generate HTML documentation
    generate_html_docs(enhanced_schema, docs_path)

    print("✅ Generated HTML documentation")

def generate_html_docs(openapi_schema: Dict[str, Any], docs_path: Path):
    """Generate HTML documentation"""

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Career Copilot API Documentation</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.7.2/swagger-ui.css" />
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.7.2/swagger-ui-bundle.js"></script>
    <script>
        const spec = {json.dumps(openapi_schema)};
        const ui = SwaggerUIBundle({{
            spec: spec,
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.presets.standalone
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ],
            layout: "BaseLayout"
        }});
    </script>
</body>
</html>
"""

    with open(docs_path / 'index.html', 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    main()
```

## Architecture Diagram Generation

### Mermaid Diagram Auto-Update

#### Diagram Validation and Update Script
```python
# scripts/update_architecture_diagrams.py
#!/usr/bin/env python3
"""
Automated architecture diagram validation and update system.
Validates Mermaid diagrams and updates them based on code analysis.
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Set
from dataclasses import dataclass
import subprocess

@dataclass
class DiagramValidationResult:
    """Result of diagram validation"""
    file_path: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    outdated_components: List[str]

@dataclass
class ComponentReference:
    """Reference to a component in the codebase"""
    name: str
    type: str  # 'service', 'model', 'endpoint', 'component'
    file_path: str
    last_modified: str

class ArchitectureDiagramManager:
    """Manages architecture diagram validation and updates"""

    def __init__(self):
        self.docs_path = Path('docs/architecture')
        self.backend_path = Path('backend')
        self.frontend_path = Path('frontend')

    def validate_all_diagrams(self) -> List[DiagramValidationResult]:
        """Validate all architecture diagrams"""
        results = []

        if not self.docs_path.exists():
            return results

        for diagram_file in self.docs_path.glob('*.md'):
            if diagram_file.name.endswith('.md'):
                result = self.validate_diagram(diagram_file)
                results.append(result)

        return results

    def validate_diagram(self, diagram_file: Path) -> DiagramValidationResult:
        """Validate a single diagram file"""
        errors = []
        warnings = []
        outdated_components = []

        try:
            content = diagram_file.read_text()

            # Extract Mermaid code blocks
            mermaid_blocks = re.findall(r'```mermaid\s*\n(.*?)\n```', content, re.DOTALL)

            for block in mermaid_blocks:
                # Validate Mermaid syntax
                syntax_errors = self.validate_mermaid_syntax(block)
                errors.extend(syntax_errors)

                # Check for outdated component references
                outdated = self.check_outdated_components(block)
                outdated_components.extend(outdated)

            # Check WikiLinks
            wikilink_warnings = self.validate_wikilinks(content)
            warnings.extend(wikilink_warnings)

        except Exception as e:
            errors.append(f"Failed to read diagram file: {e}")

        return DiagramValidationResult(
            file_path=str(diagram_file),
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            outdated_components=outdated_components
        )

    def validate_mermaid_syntax(self, mermaid_code: str) -> List[str]:
        """Validate Mermaid diagram syntax"""
        errors = []

        # Basic syntax checks
        lines = mermaid_code.strip().split('\n')

        if not lines[0].strip().startswith(('graph', 'flowchart', 'sequenceDiagram', 'classDiagram')):
            errors.append("Invalid diagram type declaration")

        # Check for common syntax errors
        bracket_count = 0
        brace_count = 0

        for line in lines:
            bracket_count += line.count('[') - line.count(']')
            brace_count += line.count('{') - line.count('}')

        if bracket_count != 0:
            errors.append("Unmatched square brackets")

        if brace_count != 0:
            errors.append("Unmatched curly braces")

        # Check for invalid node definitions
        for line in lines:
            if '-->' in line or '->' in line:
                parts = line.split('-->') if '-->' in line else line.split('->')
                if len(parts) != 2:
                    errors.append(f"Invalid connection syntax: {line.strip()}")

        return errors

    def check_outdated_components(self, mermaid_code: str) -> List[str]:
        """Check for outdated component references in diagram"""
        outdated = []

        # Extract component names from diagram
        component_pattern = r'(\w+)\[([^\]]+)\]'
        matches = re.findall(component_pattern, mermaid_code)

        current_components = self.get_current_components()

        for node_id, label in matches:
            if node_id not in current_components:
                # Check if it's a known component with different name
                if not any(comp['name'].lower().replace(' ', '') == node_id.lower()
                          for comp in current_components.values()):
                    outdated.append(f"Unknown component: {node_id}")

        return outdated

    def validate_wikilinks(self, content: str) -> List[str]:
        """Validate WikiLinks in the document"""
        warnings = []

        # Find all WikiLinks
        wikilink_pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(wikilink_pattern, content)

        for link in matches:
            # Check if linked file exists
            link_path = self.docs_path / f"{link}.md"
            if not link_path.exists():
                # Also check in subdirectories
                found = False
                for subdir in ['architecture', 'development', 'api', 'database']:
                    subdir_path = self.docs_path / subdir / f"{link}.md"
                    if subdir_path.exists():
                        found = True
                        break

                if not found:
                    warnings.append(f"Broken WikiLink: [[{link}]]")

        return warnings

    def get_current_components(self) -> Dict[str, Dict[str, Any]]:
        """Get current components from codebase analysis"""
        components = {}

        # Analyze backend services
        if self.backend_path.exists():
            for service_file in (self.backend_path / 'app' / 'services').glob('*.py'):
                if service_file.name != '__init__.py':
                    components[service_file.stem] = {
                        'name': service_file.stem.replace('_', ' ').title(),
                        'type': 'service',
                        'file_path': str(service_file),
                        'last_modified': self.get_file_modification_time(service_file)
                    }

        # Analyze frontend components
        if self.frontend_path.exists():
            for component_file in (self.frontend_path / 'src' / 'components').rglob('*.tsx'):
                component_name = component_file.stem
                components[component_name.lower()] = {
                    'name': component_name,
                    'type': 'component',
                    'file_path': str(component_file),
                    'last_modified': self.get_file_modification_time(component_file)
                }

        return components

    def get_file_modification_time(self, file_path: Path) -> str:
        """Get file modification time"""
        try:
            stat = file_path.stat()
            return str(stat.st_mtime)
        except:
            return "unknown"

    def update_diagram(self, diagram_file: Path, updates: Dict[str, Any]) -> bool:
        """Update a diagram with new component information"""
        try:
            content = diagram_file.read_text()

            # Apply updates (this would be diagram-specific logic)
            # For now, just add a comment about updates needed
            if updates.get('outdated_components'):
                update_comment = f"\n<!-- OUTDATED COMPONENTS: {', '.join(updates['outdated_components'])} -->\n"
                content += update_comment

                diagram_file.write_text(content)
                return True

        except Exception as e:
            print(f"Failed to update diagram {diagram_file}: {e}")

        return False

    def generate_validation_report(self, results: List[DiagramValidationResult]) -> str:
        """Generate a validation report"""
        report = "# Architecture Diagram Validation Report\n\n"
        report += f"Generated: {self.get_current_timestamp()}\n\n"

        total_diagrams = len(results)
        valid_diagrams = len([r for r in results if r.is_valid])
        invalid_diagrams = total_diagrams - valid_diagrams

        report += "## Summary\n\n"
        report += f"- **Total Diagrams:** {total_diagrams}\n"
        report += f"- **Valid Diagrams:** {valid_diagrams}\n"
        report += f"- **Invalid Diagrams:** {invalid_diagrams}\n\n"

        if invalid_diagrams > 0:
            report += "## Issues Found\n\n"

            for result in results:
                if not result.is_valid or result.warnings or result.outdated_components:
                    report += f"### {Path(result.file_path).name}\n\n"

                    if result.errors:
                        report += "**Errors:**\n"
                        for error in result.errors:
                            report += f"- {error}\n"
                        report += "\n"

                    if result.warnings:
                        report += "**Warnings:**\n"
                        for warning in result.warnings:
                            report += f"- {warning}\n"
                        report += "\n"

                    if result.outdated_components:
                        report += "**Outdated Components:**\n"
                        for component in result.outdated_components:
                            report += f"- {component}\n"
                        report += "\n"

        report += "## Recommendations\n\n"
        if invalid_diagrams > 0:
            report += "1. Fix syntax errors in invalid diagrams\n"
            report += "2. Update component references to match current codebase\n"
            report += "3. Fix broken WikiLinks\n"
            report += "4. Regenerate diagrams from code analysis if needed\n"

        return report

    def get_current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

def main():
    """Main validation and update process"""
    manager = ArchitectureDiagramManager()

    print("🔍 Validating architecture diagrams...")

    # Validate all diagrams
    results = manager.validate_all_diagrams()

    # Generate report
    report = manager.generate_validation_report(results)

    # Save report
    report_path = Path('docs/architecture/validation-report.md')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report)

    # Print summary
    valid_count = len([r for r in results if r.is_valid])
    total_count = len(results)

    print(f"✅ Validated {total_count} diagrams")
    print(f"✅ Valid: {valid_count}, Invalid: {total_count - valid_count}")

    # Save detailed results
    results_data = {
        'generated_at': manager.get_current_timestamp(),
        'results': [
            {
                'file_path': r.file_path,
                'is_valid': r.is_valid,
                'errors': r.errors,
                'warnings': r.warnings,
                'outdated_components': r.outdated_components
            }
            for r in results
        ]
    }

    results_path = Path('docs/architecture/validation-results.json')
    with open(results_path, 'w') as f:
        json.dump(results_data, f, indent=2)

    print("✅ Generated validation report")

    # Exit with error code if there are invalid diagrams
    if valid_count < total_count:
        print("❌ Some diagrams have issues. Check validation-report.md")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### CI/CD Integration

#### Documentation Validation in CI
```yaml
# .github/workflows/docs-validation.yml
name: Documentation Validation

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'docs/**'
      - 'backend/**'
      - 'frontend/**'
  pull_request:
    branches: [ main, develop ]
    paths:
      - 'docs/**'
      - 'backend/**'
      - 'frontend/**'

jobs:
  validate-docs:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        cd frontend && npm ci

    - name: Validate architecture diagrams
      run: python scripts/update_architecture_diagrams.py

    - name: Generate API documentation
      run: python scripts/generate_openapi_docs.py

    - name: Analyze API endpoints
      run: python scripts/analyze_api_endpoints.py

    - name: Analyze database schema
      run: python scripts/analyze_database_schema.py

    - name: Analyze React components
      run: npx ts-node scripts/analyze-components.ts

    - name: Check documentation consistency
      run: |
        # Check for broken links
        find docs -name "*.md" -exec grep -l "\[\[.*\]\]" {} \; | \
        xargs -I {} python scripts/check_wikilinks.py {}

    - name: Upload documentation artifacts
      uses: actions/upload-artifact@v3
      with:
        name: generated-docs
        path: |
          docs/api/
          docs/database/
          docs/components/
          docs/architecture/validation-report.md

  docs-deploy:
    needs: validate-docs
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy documentation to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: docs
        cname: docs.careercopilot.com
```

## Documentation Maintenance Scripts

### WikiLink Validator
```python
# scripts/check_wikilinks.py
#!/usr/bin/env python3
"""
Validate WikiLinks in documentation files.
Ensures all [[link]] references point to existing files.
"""

import os
import re
import sys
from pathlib import Path
from typing import Set, List, Dict

class WikiLinkValidator:
    """Validates WikiLinks in documentation"""

    def __init__(self, docs_path: str = 'docs'):
        self.docs_path = Path(docs_path)
        self.all_files: Set[str] = set()
        self.broken_links: Dict[str, List[str]] = {}

    def validate_all_files(self) -> bool:
        """Validate WikiLinks in all documentation files"""
        self._collect_all_files()
        self.broken_links = {}

        for md_file in self.docs_path.rglob('*.md'):
            self._validate_file(md_file)

        return len(self.broken_links) == 0

    def _collect_all_files(self):
        """Collect all documentation file names (without extension)"""
        for md_file in self.docs_path.rglob('*.md'):
            relative_path = md_file.relative_to(self.docs_path)
            file_stem = str(relative_path).replace('.md', '')
            self.all_files.add(file_stem)

    def _validate_file(self, file_path: Path):
        """Validate WikiLinks in a single file"""
        try:
            content = file_path.read_text()
            wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)

            broken_in_file = []
            for link in wikilinks:
                # Remove anchor links (#section)
                link_base = link.split('#')[0]
                if link_base not in self.all_files:
                    broken_in_file.append(link)

            if broken_in_file:
                relative_path = file_path.relative_to(self.docs_path)
                self.broken_links[str(relative_path)] = broken_in_file

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    def generate_report(self) -> str:
        """Generate validation report"""
        report = "# WikiLink Validation Report\n\n"
        report += f"Generated: {self._get_timestamp()}\n\n"

        if not self.broken_links:
            report += "✅ All WikiLinks are valid!\n"
            return report

        report += f"❌ Found {len(self.broken_links)} files with broken WikiLinks:\n\n"

        for file_path, broken_links in self.broken_links.items():
            report += f"## {file_path}\n\n"
            for link in broken_links:
                report += f"- [[{link}]]\n"
            report += "\n"

        report += "## Suggested Fixes\n\n"
        report += "1. Check if the linked file exists with correct name\n"
        report += "2. Ensure correct capitalization\n"
        report += "3. Verify the file is in the expected location\n"
        report += "4. Consider creating the missing documentation\n"

        return report

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

def main():
    """Main validation process"""
    validator = WikiLinkValidator()

    print("🔍 Validating WikiLinks...")

    is_valid = validator.validate_all_files()

    # Generate and save report
    report = validator.generate_report()

    report_path = Path('docs/wikilink-validation-report.md')
    report_path.write_text(report)

    if is_valid:
        print("✅ All WikiLinks are valid!")
        return 0
    else:
        print(f"❌ Found {len(validator.broken_links)} files with broken WikiLinks")
        print("Check wikilink-validation-report.md for details")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

### Documentation Health Monitor
```python
# scripts/monitor_docs_health.py
#!/usr/bin/env python3
"""
Monitor documentation health and freshness.
Tracks staleness, completeness, and maintenance needs.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

class DocumentationHealthMonitor:
    """Monitors documentation health metrics"""

    def __init__(self, docs_path: str = 'docs'):
        self.docs_path = Path(docs_path)
        self.health_metrics: Dict[str, Any] = {}

    def analyze_health(self) -> Dict[str, Any]:
        """Analyze overall documentation health"""
        self.health_metrics = {
            'generated_at': datetime.utcnow().isoformat(),
            'file_metrics': self._analyze_file_metrics(),
            'freshness_metrics': self._analyze_freshness(),
            'completeness_metrics': self._analyze_completeness(),
            'maintenance_alerts': self._generate_maintenance_alerts()
        }

        return self.health_metrics

    def _analyze_file_metrics(self) -> Dict[str, Any]:
        """Analyze basic file metrics"""
        total_files = 0
        total_size = 0
        file_types = {}

        for md_file in self.docs_path.rglob('*.md'):
            total_files += 1
            size = md_file.stat().st_size
            total_size += size

            ext = md_file.suffix
            file_types[ext] = file_types.get(ext, 0) + 1

        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'average_size_bytes': total_size / total_files if total_files > 0 else 0,
            'file_types': file_types
        }

    def _analyze_freshness(self) -> Dict[str, Any]:
        """Analyze documentation freshness"""
        now = datetime.now()
        freshness_thresholds = {
            'critical': timedelta(days=90),  # Needs immediate update
            'warning': timedelta(days=30),   # Should be reviewed
            'fresh': timedelta(days=7)       # Recently updated
        }

        files_by_freshness = {
            'critical': [],
            'warning': [],
            'fresh': [],
            'stale': []
        }

        for md_file in self.docs_path.rglob('*.md'):
            mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
            age = now - mtime

            relative_path = md_file.relative_to(self.docs_path)

            if age > freshness_thresholds['critical']:
                files_by_freshness['critical'].append(str(relative_path))
            elif age > freshness_thresholds['warning']:
                files_by_freshness['warning'].append(str(relative_path))
            elif age < freshness_thresholds['fresh']:
                files_by_freshness['fresh'].append(str(relative_path))
            else:
                files_by_freshness['stale'].append(str(relative_path))

        return {
            'files_by_freshness': files_by_freshness,
            'summary': {
                'critical_count': len(files_by_freshness['critical']),
                'warning_count': len(files_by_freshness['warning']),
                'fresh_count': len(files_by_freshness['fresh']),
                'stale_count': len(files_by_freshness['stale'])
            }
        }

    def _analyze_completeness(self) -> Dict[str, Any]:
        """Analyze documentation completeness"""
        completeness_checks = {
            'has_api_docs': self._check_api_documentation(),
            'has_architecture_docs': self._check_architecture_docs(),
            'has_development_guides': self._check_development_guides(),
            'has_testing_docs': self._check_testing_documentation(),
            'has_deployment_docs': self._check_deployment_docs()
        }

        completeness_score = sum(completeness_checks.values()) / len(completeness_checks)

        return {
            'checks': completeness_checks,
            'overall_score': completeness_score,
            'grade': self._calculate_grade(completeness_score)
        }

    def _check_api_documentation(self) -> bool:
        """Check if API documentation exists"""
        api_paths = [
            'docs/api/README.md',
            'docs/api/openapi.json',
            'docs/api/endpoints.json'
        ]
        return all(Path(path).exists() for path in api_paths)

    def _check_architecture_docs(self) -> bool:
        """Check if architecture documentation exists"""
        arch_path = Path('docs/architecture')
        return arch_path.exists() and len(list(arch_path.glob('*.md'))) >= 5

    def _check_development_guides(self) -> bool:
        """Check if development guides exist"""
        dev_path = Path('docs/development')
        return dev_path.exists() and len(list(dev_path.glob('*.md'))) >= 3

    def _check_testing_documentation(self) -> bool:
        """Check if testing documentation exists"""
        return Path('docs/development/testing-strategies.md').exists()

    def _check_deployment_docs(self) -> bool:
        """Check if deployment documentation exists"""
        return Path('docs/development/workflow-documentation.md').exists()

    def _calculate_grade(self, score: float) -> str:
        """Calculate completeness grade"""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'

    def _generate_maintenance_alerts(self) -> List[str]:
        """Generate maintenance alerts based on analysis"""
        alerts = []

        freshness = self.health_metrics.get('freshness_metrics', {})
        summary = freshness.get('summary', {})

        if summary.get('critical_count', 0) > 0:
            alerts.append(f"🚨 {summary['critical_count']} documents haven't been updated in 90+ days")

        if summary.get('warning_count', 0) > 0:
            alerts.append(f"⚠️ {summary['warning_count']} documents haven't been updated in 30+ days")

        completeness = self.health_metrics.get('completeness_metrics', {})
        if completeness.get('overall_score', 0) < 0.7:
            grade = completeness.get('grade', 'F')
            alerts.append(f"📚 Documentation completeness grade: {grade} - needs improvement")

        return alerts

    def generate_report(self) -> str:
        """Generate health report"""
        report = "# Documentation Health Report\n\n"
        report += f"Generated: {self.health_metrics['generated_at']}\n\n"

        # File metrics
        file_metrics = self.health_metrics['file_metrics']
        report += "## File Metrics\n\n"
        report += f"- **Total Files:** {file_metrics['total_files']}\n"
        report += f"- **Total Size:** {file_metrics['total_size_bytes']:,} bytes\n"
        report += f"- **Average Size:** {file_metrics['average_size_bytes']:,.0f} bytes\n\n"

        # Freshness metrics
        freshness = self.health_metrics['freshness_metrics']
        summary = freshness['summary']
        report += "## Freshness Analysis\n\n"
        report += f"- **Fresh (< 7 days):** {summary['fresh_count']}\n"
        report += f"- **Stale (7-30 days):** {summary['stale_count']}\n"
        report += f"- **Warning (30-90 days):** {summary['warning_count']}\n"
        report += f"- **Critical (> 90 days):** {summary['critical_count']}\n\n"

        if summary['critical_count'] > 0:
            report += "### Files Needing Immediate Attention\n\n"
            for file in freshness['files_by_freshness']['critical'][:10]:  # Show first 10
                report += f"- `{file}`\n"
            if len(freshness['files_by_freshness']['critical']) > 10:
                report += f"- ... and {len(freshness['files_by_freshness']['critical']) - 10} more\n"
            report += "\n"

        # Completeness metrics
        completeness = self.health_metrics['completeness_metrics']
        report += "## Completeness Analysis\n\n"
        report += f"- **Overall Score:** {completeness['overall_score']:.2%}\n"
        report += f"- **Grade:** {completeness['grade']}\n\n"

        report += "### Completeness Checks\n\n"
        for check, passed in completeness['checks'].items():
            status = "✅" if passed else "❌"
            report += f"- {status} {check.replace('_', ' ').title()}\n"
        report += "\n"

        # Maintenance alerts
        alerts = self.health_metrics['maintenance_alerts']
        if alerts:
            report += "## Maintenance Alerts\n\n"
            for alert in alerts:
                report += f"- {alert}\n"
            report += "\n"

        # Recommendations
        report += "## Recommendations\n\n"

        if summary['critical_count'] > 0:
            report += "1. **Update Critical Documents:** Review and update documents not modified in 90+ days\n"

        if completeness['overall_score'] < 0.8:
            report += "2. **Improve Completeness:** Add missing documentation sections\n"

        report += "3. **Regular Maintenance:** Set up automated checks to monitor documentation health\n"
        report += "4. **Review Process:** Include documentation updates in code review checklists\n"

        return report

def main():
    """Main health monitoring process"""
    monitor = DocumentationHealthMonitor()

    print("🔍 Analyzing documentation health...")

    health_data = monitor.analyze_health()
    report = monitor.generate_report()

    # Save report
    report_path = Path('docs/health-report.md')
    report_path.write_text(report)

    # Save raw data
    data_path = Path('docs/health-metrics.json')
    with open(data_path, 'w') as f:
        json.dump(health_data, f, indent=2)

    print("✅ Generated documentation health report")

    # Check for critical issues
    freshness = health_data['freshness_metrics']['summary']
    completeness = health_data['completeness_metrics']

    has_critical_issues = (
        freshness['critical_count'] > 0 or
        completeness['overall_score'] < 0.6
    )

    if has_critical_issues:
        print("⚠️ Documentation health issues detected")
        return 1

    print("✅ Documentation health is good")
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

## Automated Documentation Pipeline

### Complete CI/CD Documentation Pipeline
```yaml
# .github/workflows/docs-pipeline.yml
name: Documentation Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  analyze-and-generate:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'

    - name: Install Python dependencies
      run: |
        pip install -r backend/requirements.txt
        pip install fastapi sqlalchemy alembic

    - name: Install Node.js dependencies
      run: |
        cd frontend && npm ci
        npm install -g @apidevtools/swagger-cli typescript

    - name: Analyze codebase
      run: |
        echo "🔍 Analyzing API endpoints..."
        python scripts/analyze_api_endpoints.py

        echo "🔍 Analyzing database schema..."
        python scripts/analyze_database_schema.py

        echo "🔍 Analyzing React components..."
        npx ts-node scripts/analyze-components.ts

    - name: Generate API documentation
      run: |
        echo "📝 Generating OpenAPI docs..."
        python scripts/generate_openapi_docs.py

    - name: Validate architecture diagrams
      run: |
        echo "🔍 Validating diagrams..."
        python scripts/update_architecture_diagrams.py

    - name: Check documentation health
      run: |
        echo "🏥 Checking documentation health..."
        python scripts/monitor_docs_health.py

    - name: Validate WikiLinks
      run: |
        echo "🔗 Validating WikiLinks..."
        python scripts/check_wikilinks.py

    - name: Upload generated docs
      uses: actions/upload-artifact@v3
      with:
        name: generated-documentation
        path: |
          docs/api/
          docs/database/
          docs/components/
          docs/architecture/
          docs/development/
          docs/health-report.md
          docs/wikilink-validation-report.md

  deploy-docs:
    needs: analyze-and-generate
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'

    steps:
    - uses: actions/checkout@v3

    - name: Download generated docs
      uses: actions/download-artifact@v3
      with:
        name: generated-documentation
        path: docs/

    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: docs
        cname: docs.careercopilot.com

  notify:
    needs: [analyze-and-generate, deploy-docs]
    runs-on: ubuntu-latest
    if: always()

    steps:
    - name: Send notification
      run: |
        if [ "${{ needs.analyze-and-generate.result }}" = "failure" ] || [ "${{ needs.deploy-docs.result }}" = "failure" ]; then
          echo "❌ Documentation pipeline failed"
          # Send failure notification
        else
          echo "✅ Documentation pipeline completed successfully"
          # Send success notification
        fi
```

---

*See also: [[code-examples|Code Examples]], [[testing-strategies|Testing Strategies]], [[workflow-documentation|Workflow Documentation]]*"