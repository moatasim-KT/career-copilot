import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './Card2';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof Card> = {
    title: 'Components/UI/Card2',
    component: Card,
    tags: ['autodocs'],
};
export default meta;
type Story = StoryObj<typeof Card>;

export const Elevations: Story = {
    render: () => (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card elevation={1} hover>
                <CardHeader>
                    <CardTitle>Card 1</CardTitle>
                </CardHeader>
                <CardContent>
                    <p>Elevation 1 with hover effect</p>
                </CardContent>
            </Card>
            <Card elevation={2} gradient>
                <CardHeader>
                    <CardTitle>Card 2</CardTitle>
                </CardHeader>
                <CardContent>
                    <p>Elevation 2 with gradient</p>
                </CardContent>
            </Card>
            <Card elevation={3} interactive>
                <CardHeader>
                    <CardTitle>Card 3</CardTitle>
                </CardHeader>
                <CardContent>
                    <p>Elevation 3 and interactive</p>
                </CardContent>
            </Card>
        </div>
    ),
};
