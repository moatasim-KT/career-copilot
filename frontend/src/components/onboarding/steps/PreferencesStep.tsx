
import React from 'react';
import { Input } from '@/components/ui/Input';
import { MultiSelect2 } from '@/components/ui/MultiSelect2';
import { Select } from '@/components/ui/Select';

interface PreferencesStepProps {
  data: {
    preferredJobTitles?: string[];
    preferredLocations?: string;
    salaryExpectations?: string;
    workArrangement?: string;
    companySize?: string;
    industry?: string[];
  };
  onChange: (data: any) => void;
}

const jobTitleOptions = [
    { value: 'frontend-developer', label: 'Frontend Developer' },
    { value: 'backend-developer', label: 'Backend Developer' },
    { value: 'full-stack-developer', label: 'Full-Stack Developer' },
    { value: 'data-scientist', label: 'Data Scientist' },
    { value: 'devops-engineer', label: 'DevOps Engineer' },
];

const industryOptions = [
    { value: 'fintech', label: 'Fintech' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'ecommerce', label: 'E-commerce' },
    { value: 'saas', label: 'SaaS' },
    { value: 'gaming', label: 'Gaming' },
];

const PreferencesStep: React.FC<PreferencesStepProps> = ({ data, onChange }) => {
  return (
    <div>
      <h2 className="text-2xl font-bold">Job Preferences</h2>
      <p className="mt-2 text-gray-600">
        Help us find the perfect job for you.
      </p>
      <div className="mt-8 space-y-6">
        <MultiSelect2
          label="Preferred Job Titles"
          options={jobTitleOptions}
          value={data.preferredJobTitles || []}
          onChange={(selected) => onChange({ preferredJobTitles: selected })}
        />
        <Input
          label="Preferred Locations (city, state, or remote)"
          value={data.preferredLocations || ''}
          onChange={(e) => onChange({ preferredLocations: e.target.value })}
        />
        <Input
          label="Salary Expectations"
          value={data.salaryExpectations || ''}
          onChange={(e) => onChange({ salaryExpectations: e.target.value })}
        />
        <Select
          label="Work Arrangement"
          value={data.workArrangement || ''}
          onChange={(e) => onChange({ workArrangement: e.target.value })}
        >
          <option value="">Select...</option>
          <option value="remote">Remote</option>
          <option value="hybrid">Hybrid</option>
          <option value="on-site">On-site</option>
        </Select>
        <Select
          label="Company Size (Optional)"
          value={data.companySize || ''}
          onChange={(e) => onChange({ companySize: e.target.value })}
        >
          <option value="">Select...</option>
          <option value="1-10">1-10 employees</option>
          <option value="11-50">11-50 employees</option>
          <option value="51-200">51-200 employees</option>
          <option value="201-500">201-500 employees</option>
          <option value="500+">500+ employees</option>
        </Select>
        <MultiSelect2
          label="Industry (Optional)"
          options={industryOptions}
          value={data.industry || []}
          onChange={(selected) => onChange({ industry: selected })}
        />
      </div>
    </div>
  );
};

export default PreferencesStep;
