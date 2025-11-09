import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import StaggerReveal, { StaggerRevealItem } from './StaggerReveal';
import Card2 from './Card2';
import Button2 from './Button2';

const meta = {
  title: 'UI/Loading/StaggerReveal',
  component: StaggerReveal,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof StaggerReveal>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Basic stagger reveal with cards
 */
export const Default: Story = {
  render: () => (
    <StaggerReveal className="grid gap-4 md:grid-cols-3">
      <StaggerRevealItem>
        <Card2 className="p-6">
          <h3 className="text-lg font-semibold text-neutral-900">Card 1</h3>
          <p className="mt-2 text-neutral-600">First item to appear</p>
        </Card2>
      </StaggerRevealItem>
      <StaggerRevealItem>
        <Card2 className="p-6">
          <h3 className="text-lg font-semibold text-neutral-900">Card 2</h3>
          <p className="mt-2 text-neutral-600">Second item to appear</p>
        </Card2>
      </StaggerRevealItem>
      <StaggerRevealItem>
        <Card2 className="p-6">
          <h3 className="text-lg font-semibold text-neutral-900">Card 3</h3>
          <p className="mt-2 text-neutral-600">Third item to appear</p>
        </Card2>
      </StaggerRevealItem>
    </StaggerReveal>
  ),
};

/**
 * Fast stagger for list items
 */
export const FastStagger: Story = {
  render: () => (
    <div className="w-96">
      <StaggerReveal speed="fast" className="space-y-2">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((item) => (
          <StaggerRevealItem key={item} speed="fast">
            <div className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-primary-700">
                  {item}
                </div>
                <div>
                  <h4 className="font-medium text-neutral-900">List Item {item}</h4>
                  <p className="text-sm text-neutral-600">Fast stagger animation</p>
                </div>
              </div>
            </div>
          </StaggerRevealItem>
        ))}
      </StaggerReveal>
    </div>
  ),
};

/**
 * Normal speed stagger
 */
export const NormalStagger: Story = {
  render: () => (
    <div className="w-96">
      <StaggerReveal speed="normal" className="space-y-3">
        {[1, 2, 3, 4, 5].map((item) => (
          <StaggerRevealItem key={item} speed="normal">
            <Card2 className="p-4">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 text-xl text-white">
                  {item}
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-neutral-900">Item {item}</h4>
                  <p className="text-sm text-neutral-600">Normal stagger speed</p>
                </div>
              </div>
            </Card2>
          </StaggerRevealItem>
        ))}
      </StaggerReveal>
    </div>
  ),
};

/**
 * Interactive example with trigger button
 */
export const Interactive: Story = {
  render: () => {
    const [key, setKey] = useState(0);

    const handleReset = () => {
      setKey((prev) => prev + 1);
    };

    return (
      <div className="space-y-6">
        <Button2 onClick={handleReset}>Replay Animation</Button2>

        <StaggerReveal key={key} className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[
            { icon: '📊', title: 'Analytics', color: 'bg-blue-100' },
            { icon: '💼', title: 'Jobs', color: 'bg-green-100' },
            { icon: '📝', title: 'Applications', color: 'bg-purple-100' },
            { icon: '⭐', title: 'Favorites', color: 'bg-yellow-100' },
          ].map((item, index) => (
            <StaggerRevealItem key={index}>
              <Card2 className="p-6 text-center">
                <div className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full ${item.color} text-3xl`}>
                  {item.icon}
                </div>
                <h3 className="mt-4 font-semibold text-neutral-900">{item.title}</h3>
              </Card2>
            </StaggerRevealItem>
          ))}
        </StaggerReveal>
      </div>
    );
  },
};

/**
 * Grid layout with many items
 */
export const GridLayout: Story = {
  render: () => (
    <StaggerReveal className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
      {Array.from({ length: 12 }).map((_, index) => (
        <StaggerRevealItem key={index}>
          <Card2 className="aspect-square p-4">
            <div className="flex h-full flex-col items-center justify-center">
              <div className="text-4xl">🎯</div>
              <p className="mt-2 text-sm font-medium text-neutral-900">Item {index + 1}</p>
            </div>
          </Card2>
        </StaggerRevealItem>
      ))}
    </StaggerReveal>
  ),
};

/**
 * Custom timing
 */
export const CustomTiming: Story = {
  render: () => (
    <StaggerReveal staggerDelay={0.15} initialDelay={0.3} className="space-y-4">
      {[1, 2, 3, 4].map((item) => (
        <StaggerRevealItem key={item} duration={0.5}>
          <Card2 className="p-6">
            <h3 className="text-lg font-semibold text-neutral-900">
              Custom Timing Item {item}
            </h3>
            <p className="mt-2 text-neutral-600">
              Slower stagger with longer duration for dramatic effect
            </p>
          </Card2>
        </StaggerRevealItem>
      ))}
    </StaggerReveal>
  ),
};

/**
 * Feature cards showcase
 */
export const FeatureCards: Story = {
  render: () => (
    <StaggerReveal className="grid gap-6 md:grid-cols-3">
      {[
        {
          icon: '🚀',
          title: 'Fast Performance',
          description: 'Optimized for speed and efficiency',
        },
        {
          icon: '🎨',
          title: 'Beautiful Design',
          description: 'Modern and intuitive interface',
        },
        {
          icon: '🔒',
          title: 'Secure',
          description: 'Enterprise-grade security',
        },
      ].map((feature, index) => (
        <StaggerRevealItem key={index}>
          <Card2 className="p-6 text-center">
            <div className="text-5xl">{feature.icon}</div>
            <h3 className="mt-4 text-xl font-semibold text-neutral-900">{feature.title}</h3>
            <p className="mt-2 text-neutral-600">{feature.description}</p>
          </Card2>
        </StaggerRevealItem>
      ))}
    </StaggerReveal>
  ),
};

/**
 * Vertical list with avatars
 */
export const VerticalList: Story = {
  render: () => (
    <div className="w-96">
      <StaggerReveal speed="fast" className="space-y-3">
        {[
          { name: 'Alice Johnson', role: 'Product Manager', avatar: '👩' },
          { name: 'Bob Smith', role: 'Software Engineer', avatar: '👨' },
          { name: 'Carol White', role: 'UX Designer', avatar: '👩‍🎨' },
          { name: 'David Brown', role: 'Data Analyst', avatar: '👨‍💼' },
          { name: 'Eve Davis', role: 'Marketing Lead', avatar: '👩‍💼' },
        ].map((person, index) => (
          <StaggerRevealItem key={index} speed="fast">
            <div className="flex items-center gap-4 rounded-lg border border-neutral-200 bg-white p-4 shadow-sm">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-neutral-100 text-2xl">
                {person.avatar}
              </div>
              <div>
                <h4 className="font-medium text-neutral-900">{person.name}</h4>
                <p className="text-sm text-neutral-600">{person.role}</p>
              </div>
            </div>
          </StaggerRevealItem>
        ))}
      </StaggerReveal>
    </div>
  ),
};
