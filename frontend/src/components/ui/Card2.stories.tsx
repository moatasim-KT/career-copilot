import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from './Card2';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof Card> = {
    title: 'Components/UI/Card2',
    component: Card,
    tags: ['autodocs'],
    argTypes: {
        elevation: {
            control: { type: 'select' },
            options: [0, 1, 2, 3, 4, 5],
        },
        padding: {
            control: { type: 'select' },
            options: ['none', 'sm', 'md', 'lg', 'xl'],
        },
        glowColor: {
            control: { type: 'select' },
            options: ['primary', 'success', 'warning', 'error'],
        },
    },
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

export const EnhancedHoverEffects: Story = {
    render: () => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-8">
            <Card hover elevation={2}>
                <CardHeader>
                    <CardTitle>Enhanced Hover</CardTitle>
                    <CardDescription>Smooth shadow expansion on hover</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        Hover over this card to see the enhanced shadow expansion and lift effect.
                        The shadow smoothly expands and the card lifts with a subtle scale.
                    </p>
                </CardContent>
            </Card>

            <Card hover elevation={3} interactive>
                <CardHeader>
                    <CardTitle>Interactive Card</CardTitle>
                    <CardDescription>With cursor pointer</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        This card has both hover effects and interactive cursor styling.
                        Perfect for clickable cards.
                    </p>
                </CardContent>
            </Card>
        </div>
    ),
};

export const FeaturedCards: Story = {
    render: () => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-8">
            <Card featured hover glowColor="primary">
                <CardHeader>
                    <CardTitle>Premium Plan</CardTitle>
                    <CardDescription>Featured with primary glow</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        This featured card has a glow effect that intensifies on hover.
                        Perfect for highlighting premium or important content.
                    </p>
                    <div className="mt-4 text-3xl font-bold text-primary-600 dark:text-primary-400">
                        $99/mo
                    </div>
                </CardContent>
                <CardFooter>
                    <button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                        Get Started
                    </button>
                </CardFooter>
            </Card>

            <Card featured hover glowColor="success">
                <CardHeader>
                    <CardTitle>Success Story</CardTitle>
                    <CardDescription>Featured with success glow</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        Use different glow colors to match your content theme.
                        This one uses the success color for positive highlights.
                    </p>
                    <div className="mt-4 text-3xl font-bold text-success-600 dark:text-success-400">
                        ✓ Verified
                    </div>
                </CardContent>
            </Card>
        </div>
    ),
};

export const GradientBorderCards: Story = {
    render: () => (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 p-8">
            <Card gradientBorder hover>
                <CardHeader>
                    <CardTitle>Gradient Border</CardTitle>
                    <CardDescription>Animated gradient border on hover</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        Hover to reveal an animated gradient border that shifts colors.
                        The border uses a pseudo-element for smooth animation.
                    </p>
                </CardContent>
            </Card>

            <Card gradientBorder featured hover glowColor="primary">
                <CardHeader>
                    <CardTitle>Combined Effects</CardTitle>
                    <CardDescription>Gradient border + featured glow</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        Combine gradient border with featured glow for maximum visual impact.
                        Perfect for hero cards or special promotions.
                    </p>
                </CardContent>
            </Card>
        </div>
    ),
};

export const AllGlowColors: Story = {
    render: () => (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-8">
            <Card featured hover glowColor="primary">
                <CardHeader>
                    <CardTitle>Primary</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        Primary blue glow effect
                    </p>
                </CardContent>
            </Card>

            <Card featured hover glowColor="success">
                <CardHeader>
                    <CardTitle>Success</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        Success green glow effect
                    </p>
                </CardContent>
            </Card>

            <Card featured hover glowColor="warning">
                <CardHeader>
                    <CardTitle>Warning</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        Warning orange glow effect
                    </p>
                </CardContent>
            </Card>

            <Card featured hover glowColor="error">
                <CardHeader>
                    <CardTitle>Error</CardTitle>
                </CardHeader>
                <CardContent>
                    <p className="text-neutral-600 dark:text-neutral-400">
                        Error red glow effect
                    </p>
                </CardContent>
            </Card>
        </div>
    ),
};

export const CompleteShowcase: Story = {
    render: () => (
        <div className="space-y-8 p-8">
            <div>
                <h2 className="text-2xl font-bold mb-4 text-neutral-900 dark:text-neutral-100">
                    Standard Cards
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Basic Card</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-neutral-600 dark:text-neutral-400">
                                Default card with no special effects
                            </p>
                        </CardContent>
                    </Card>

                    <Card hover>
                        <CardHeader>
                            <CardTitle>Hover Card</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-neutral-600 dark:text-neutral-400">
                                Enhanced hover with shadow expansion
                            </p>
                        </CardContent>
                    </Card>

                    <Card gradient>
                        <CardHeader>
                            <CardTitle>Gradient Card</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-neutral-600 dark:text-neutral-400">
                                Subtle gradient background
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </div>

            <div>
                <h2 className="text-2xl font-bold mb-4 text-neutral-900 dark:text-neutral-100">
                    Featured Cards
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card featured hover glowColor="primary">
                        <CardHeader>
                            <CardTitle>Featured Premium</CardTitle>
                            <CardDescription>With primary glow effect</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <p className="text-neutral-600 dark:text-neutral-400">
                                Perfect for highlighting premium content or special offers
                            </p>
                        </CardContent>
                    </Card>

                    <Card gradientBorder hover>
                        <CardHeader>
                            <CardTitle>Gradient Border</CardTitle>
                            <CardDescription>Animated border on hover</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <p className="text-neutral-600 dark:text-neutral-400">
                                Animated gradient border reveals on hover
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </div>

            <div>
                <h2 className="text-2xl font-bold mb-4 text-neutral-900 dark:text-neutral-100">
                    Ultimate Card
                </h2>
                <Card featured gradientBorder hover glowColor="primary" elevation={3}>
                    <CardHeader>
                        <CardTitle>All Effects Combined</CardTitle>
                        <CardDescription>
                            Featured + Gradient Border + Enhanced Hover
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <p className="text-neutral-600 dark:text-neutral-400 mb-4">
                            This card combines all available effects: featured glow, gradient border,
                            enhanced hover animations, and elevated shadow. Perfect for hero sections
                            or the most important content on your page.
                        </p>
                        <div className="flex items-center gap-4">
                            <div className="text-3xl font-bold text-primary-600 dark:text-primary-400">
                                $149/mo
                            </div>
                            <div className="text-sm text-neutral-500 dark:text-neutral-400">
                                Most Popular
                            </div>
                        </div>
                    </CardContent>
                    <CardFooter>
                        <button className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-semibold">
                            Choose Plan
                        </button>
                        <span className="text-sm text-neutral-500 dark:text-neutral-400">
                            30-day money back guarantee
                        </span>
                    </CardFooter>
                </Card>
            </div>
        </div>
    ),
};
