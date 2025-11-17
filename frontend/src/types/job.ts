
export interface Company {
    id: string;
    name: string;
    logoUrl?: string;
}

export interface Job {
    id: string;
    title: string;
    company: Company;
    location: string;
    description: string;
    skills: string[];
    salaryRange?: {
        min: number;
        max: number;
    };
    // Phase 3.3: New fields for expanded job boards
    language_requirements?: string[];
    experience_level?: string;
    equity_range?: string;
    funding_stage?: string;
    total_funding?: number;
    investors?: string[];
    tech_stack?: string[];
    company_culture_tags?: string[];
    perks?: string[];
    work_permit_info?: string;
    workload_percentage?: number;
    company_verified?: boolean;
    company_videos?: Array<{
        url: string;
        type: string;
        duration?: number;
        thumbnail?: string;
    }>;
    job_language?: string;
    type?: string;
    postedAt?: string;
    remote_option?: string;
    source?: string;
    salary_range?: string;
}
