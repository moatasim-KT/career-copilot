#!/usr/bin/env node

/**
 * Frontend Component Migration Script
 * 
 * Updates frontend components to use the unified API client
 * instead of direct fetch() calls to ensure backend compatibility.
 * 
 * Usage: node scripts/migrate-to-api-client.js
 */

const fs = require('fs');
const path = require('path');

const COMPONENTS_TO_UPDATE = [
    {
        file: 'src/features/personalization/PersonalizationEngine.tsx',
        replacements: [
            {
                from: "const response = await fetch('/api/jobs/available');",
                to: "const response = await apiClient.jobs.available({ limit: 100 });"
            },
            {
                from: "const jobs = await response.json();",
                to: "const jobs = response.data || [];"
            },
            {
                from: "await fetch(`/api/users/${userId}/preferences`, {",
                to: "await apiClient.personalization.updatePreferences(parseInt(userId), newPreferences);"
            },
            {
                from: "await fetch(`/api/users/${userId}/behavior`, {",
                to: "await apiClient.personalization.trackBehavior(parseInt(userId), action, jobId);"
            }
        ]
    },
    {
        file: 'src/components/recommendations/SmartRecommendations.tsx',
        replacements: [
            {
                from: "fetch(`/api/recommendations/${jobId}/feedback`, {",
                to: "apiClient.recommendations.feedback(\n      jobId,\n      userId,\n      isPositive,\n      undefined  // optional reason\n    ).then(() => {"
            },
            {
                from: "method: 'POST',\n        headers: { 'Content-Type': 'application/json' },\n        body: JSON.stringify({ userId, isPositive }),\n      });",
                to: "});"
            }
        ]
    },
    {
        file: 'src/components/social/SocialFeatures.tsx',
        replacements: [
            {
                from: "const response = await fetch(`/api/users/${userId}/mentors`);",
                to: "const response = await apiClient.social.getMentors(parseInt(userId), 10);"
            },
            {
                from: "const data = await response.json();\n          setMentors(data);",
                to: "if (response.data) {\n            setMentors(response.data);\n          }"
            },
            {
                from: "await fetch(`/api/users/${userId}/connections`, {\n        method: 'POST',\n        headers: { 'Content-Type': 'application/json' },\n        body: JSON.stringify({ mentorId }),\n      });",
                to: "await apiClient.social.createConnection(parseInt(userId), mentorId);"
            }
        ]
    }
];

function updateFile(filePath, replacements) {
    const fullPath = path.join(process.cwd(), filePath);

    if (!fs.existsSync(fullPath)) {
        console.log(`⚠️  File not found: ${filePath}`);
        return false;
    }

    let content = fs.readFileSync(fullPath, 'utf-8');
    let updated = false;

    replacements.forEach(({ from, to }) => {
        if (content.includes(from)) {
            content = content.replace(from, to);
            updated = true;
            console.log(`  ✓ Replaced: ${from.substring(0, 50)}...`);
        }
    });

    if (updated) {
        fs.writeFileSync(fullPath, content, 'utf-8');
        console.log(`✅ Updated: ${filePath}\n`);
        return true;
    } else {
        console.log(`⏭️  No changes needed: ${filePath}\n`);
        return false;
    }
}

function main() {
    console.log('🚀 Starting Frontend Component Migration\n');
    console.log('This script updates components to use the unified API client.\n');
    console.log('='.repeat(60) + '\n');

    let totalUpdated = 0;

    COMPONENTS_TO_UPDATE.forEach(({ file, replacements }) => {
        console.log(`📝 Processing: ${file}`);
        const updated = updateFile(file, replacements);
        if (updated) totalUpdated++;
    });

    console.log('='.repeat(60) + '\n');
    console.log(`✨ Migration complete! Updated ${totalUpdated} files.\n`);
    console.log('Next steps:');
    console.log('1. Review the changes with git diff');
    console.log('2. Add missing apiClient imports if needed');
    console.log('3. Run: npm run lint to check for issues');
    console.log('4. Run: npm run type-check to verify types');
    console.log('5. Test the application thoroughly\n');
}

main();
