
import { Meta, StoryObj } from '@storybook/react';
import FilterPanel from './FilterPanel';

const meta: Meta<typeof FilterPanel> = {
  title: 'UI/FilterPanel',
  component: FilterPanel,
};

export default meta;

type Story = StoryObj<typeof FilterPanel>;

const sampleCategories = [
  {
    id: 'job-type',
    name: 'Job Type',
    options: ['Full-time', 'Part-time', 'Contract', 'Internship'],
  },
  {
    id: 'location',
    name: 'Location',
    options: ['Remote', 'New York, NY', 'San Francisco, CA', 'Austin, TX'],
  },
  {
    id: 'experience-level',
    name: 'Experience Level',
    options: ['Entry-level', 'Mid-level', 'Senior-level', 'Lead'],
  },
];

export const Default: Story = {
  args: {
    categories: sampleCategories,
    onFilterChange: (filters) => console.log(filters),
  },
};
