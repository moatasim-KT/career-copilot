/**
 * Authentication Load Test
 * 
 * Tests authentication endpoints under load with k6.
 * Validates performance for login, logout, and token refresh.
 * 
 * Usage:
 *   k6 run tests/load/auth.k6.js
 *   k6 run --vus 100 --duration 30s tests/load/auth.k6.js
 * 
 * @module tests/load/auth
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');
const logoutDuration = new Trend('logout_duration');

// Test configuration
export const options = {
    stages: [
        { duration: '30s', target: 20 }, // Ramp up to 20 users
        { duration: '1m', target: 50 },  // Ramp up to 50 users
        { duration: '30s', target: 100 }, // Spike to 100 users
        { duration: '1m', target: 100 },  // Stay at 100 users
        { duration: '30s', target: 0 },   // Ramp down to 0
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
        http_req_failed: ['rate<0.01'],   // Error rate must be below 1%
        errors: ['rate<0.01'],
        login_duration: ['p(95)<300'],     // Login should be fast
        logout_duration: ['p(95)<200'],    // Logout should be faster
    },
};

// Base URL from environment or default
const BASE_URL = __ENV.BASE_URL || 'http://localhost:3000';

// Test data
const users = [
    { email: 'user1@example.com', password: 'password123' },
    { email: 'user2@example.com', password: 'password123' },
    { email: 'user3@example.com', password: 'password123' },
    { email: 'user4@example.com', password: 'password123' },
    { email: 'user5@example.com', password: 'password123' },
];

/**
 * Setup function - runs once before all VUs
 */
export function setup() {
    console.log('Starting authentication load test...');
    console.log(`Base URL: ${BASE_URL}`);
    return { startTime: Date.now() };
}

/**
 * Main test function - runs for each VU iteration
 */
export default function () {
    // Select a random user
    const user = users[Math.floor(Math.random() * users.length)];

    // 1. Login
    const loginStart = Date.now();
    const loginResponse = http.post(
        `${BASE_URL}/api/auth/login`,
        JSON.stringify({
            email: user.email,
            password: user.password,
        }),
        {
            headers: { 'Content-Type': 'application/json' },
            tags: { name: 'Login' },
        }
    );

    const loginSuccess = check(loginResponse, {
        'login status is 200': (r) => r.status === 200,
        'login returns token': (r) => {
            const body = JSON.parse(r.body);
            return body.token !== undefined;
        },
        'login response time < 500ms': (r) => r.timings.duration < 500,
    });

    loginDuration.add(Date.now() - loginStart);
    errorRate.add(!loginSuccess);

    if (!loginSuccess) {
        console.error(`Login failed: ${loginResponse.status} ${loginResponse.body}`);
        return;
    }

    const token = JSON.parse(loginResponse.body).token;
    sleep(1); // Simulate user reading time

    // 2. Verify authenticated endpoint
    const meResponse = http.get(`${BASE_URL}/api/auth/me`, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
        tags: { name: 'GetMe' },
    });

    check(meResponse, {
        'me status is 200': (r) => r.status === 200,
        'me returns user data': (r) => {
            const body = JSON.parse(r.body);
            return body.email === user.email;
        },
    });

    sleep(2); // Simulate user activity

    // 3. Refresh token
    const refreshResponse = http.post(
        `${BASE_URL}/api/auth/refresh`,
        null,
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
            tags: { name: 'RefreshToken' },
        }
    );

    check(refreshResponse, {
        'refresh status is 200': (r) => r.status === 200,
        'refresh returns new token': (r) => {
            const body = JSON.parse(r.body);
            return body.token !== undefined;
        },
    });

    sleep(1);

    // 4. Logout
    const logoutStart = Date.now();
    const logoutResponse = http.post(
        `${BASE_URL}/api/auth/logout`,
        null,
        {
            headers: {
                Authorization: `Bearer ${token}`,
            },
            tags: { name: 'Logout' },
        }
    );

    const logoutSuccess = check(logoutResponse, {
        'logout status is 200': (r) => r.status === 200,
        'logout response time < 300ms': (r) => r.timings.duration < 300,
    });

    logoutDuration.add(Date.now() - logoutStart);
    errorRate.add(!logoutSuccess);

    sleep(1); // Think time before next iteration
}

/**
 * Teardown function - runs once after all VUs complete
 */
export function teardown(data) {
    const duration = (Date.now() - data.startTime) / 1000;
    console.log(`Test completed in ${duration.toFixed(2)}s`);
}
