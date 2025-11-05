import type { Meta, StoryObj } from '@storybook/react';

import Card, { CardHeader, CardTitle, CardContent } from './Card';

const meta = {
    title: 'UI/Card',
    component: Card,
    parameters: {
        layout: 'padded',
    },
    tags: ['autodocs'],
    argTypes: {
        padding: {
            control: 'select',
            options: ['sm', 'md', 'lg'],
            description: 'The padding size of the card',
        },
        hover: {
            control: 'boolean',
            description: 'Enable hover effect',
        },
    },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        children: 'This is a simple card with default styling.',
    },
};

export const SmallPadding: Story = {
    args: {
        children: 'Card with small padding',
        padding: 'sm',
    },
};

export const MediumPadding: Story = {
    args: {
        children: 'Card with medium padding',
        padding: 'md',
    },
};

export const LargePadding: Story = {
    args: {
        children: 'Card with large padding',
        padding: 'lg',
    },
};

export const WithHover: Story = {
    args: {
        children: 'Hover over this card to see the effect',
        hover: true,
    },
};

export const WithHeader: Story = {
    args: {
        children: (
            <>
                <CardHeader>
                    <CardTitle>Card Title</CardTitle>
                </CardHeader>
                <CardContent>
                    <p>This is the card content with a header and title.</p>
                </CardContent>
            </>
        ),
    },
};

export const ComplexCard: Story = {
    args: {
        children: (
            <>
                <CardHeader>
                    <CardTitle>User Profile</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        <p className="text-sm text-gray-600">Name: John Doe</p>
                        <p className="text-sm text-gray-600">Email: john.doe@example.com</p>
                        <p className="text-sm text-gray-600">Role: Software Engineer</p>
                    </div>
                </CardContent>
            </>
        ),
        hover: true,
    },
};

export const MultipleCards: Story = {
    args: {
        children: 'Card 1',
    },
    render: () => (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card hover>
                <CardHeader>
                    <CardTitle>Feature 1</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-600">Description of feature 1</p>
                </CardContent>
            </Card>
            <Card hover>
                <CardHeader>
                    <CardTitle>Feature 2</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-600">Description of feature 2</p>
                </CardContent>
            </Card>
            <Card hover>
                <CardHeader>
                    <CardTitle>Feature 3</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-600">Description of feature 3</p>
                </CardContent>
            </Card>
        </div>
    ),
};
