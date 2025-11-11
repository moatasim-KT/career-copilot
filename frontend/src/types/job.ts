
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
}
