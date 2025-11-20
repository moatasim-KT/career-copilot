import React from 'react';
import { Input2 } from './Input2';
import type { Meta, StoryObj } from '@storybook/react';
import { Mail, Check } from 'lucide-react';

const meta: Meta<typeof Input2> = {
    title: 'Components/UI/Input2',
    component: Input2,
    tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Input2>;

export const Variants: Story = {
    render: () => (
        <div className="flex flex-col gap-4">
            <Input2 placeholder="Default" />
            <Input2 variant="filled" placeholder="Filled" />
            <Input2 variant="outlined" placeholder="Outlined" />
            <Input2 variant="ghost" placeholder="Ghost" />
        </div>
    ),
};

export const States: Story = {
    render: () => (
        <div className="flex flex-col gap-4">
            <Input2 placeholder="Default" />
            <Input2 state="error" placeholder="Error" error="This is an error message." />
            <Input2 state="success" placeholder="Success" success="This is a success message." />
            <Input2 state="disabled" placeholder="Disabled" />
        </div>
    ),
};

export const WithIcons: Story = {
    render: () => (
        <div className="flex flex-col gap-4">
            <Input2 prefixIcon={<Mail />} placeholder="Email" />
            <Input2 suffixIcon={<Check />} placeholder="Username" />
        </div>
    ),
};

export const Clearable: Story = {
    render: () => {
        const [value, setValue] = React.useState('Some value');
        return <Input2 clearable value={value} onChange={(e) => setValue(e.target.value)} onClear={() => setValue('')} />;
    },
};

export const Loading: Story = {
    render: () => (
        <Input2 loading placeholder="Loading..." />
    ),
};
