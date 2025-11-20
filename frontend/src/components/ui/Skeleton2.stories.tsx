import React from 'react';
import { Skeleton2 } from './Skeleton2';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof Skeleton2> = {
    title: 'Components/UI/Skeleton2',
    component: Skeleton2,
    tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Skeleton2>;

export const Variants: Story = {
    render: () => (
        <div className="flex flex-col gap-4">
            <Skeleton2 variant="text" width="70%" />
            <Skeleton2 variant="text" width="50%" />
            <div className="flex items-center gap-4">
                <Skeleton2 variant="circle" width={40} height={40} />
                <Skeleton2 variant="text" width={150} />
            </div>
            <Skeleton2 variant="rectangle" width="100%" height={100} />
        </div>
    ),
};

export const Animations: Story = {
    render: () => (
        <div className="flex flex-col gap-4">
            <Skeleton2 variant="text" width="70%" animation="pulse" />
            <Skeleton2 variant="rectangle" width="100%" height={50} animation="shimmer" />
            <Skeleton2 variant="circle" width={50} height={50} animation="wave" />
            <Skeleton2 variant="rectangle" width="100%" height={30} animation="none" />
        </div>
    ),
};

export const Combined: Story = {
    render: () => (
        <div className="flex items-start space-x-4">
            <Skeleton2 variant="circle" width={60} height={60} />
            <div className="flex-1 space-y-2">
                <Skeleton2 variant="text" width="80%" />
                <Skeleton2 variant="text" width="60%" />
                <Skeleton2 variant="text" width="90%" />
            </div>
        </div>
    ),
};
