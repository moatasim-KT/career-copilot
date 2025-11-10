/**
 * Search Field Definitions
 * 
 * Defines searchable fields for different entities (jobs, applications, etc.)
 */

import type { SearchField } from '@/types/search';

/**
 * Job search fields
 */
export const JOB_SEARCH_FIELDS: SearchField[] = [
  {
    name: 'title',
    label: 'Job Title',
    type: 'text',
    operators: ['contains', 'equals', 'startsWith', 'endsWith', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'contains',
    placeholder: 'e.g., Senior Developer',
    helpText: 'Search by job title',
  },
  {
    name: 'company',
    label: 'Company',
    type: 'text',
    operators: ['contains', 'equals', 'startsWith', 'endsWith', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'contains',
    placeholder: 'e.g., Google',
    helpText: 'Search by company name',
  },
  {
    name: 'location',
    label: 'Location',
    type: 'text',
    operators: ['contains', 'equals', 'startsWith', 'endsWith', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'contains',
    placeholder: 'e.g., San Francisco',
    helpText: 'Search by job location',
  },
  {
    name: 'remote',
    label: 'Remote',
    type: 'boolean',
    operators: ['is', 'isNot'],
    defaultOperator: 'is',
    helpText: 'Filter by remote work availability',
  },
  {
    name: 'job_type',
    label: 'Job Type',
    type: 'select',
    operators: ['equals', 'in', 'notIn', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'equals',
    options: [
      { value: 'full-time', label: 'Full-time' },
      { value: 'part-time', label: 'Part-time' },
      { value: 'contract', label: 'Contract' },
      { value: 'internship', label: 'Internship' },
    ],
    helpText: 'Filter by employment type',
  },
  {
    name: 'source',
    label: 'Source',
    type: 'select',
    operators: ['equals', 'in', 'notIn', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'equals',
    options: [
      { value: 'manual', label: 'Manual' },
      { value: 'scraped', label: 'Scraped' },
      { value: 'linkedin', label: 'LinkedIn' },
      { value: 'indeed', label: 'Indeed' },
      { value: 'glassdoor', label: 'Glassdoor' },
    ],
    helpText: 'Filter by job source',
  },
  {
    name: 'tech_stack',
    label: 'Tech Stack',
    type: 'text',
    operators: ['contains', 'equals', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'contains',
    placeholder: 'e.g., React, Python',
    helpText: 'Search by required technologies',
  },
  {
    name: 'salary_range',
    label: 'Salary Range',
    type: 'text',
    operators: ['contains', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'contains',
    placeholder: 'e.g., 100k',
    helpText: 'Search by salary information',
  },
  {
    name: 'match_score',
    label: 'Match Score',
    type: 'number',
    operators: ['equals', 'gt', 'gte', 'lt', 'lte', 'between', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'gte',
    placeholder: 'e.g., 80',
    helpText: 'Filter by match score (0-100)',
  },
  {
    name: 'created_at',
    label: 'Date Added',
    type: 'date',
    operators: ['before', 'after', 'between', 'inLastDays', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'inLastDays',
    helpText: 'Filter by when the job was added',
  },
];

/**
 * Application search fields
 */
export const APPLICATION_SEARCH_FIELDS: SearchField[] = [
  {
    name: 'job_title',
    label: 'Job Title',
    type: 'text',
    operators: ['contains', 'equals', 'startsWith', 'endsWith', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'contains',
    placeholder: 'e.g., Senior Developer',
    helpText: 'Search by job title',
  },
  {
    name: 'company',
    label: 'Company',
    type: 'text',
    operators: ['contains', 'equals', 'startsWith', 'endsWith', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'contains',
    placeholder: 'e.g., Google',
    helpText: 'Search by company name',
  },
  {
    name: 'status',
    label: 'Status',
    type: 'select',
    operators: ['equals', 'in', 'notIn'],
    defaultOperator: 'equals',
    options: [
      { value: 'interested', label: 'Interested' },
      { value: 'applied', label: 'Applied' },
      { value: 'interview', label: 'Interview' },
      { value: 'offer', label: 'Offer' },
      { value: 'rejected', label: 'Rejected' },
      { value: 'accepted', label: 'Accepted' },
      { value: 'declined', label: 'Declined' },
    ],
    helpText: 'Filter by application status',
  },
  {
    name: 'notes',
    label: 'Notes',
    type: 'text',
    operators: ['contains', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'contains',
    placeholder: 'Search in notes',
    helpText: 'Search within application notes',
  },
  {
    name: 'applied_date',
    label: 'Applied Date',
    type: 'date',
    operators: ['before', 'after', 'between', 'inLastDays', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'inLastDays',
    helpText: 'Filter by application date',
  },
  {
    name: 'interview_date',
    label: 'Interview Date',
    type: 'date',
    operators: ['before', 'after', 'between', 'inLastDays', 'inNextDays', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'inNextDays',
    helpText: 'Filter by interview date',
  },
  {
    name: 'response_date',
    label: 'Response Date',
    type: 'date',
    operators: ['before', 'after', 'between', 'inLastDays', 'isEmpty', 'isNotEmpty'],
    defaultOperator: 'inLastDays',
    helpText: 'Filter by response date',
  },
];
