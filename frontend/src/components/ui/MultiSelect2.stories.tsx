import React, { useState } from 'react';
import { MultiSelect2, MultiSelect2Option } from './MultiSelect2';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof MultiSelect2> = {
    title: 'Components/UI/MultiSelect2',
    component: MultiSelect2,
    tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof MultiSelect2>;

const sampleOptions: MultiSelect2Option[] = [
    { value: 'react', label: 'React' },
    { value: 'angular', label: 'Angular' },
    { value: 'vue', label: 'Vue' },
    { value: 'svelte', label: 'Svelte' },
    { value: 'nextjs', label: 'Next.js' },
    { value: 'nuxtjs', label: 'Nuxt.js' },
    { value: 'tailwindcss', label: 'Tailwind CSS' },
    { value: 'bootstrap', label: 'Bootstrap' },
];

export const Default: Story = {
    render: () => {
        const [selected, setSelected] = useState<string[]>([]);
        return <MultiSelect2 options={sampleOptions} value={selected} onChange={setSelected} />;
    },
};

export const WithLabelAndPlaceholder: Story = {
    render: () => {
        const [selected, setSelected] = useState<string[]>([]);
        return (
            <MultiSelect2
                options={sampleOptions}
                value={selected}
                onChange={setSelected}
                label="Favorite Frameworks"
                placeholder="Select your frameworks"
            />
        );
    },
};

export const MaxSelection: Story = {
    render: () => {
        const [selected, setSelected] = useState<string[]>([]);
        return (
            <MultiSelect2
                options={sampleOptions}
                value={selected}
                onChange={setSelected}
                maxSelection={3}
                label="Max 3 Selections"
            />
        );
    },
};

export const WithError: Story = {
    render: () => {
        const [selected, setSelected] = useState<string[]>([]);
        return (
            <MultiSelect2
                options={sampleOptions}
                value={selected}
                onChange={setSelected}
                label="Skills"
                error="Please select at least one skill."
            />
        );
    },
};
