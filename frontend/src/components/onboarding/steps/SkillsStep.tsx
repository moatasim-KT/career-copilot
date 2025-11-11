/**
 * SkillsStep Component
 * 
 * Second step of onboarding wizard - collects user skills and expertise.
 * 
 * Features:
 * - Multi-select skill tags
 * - Popular skills suggestions
 * - Search for skills
 * - Add custom skills
 * - Proficiency level per skill (optional)
 * - Skill categories
 * 
 * @module components/onboarding/steps/SkillsStep
 */

'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Plus, X, Star, TrendingUp, Code, Database, Cloud, Palette } from 'lucide-react';

import Input2 from '@/components/ui/Input2';
import Badge from '@/components/ui/Badge';
import { staggerContainer, staggerItem } from '@/lib/animations';
import { cn } from '@/lib/utils';

import type { StepProps } from '../OnboardingWizard';

/**
 * Skill interface
 */
interface Skill {
  value: string;
  label: string;
  proficiency?: 'Beginner' | 'Intermediate' | 'Advanced' | 'Expert';
  category?: string;
}

/**
 * Proficiency levels
 */
const proficiencyLevels = [
  { value: 'Beginner', label: 'Beginner', description: 'Learning the basics' },
  { value: 'Intermediate', label: 'Intermediate', description: 'Can work independently' },
  { value: 'Advanced', label: 'Advanced', description: 'Expert level knowledge' },
  { value: 'Expert', label: 'Expert', description: 'Industry leader' },
];

/**
 * Popular skills by category
 */
const skillCategories = [
  {
    id: 'frontend',
    name: 'Frontend',
    icon: <Palette className="h-4 w-4" />,
    skills: [
      { value: 'react', label: 'React' },
      { value: 'vue', label: 'Vue.js' },
      { value: 'angular', label: 'Angular' },
      { value: 'typescript', label: 'TypeScript' },
      { value: 'javascript', label: 'JavaScript' },
      { value: 'html-css', label: 'HTML/CSS' },
      { value: 'tailwind', label: 'Tailwind CSS' },
      { value: 'nextjs', label: 'Next.js' },
    ],
  },
  {
    id: 'backend',
    name: 'Backend',
    icon: <Code className="h-4 w-4" />,
    skills: [
      { value: 'nodejs', label: 'Node.js' },
      { value: 'python', label: 'Python' },
      { value: 'java', label: 'Java' },
      { value: 'go', label: 'Go' },
      { value: 'rust', label: 'Rust' },
      { value: 'php', label: 'PHP' },
      { value: 'ruby', label: 'Ruby' },
      { value: 'csharp', label: 'C#' },
    ],
  },
  {
    id: 'database',
    name: 'Database',
    icon: <Database className="h-4 w-4" />,
    skills: [
      { value: 'postgresql', label: 'PostgreSQL' },
      { value: 'mysql', label: 'MySQL' },
      { value: 'mongodb', label: 'MongoDB' },
      { value: 'redis', label: 'Redis' },
      { value: 'elasticsearch', label: 'Elasticsearch' },
      { value: 'dynamodb', label: 'DynamoDB' },
    ],
  },
  {
    id: 'cloud',
    name: 'Cloud & DevOps',
    icon: <Cloud className="h-4 w-4" />,
    skills: [
      { value: 'aws', label: 'AWS' },
      { value: 'azure', label: 'Azure' },
      { value: 'gcp', label: 'Google Cloud' },
      { value: 'docker', label: 'Docker' },
      { value: 'kubernetes', label: 'Kubernetes' },
      { value: 'terraform', label: 'Terraform' },
      { value: 'ci-cd', label: 'CI/CD' },
    ],
  },
];

/**
 * Flatten all skills for search
 */
const allSkills = skillCategories.flatMap((category) =>
  category.skills.map((skill) => ({ ...skill, category: category.name }))
);

/**
 * SkillsStep Component
 */
const SkillsStep: React.FC<StepProps> = ({ data, onChange }) => {
  const [selectedSkills, setSelectedSkills] = useState<Skill[]>(data.skills || []);
  const [searchQuery, setSearchQuery] = useState('');
  const [customSkill, setCustomSkill] = useState('');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  // Auto-save on change
  useEffect(() => {
    onChange({ skills: selectedSkills });
  }, [selectedSkills, onChange]);

  /**
   * Add skill
   */
  const handleAddSkill = (skillValue: string, skillLabel: string, category?: string) => {
    if (selectedSkills.some((s) => s.value === skillValue)) {
      return;
    }

    const newSkill: Skill = {
      value: skillValue,
      label: skillLabel,
      proficiency: 'Intermediate',
      category,
    };

    setSelectedSkills([...selectedSkills, newSkill]);
  };

  /**
   * Remove skill
   */
  const handleRemoveSkill = (skillValue: string) => {
    setSelectedSkills(selectedSkills.filter((s) => s.value !== skillValue));
  };

  /**
   * Update proficiency
   */
  const handleProficiencyChange = (skillValue: string, proficiency: any) => {
    setSelectedSkills(
      selectedSkills.map((skill) =>
        skill.value === skillValue ? { ...skill, proficiency } : skill
      )
    );
  };

  /**
   * Add custom skill
   */
  const handleAddCustomSkill = () => {
    if (!customSkill.trim()) {
      return;
    }

    const skillValue = customSkill.toLowerCase().replace(/\s+/g, '-');
    handleAddSkill(skillValue, customSkill.trim(), 'Custom');
    setCustomSkill('');
  };

  /**
   * Filter skills by search query
   */
  const filteredSkills = searchQuery
    ? allSkills.filter((skill) =>
        skill.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  /**
   * Get trending skills (most commonly selected)
   */
  const trendingSkills = [
    { value: 'react', label: 'React' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'python', label: 'Python' },
    { value: 'aws', label: 'AWS' },
    { value: 'docker', label: 'Docker' },
  ];

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 mb-4">
          <Star className="h-8 w-8 text-primary-600 dark:text-primary-400" />
        </div>
        <h3 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
          What are your skills?
        </h3>
        <p className="text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto">
          Select your technical skills to help us match you with the right opportunities.
          You can add proficiency levels later.
        </p>
      </motion.div>

      {/* Search */}
      <motion.div variants={staggerItem}>
        <Input2
          placeholder="Search for skills..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          prefixIcon={<Search className="h-4 w-4" />}
          clearable
          onClear={() => setSearchQuery('')}
        />

        {/* Search results */}
        <AnimatePresence>
          {searchQuery && filteredSkills.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mt-2 p-4 bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700 shadow-lg"
            >
              <div className="flex flex-wrap gap-2">
                {filteredSkills.slice(0, 10).map((skill) => (
                  <button
                    key={skill.value}
                    onClick={() => handleAddSkill(skill.value, skill.label, skill.category)}
                    disabled={selectedSkills.some((s) => s.value === skill.value)}
                    className={cn(
                      'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
                      selectedSkills.some((s) => s.value === skill.value)
                        ? 'bg-neutral-100 dark:bg-neutral-700 text-neutral-400 cursor-not-allowed'
                        : 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 hover:bg-primary-100 dark:hover:bg-primary-900/50'
                    )}
                  >
                    {skill.label}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Trending skills */}
      {!searchQuery && selectedSkills.length === 0 && (
        <motion.div variants={staggerItem}>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="h-4 w-4 text-neutral-600 dark:text-neutral-400" />
            <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
              Trending Skills
            </h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {trendingSkills.map((skill) => (
              <button
                key={skill.value}
                onClick={() => handleAddSkill(skill.value, skill.label)}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-primary-50 to-primary-100 dark:from-primary-900/30 dark:to-primary-800/30 text-primary-700 dark:text-primary-300 hover:from-primary-100 hover:to-primary-200 dark:hover:from-primary-900/50 dark:hover:to-primary-800/50 transition-all font-medium text-sm"
              >
                {skill.label}
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Skill categories */}
      {!searchQuery && (
        <motion.div variants={staggerItem} className="space-y-4">
          <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
            Browse by Category
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {skillCategories.map((category) => (
              <button
                key={category.id}
                onClick={() =>
                  setActiveCategory(activeCategory === category.id ? null : category.id)
                }
                className={cn(
                  'p-4 rounded-lg border-2 transition-all text-left',
                  activeCategory === category.id
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                    : 'border-neutral-200 dark:border-neutral-700 hover:border-primary-300 dark:hover:border-primary-700'
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  {category.icon}
                  <span className="font-medium text-sm text-neutral-900 dark:text-neutral-100">
                    {category.name}
                  </span>
                </div>
                <span className="text-xs text-neutral-600 dark:text-neutral-400">
                  {category.skills.length} skills
                </span>
              </button>
            ))}
          </div>

          {/* Category skills */}
          <AnimatePresence>
            {activeCategory && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="p-4 bg-neutral-50 dark:bg-neutral-800/50 rounded-lg">
                  <div className="flex flex-wrap gap-2">
                    {skillCategories
                      .find((c) => c.id === activeCategory)
                      ?.skills.map((skill) => (
                        <button
                          key={skill.value}
                          onClick={() =>
                            handleAddSkill(
                              skill.value,
                              skill.label,
                              skillCategories.find((c) => c.id === activeCategory)?.name
                            )
                          }
                          disabled={selectedSkills.some((s) => s.value === skill.value)}
                          className={cn(
                            'px-3 py-1.5 rounded-full text-sm font-medium transition-colors',
                            selectedSkills.some((s) => s.value === skill.value)
                              ? 'bg-neutral-200 dark:bg-neutral-700 text-neutral-400 cursor-not-allowed'
                              : 'bg-white dark:bg-neutral-800 text-neutral-700 dark:text-neutral-300 hover:bg-primary-50 dark:hover:bg-primary-900/30 border border-neutral-200 dark:border-neutral-700'
                          )}
                        >
                          {skill.label}
                        </button>
                      ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Selected skills */}
      {selectedSkills.length > 0 && (
        <motion.div variants={staggerItem} className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
              Your Skills ({selectedSkills.length})
            </h4>
            <button
              onClick={() => setSelectedSkills([])}
              className="text-xs text-error-600 hover:text-error-700 dark:text-error-400 dark:hover:text-error-300"
            >
              Clear all
            </button>
          </div>

          <div className="space-y-3">
            <AnimatePresence>
              {selectedSkills.map((skill) => (
                <motion.div
                  key={skill.value}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="flex items-center gap-3 p-3 bg-white dark:bg-neutral-800 rounded-lg border border-neutral-200 dark:border-neutral-700"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-neutral-900 dark:text-neutral-100">
                        {skill.label}
                      </span>
                      {skill.category && (
                        <Badge variant="secondary" size="sm">
                          {skill.category}
                        </Badge>
                      )}
                    </div>
                  </div>

                  <select
                    value={skill.proficiency || 'Intermediate'}
                    onChange={(e) => handleProficiencyChange(skill.value, e.target.value)}
                    className="w-40 h-8 px-3 text-sm rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  >
                    {proficiencyLevels.map((level) => (
                      <option key={level.value} value={level.value}>
                        {level.label}
                      </option>
                    ))}
                  </select>

                  <button
                    onClick={() => handleRemoveSkill(skill.value)}
                    className="p-1 text-neutral-400 hover:text-error-600 dark:hover:text-error-400 transition-colors"
                    aria-label={`Remove ${skill.label}`}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      )}

      {/* Add custom skill */}
      <motion.div variants={staggerItem} className="pt-6 border-t border-neutral-200 dark:border-neutral-700">
        <h4 className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
          Don't see your skill? Add it manually
        </h4>
        <div className="flex gap-2">
          <Input2
            placeholder="Enter skill name"
            value={customSkill}
            onChange={(e) => setCustomSkill(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAddCustomSkill();
              }
            }}
            className="flex-1"
          />
          <button
            onClick={handleAddCustomSkill}
            disabled={!customSkill.trim()}
            className={cn(
              'px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2',
              customSkill.trim()
                ? 'bg-primary-600 text-white hover:bg-primary-700'
                : 'bg-neutral-200 dark:bg-neutral-700 text-neutral-400 cursor-not-allowed'
            )}
          >
            <Plus className="h-4 w-4" />
            Add
          </button>
        </div>
      </motion.div>

      {/* Helper text */}
      {selectedSkills.length === 0 && (
        <motion.div
          variants={staggerItem}
          className="text-center p-6 bg-neutral-50 dark:bg-neutral-800/50 rounded-lg"
        >
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            Select at least 3-5 skills to get better job recommendations
          </p>
        </motion.div>
      )}
    </motion.div>
  );
};

export default SkillsStep;
