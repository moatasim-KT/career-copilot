import { z } from 'zod';

// Define Zod schemas for API response types

export const JobSchema = z.object({
  id: z.number(),
  company: z.string(),
  title: z.string(),
  location: z.string().optional(),
  url: z.string().optional(),
  salary_range: z.string().optional(),
  job_type: z.string(),
  description: z.string().optional(),
  remote: z.boolean(),
  tech_stack: z.array(z.string()),
  responsibilities: z.string().optional(),
  source: z.string(),
  match_score: z.number().optional(),
  documents_required: z.array(z.string()).optional(),
  created_at: z.string().optional(),
});

export const ApplicationSchema = z.object({
  id: z.number(),
  job_id: z.number(),
  job: JobSchema.optional(), // Nested schema
  status: z.enum(['interested', 'applied', 'interview', 'offer', 'rejected', 'accepted', 'declined']),
  applied_date: z.string().optional(),
  interview_date: z.string().optional(),
  response_date: z.string().optional(),
  notes: z.string().optional(),
  interview_feedback: z.object({
    questions: z.array(z.string()),
    skill_areas: z.array(z.string()),
    notes: z.string(),
  }).optional(),
});

export const UserProfileSchema = z.object({
  id: z.number(),
  username: z.string(),
  email: z.string().email(),
  full_name: z.string().optional(),
  experience_level: z.string().optional(),
  current_role: z.string().optional(),
  target_roles: z.array(z.string()).optional(),
  skills: z.array(z.string()).optional(),
  location: z.string().optional(),
  remote_preference: z.boolean().optional(),
  prefer_remote_jobs: z.boolean().optional(),
  salary_expectation: z.string().optional(),
});

export const AnalyticsSummarySchema = z.object({
  total_jobs: z.number(),
  total_applications: z.number(),
  pending_applications: z.number(),
  interviews_scheduled: z.number(),
  offers_received: z.number(),
  rejections_received: z.number(),
  acceptance_rate: z.number(),
  daily_applications_today: z.number(),
  weekly_applications: z.number(),
  monthly_applications: z.number(),
  daily_application_goal: z.number(),
  daily_goal_progress: z.number(),
  top_skills_in_jobs: z.array(z.object({ skill: z.string(), count: z.number() })),
  top_companies_applied: z.array(z.object({ company: z.string(), count: z.number() })),
  application_status_breakdown: z.record(z.string(), z.number()),
  total_jobs_trend: z.object({ trend: z.enum(['up', 'down', 'neutral']), value: z.number() }),
  total_applications_trend: z.object({ trend: z.enum(['up', 'down', 'neutral']), value: z.number() }),
  interviews_scheduled_trend: z.object({ trend: z.enum(['up', 'down', 'neutral']), value: z.number() }),
  offers_received_trend: z.object({ trend: z.enum(['up', 'down', 'neutral']), value: z.number() }),
});

export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataType: T) =>
  z.object({
    data: dataType.optional(),
    error: z.string().optional(),
  });