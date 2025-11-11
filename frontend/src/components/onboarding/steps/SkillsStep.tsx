
import React from 'react';
import { MultiSelect2 } from '@/components/ui/MultiSelect2';
import { Select } from '@/components/ui/Select';

interface Skill {
  value: string;
  label: string;
  proficiency: 'Beginner' | 'Intermediate' | 'Advanced';
}

interface SkillsStepProps {
  data: {
    skills?: Skill[];
    customSkills?: string;
  };
  onChange: (data: any) => void;
}

const popularSkills = [
  { value: 'react', label: 'React' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'python', label: 'Python' },
  { value: 'nodejs', label: 'Node.js' },
  { value: 'graphql', label: 'GraphQL' },
];

const SkillsStep: React.FC<SkillsStepProps> = ({ data, onChange }) => {
  const handleSkillChange = (selectedSkills: string[]) => {
    const newSkills = selectedSkills.map(skillValue => {
      const existingSkill = data.skills?.find(s => s.value === skillValue);
      return existingSkill || { value: skillValue, label: skillValue, proficiency: 'Intermediate' };
    });
    onChange({ skills: newSkills });
  };

  const handleProficiencyChange = (skillValue: string, proficiency: any) => {
    const updatedSkills = data.skills?.map(skill =>
      skill.value === skillValue ? { ...skill, proficiency } : skill
    );
    onChange({ skills: updatedSkills });
  };

  return (
    <div>
      <h2 className="text-2xl font-bold">Skills & Expertise</h2>
      <p className="mt-2 text-gray-600">
        Tell us about your skills to get better job recommendations.
      </p>
      <div className="mt-8 space-y-6">
        <MultiSelect2
          label="Select your skills"
          options={popularSkills}
          value={data.skills?.map(s => s.value) || []}
          onChange={handleSkillChange}
        />
        {data.skills && data.skills.length > 0 && (
          <div className="space-y-4">
            {data.skills.map(skill => (
              <div key={skill.value} className="flex items-center justify-between">
                <span>{popularSkills.find(ps => ps.value === skill.value)?.label || skill.label}</span>
                <Select
                  value={skill.proficiency}
                  onChange={(e) => handleProficiencyChange(skill.value, e.target.value)}
                  className="w-40"
                >
                  <option>Beginner</option>
                  <option>Intermediate</option>
                  <option>Advanced</option>
                </Select>
              </div>
            ))}
          </div>
        )}
        <div className="mt-4">
          <label htmlFor="customSkills" className="block text-sm font-medium text-gray-700">
            Add custom skills (comma-separated)
          </label>
          <input
            type="text"
            id="customSkills"
            value={data.customSkills || ''}
            onChange={(e) => onChange({ customSkills: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
        </div>
      </div>
    </div>
  );
};

export default SkillsStep;
