import React, { useState } from 'react';
import { PasswordInput2 } from './PasswordInput2';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof PasswordInput2> = {
    title: 'Components/UI/PasswordInput2',
    component: PasswordInput2,
    tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof PasswordInput2>;

export const Default: Story = {
    render: () => {
        const [password, setPassword] = useState('');
        return (
            <PasswordInput2
                label="Password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />
        );
    },
};

export const WithStrengthAndRequirements: Story = {
    render: () => {
        const [password, setPassword] = useState('');
        return (
            <PasswordInput2
                label="New Password"
                placeholder="Enter your new password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                showStrength
                showRequirements
            />
        );
    },
};

export const WithError: Story = {
    render: () => {
        const [password, setPassword] = useState('weak');
        return (
            <PasswordInput2
                label="Password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error="Password does not meet requirements."
                showStrength
            />
        );
    },
};
