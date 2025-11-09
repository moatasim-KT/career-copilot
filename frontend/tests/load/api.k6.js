/**
 * API Load Test
 * 
 * Tests critical API endpoints under load.
 * Validates performance for job applications CRUD operations.
 * 
 * Usage:
 *   k6 run tests/load/api.k6.js
 *   k6 run --vus 50 --duration 60s tests/load/api.k6.js
 * 
 * @module tests/load/api
 */

/* global __ENV */


import { check, sleep } from 'k6';
import http from 'k6/http';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const createDuration = new Trend('create_application_duration');
const listDuration = new Trend('list_applications_duration');
const updateDuration = new Trend('update_application_duration');
const deleteDuration = new Trend('delete_application_duration');
const operationCounter = new Counter('operations_total');

// Test configuration
export const options = {
    stages: [
        { duration: '1m', target: 25 },  // Ramp up to 25 users
        { duration: '2m', target: 50 },  // Ramp up to 50 users
        { duration: '1m', target: 75 },  // Spike to 75 users
        { duration: '2m', target: 50 },  // Scale back to 50
        { duration: '1m', target: 0 },   // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<500', 'p(99)<1000'],
        http_req_failed: ['rate<0.01'],
        errors: ['rate<0.01'],
        create_application_duration: ['p(95)<400'],
        list_applications_duration: ['p(95)<300'],
        update_application_duration: ['p(95)<350'],
        delete_application_duration: ['p(95)<250'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';
const API_TOKEN = __ENV.API_TOKEN || 'test-token-123';

// Sample job application data
const companies = ['Google', 'Meta', 'Amazon', 'Microsoft', 'Apple', 'Netflix', 'Tesla'];
const positions = ['Software Engineer', 'Senior Engineer', 'Tech Lead', 'Engineering Manager'];
const statuses = ['applied', 'interviewing', 'offer', 'rejected'];

function generateApplicationData() {
    return {
        company: companies[Math.floor(Math.random() * companies.length)],
        position: positions[Math.floor(Math.random() * positions.length)],
        status: statuses[Math.floor(Math.random() * statuses.length)],
        dateApplied: new Date().toISOString().split('T')[0],
        notes: `Test application created by load test at ${new Date().toISOString()}`,
    };
}

export function setup() {
    console.log('Starting API load test...');
    console.log(`Base URL: ${BASE_URL}`);

    // Verify API is accessible
    const healthCheck = http.get(`${BASE_URL}/api/health`);
    if (healthCheck.status !== 200) {
        throw new Error(`API health check failed: ${healthCheck.status}`);
    }

    return { startTime: Date.now() };
}

export default function () {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_TOKEN}`,
    };

    // 1. List applications (Read)
    const listStart = Date.now();
    const listResponse = http.get(`${BASE_URL}/api/applications`, {
        headers,
        tags: { name: 'ListApplications' },
    });

    const listSuccess = check(listResponse, {
        'list status is 200': (r) => r.status === 200,
        'list returns array': (r) => Array.isArray(JSON.parse(r.body)),
        'list response time < 500ms': (r) => r.timings.duration < 500,
    });

    listDuration.add(Date.now() - listStart);
    errorRate.add(!listSuccess);
    operationCounter.add(1);

    sleep(0.5);

    // 2. Create application (Create)
    const createStart = Date.now();
    const applicationData = generateApplicationData();
    const createResponse = http.post(
        `${BASE_URL}/api/applications`,
        JSON.stringify(applicationData),
        {
            headers,
            tags: { name: 'CreateApplication' },
        },
    );

    const createSuccess = check(createResponse, {
        'create status is 201': (r) => r.status === 201,
        'create returns id': (r) => {
            const body = JSON.parse(r.body);
            return body.id !== undefined;
        },
        'create response time < 600ms': (r) => r.timings.duration < 600,
    });

    createDuration.add(Date.now() - createStart);
    errorRate.add(!createSuccess);
    operationCounter.add(1);

    if (!createSuccess) {
        console.error(`Create failed: ${createResponse.status}`);
        return;
    }

    const applicationId = JSON.parse(createResponse.body).id;
    sleep(1);

    // 3. Get single application (Read)
    const getResponse = http.get(`${BASE_URL}/api/applications/${applicationId}`, {
        headers,
        tags: { name: 'GetApplication' },
    });

    check(getResponse, {
        'get status is 200': (r) => r.status === 200,
        'get returns correct id': (r) => {
            const body = JSON.parse(r.body);
            return body.id === applicationId;
        },
    });

    operationCounter.add(1);
    sleep(0.5);

    // 4. Update application (Update)
    const updateStart = Date.now();
    const updateData = {
        ...applicationData,
        status: 'interviewing',
        notes: 'Updated by load test',
    };

    const updateResponse = http.put(
        `${BASE_URL}/api/applications/${applicationId}`,
        JSON.stringify(updateData),
        {
            headers,
            tags: { name: 'UpdateApplication' },
        },
    );

    const updateSuccess = check(updateResponse, {
        'update status is 200': (r) => r.status === 200,
        'update response time < 500ms': (r) => r.timings.duration < 500,
    });

    updateDuration.add(Date.now() - updateStart);
    errorRate.add(!updateSuccess);
    operationCounter.add(1);

    sleep(1);

    // 5. Search/filter applications (Read)
    const searchResponse = http.get(
        `${BASE_URL}/api/applications?status=interviewing&company=${applicationData.company}`,
        {
            headers,
            tags: { name: 'SearchApplications' },
        },
    );

    check(searchResponse, {
        'search status is 200': (r) => r.status === 200,
        'search returns filtered results': (r) => {
            const body = JSON.parse(r.body);
            return Array.isArray(body) && body.length >= 0;
        },
    });

    operationCounter.add(1);
    sleep(0.5);

    // 6. Delete application (Delete)
    const deleteStart = Date.now();
    const deleteResponse = http.del(`${BASE_URL}/api/applications/${applicationId}`, {
        headers,
        tags: { name: 'DeleteApplication' },
    });

    const deleteSuccess = check(deleteResponse, {
        'delete status is 204': (r) => r.status === 204 || r.status === 200,
        'delete response time < 400ms': (r) => r.timings.duration < 400,
    });

    deleteDuration.add(Date.now() - deleteStart);
    errorRate.add(!deleteSuccess);
    operationCounter.add(1);

    sleep(1); // Think time before next iteration
}

export function teardown(data) {
    const duration = (Date.now() - data.startTime) / 1000;
    console.log(`API load test completed in ${duration.toFixed(2)}s`);
    console.log('Check Grafana dashboards for detailed metrics.');
}
