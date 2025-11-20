#!/usr/bin/env node
/**
 * Automated React component analysis and documentation generation.
 * Scans TypeScript/React files and generates component documentation.
 */

const fs = require('fs');
const path = require('path');
const ts = require('typescript');

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
        ts.forEachChild(sourceFile, (node: any) => {
            if (ts.isImportDeclaration(node)) {
                const moduleSpecifier = node.moduleSpecifier.getText().replace(/['"]/g, '');
                if (moduleSpecifier.startsWith('./') || moduleSpecifier.startsWith('../')) {
                    dependencies.push(moduleSpecifier);
                }
            }
        });

        // Find component declaration
        ts.forEachChild(sourceFile, (node: any) => {
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

    private getNodeName(node: any): string | null {
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

    private getJSDocComments(node: any): string {
        const jsDoc = (node as any).jsDoc;
        if (jsDoc && jsDoc.length > 0) {
            return jsDoc[0].comment || '';
        }
        return '';
    }

    private extractProps(node: any, sourceFile: any): PropInfo[] {
        const props: PropInfo[] = [];

        // Look for interface or type alias with Props
        ts.forEachChild(sourceFile, (child: any) => {
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

    private extractPropFromSignature(member: any): PropInfo | null {
        if (member.name && ts.isIdentifier(member.name)) {
            return {
                name: member.name.text,
                type: member.type ? member.type.getText() : 'any',
                required: !member.questionToken,
                defaultValue: undefined, // Property signatures don't have initializers
                description: this.getJSDocComments(member)
            };
        }
        return null;
    }

    private getParamDescription(node: any, paramName: string): string {
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