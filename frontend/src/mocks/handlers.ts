import { http, HttpResponse } from 'msw';

const jobs = [
  {
    id: 1,
    company: 'Google',
    title: 'Software Engineer',
    location: 'Mountain View, CA',
    url: 'https://careers.google.com',
    salary_range: '$150k-$200k',
    job_type: 'full-time',
    description: 'Develop software',
    remote: false,
    tech_stack: ['Python', 'Go'],
    responsibilities: 'Write code',
    source: 'manual',
    match_score: 90,
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    company: 'Microsoft',
    title: 'Cloud Engineer',
    location: 'Redmond, WA',
    url: 'https://careers.microsoft.com',
    salary_range: '$140k-$190k',
    job_type: 'full-time',
    description: 'Manage cloud infrastructure',
    remote: true,
    tech_stack: ['Azure', 'Kubernetes'],
    responsibilities: 'Deploy services',
    source: 'scraped',
    match_score: 85,
    created_at: new Date().toISOString(),
  },
];

export const handlers = [
  http.get('http://localhost:8002/api/v1/jobs', () => {
    return HttpResponse.json(jobs);
  }),

  http.post('http://localhost:8002/api/v1/jobs', async ({ request }) => {
    const newJob = await request.json() as any;
    const jobWithId = { ...newJob, id: jobs.length + 1, created_at: new Date().toISOString() };
    jobs.push(jobWithId);
    return HttpResponse.json(jobWithId, { status: 200 });
  }),

  http.put('http://localhost:8002/api/v1/jobs/:id', async ({ params, request }) => {
    const { id } = params;
    const updatedJobData = await request.json() as any;
    const index = jobs.findIndex(job => job.id === Number(id));
    if (index !== -1) {
      jobs[index] = { ...jobs[index], ...updatedJobData };
      return HttpResponse.json(jobs[index], { status: 200 });
    }
    return HttpResponse.json({ error: 'Job not found' }, { status: 404 });
  }),

  http.delete('http://localhost:8002/api/v1/jobs/:id', ({ params }) => {
    const { id } = params;
    const index = jobs.findIndex(job => job.id === Number(id));
    if (index !== -1) {
      jobs.splice(index, 1);
      return HttpResponse.json({ message: 'Job deleted successfully' }, { status: 200 });
    }
    return HttpResponse.json({ error: 'Job not found' }, { status: 404 });
  }),
];
