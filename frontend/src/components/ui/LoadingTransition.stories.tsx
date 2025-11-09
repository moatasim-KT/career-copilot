import type { Meta, StoryObj } from '@storybook/react';
import { useState, useEffect } from 'react';

import LoadingTransition from './LoadingTransition';
import Skeleton2 from './Skeleton2';
import Card2 from './Card2';
import Button2 from './Button2';

const meta = {
  title: 'UI/Loading/LoadingTransition',
  component: LoadingTransition,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof LoadingTransition>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Basic loading transition with skeleton
 */
export const Default: Story = {
  render: () => {
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      const timer = setTimeout(() => setLoading(false), 2000);
      return () => clearTimeout(timer);
    }, []);

    return (
      <div className="w-96">
        <LoadingTransition
          loading={loading}
          skeleton={
            <div className="space-y-3">
              <Skeleton2 height={24} width="60%" />
              <Skeleton2 height={16} width="100%" />
              <Skeleton2 height={16} width="90%" />
            </div>
          }
        >
          <div>
            <h3 className="text-xl font-semibold text-neutral-900">Content Loaded</h3>
            <p className="mt-2 text-neutral-600">
              This is the actual content that appears after loading completes.
            </p>
          </div>
        </LoadingTransition>
      </div>
    );
  },
};

/**
 * Interactive example with toggle button
 */
export const Interactive: Story = {
  render: () => {
    const [loading, setLoading] = useState(false);

    const handleToggle = () => {
      setLoading(true);
      setTimeout(() => setLoading(false), 2000);
    };

    return (
      <div className="space-y-4">
        <Button2 onClick={handleToggle} disabled={loading}>
          {loading ? 'Loading...' : 'Trigger Loading'}
        </Button2>

        <div className="w-96">
          <LoadingTransition
            loading={loading}
            skeleton={
              <div className="space-y-4">
                <Skeleton2 variant="circle" width={64} height={64} />
                <Skeleton2 height={20} width="70%" />
                <Skeleton2 height={16} width="100%" />
                <Skeleton2 height={16} width="85%" />
              </div>
            }
          >
            <div className="space-y-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-100 text-2xl">
                👤
              </div>
              <h3 className="text-lg font-semibold text-neutral-900">John Doe</h3>
              <p className="text-neutral-600">
                Senior Software Engineer with 10 years of experience in web development.
              </p>
            </div>
          </LoadingTransition>
        </div>
      </div>
    );
  },
};

/**
 * Card loading transition
 */
export const CardTransition: Story = {
  render: () => {
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      const timer = setTimeout(() => setLoading(false), 2500);
      return () => clearTimeout(timer);
    }, []);

    return (
      <div className="w-96">
        <LoadingTransition
          loading={loading}
          skeleton={
            <Card2 className="p-6">
              <div className="space-y-4">
                <Skeleton2 height={24} width="50%" />
                <Skeleton2 height={16} width="100%" />
                <Skeleton2 height={16} width="90%" />
                <Skeleton2 height={16} width="95%" />
                <div className="flex gap-2 pt-2">
                  <Skeleton2 height={36} width={100} />
                  <Skeleton2 height={36} width={100} />
                </div>
              </div>
            </Card2>
          }
        >
          <Card2 className="p-6">
            <h3 className="text-xl font-semibold text-neutral-900">Job Posting</h3>
            <p className="mt-4 text-neutral-600">
              We're looking for a talented developer to join our team. This is a great
              opportunity to work on exciting projects with cutting-edge technologies.
            </p>
            <div className="mt-6 flex gap-2">
              <Button2 variant="primary">Apply Now</Button2>
              <Button2 variant="outline">Learn More</Button2>
            </div>
          </Card2>
        </LoadingTransition>
      </div>
    );
  },
};

/**
 * Multiple items with different timing
 */
export const MultipleItems: Story = {
  render: () => {
    const [loading1, setLoading1] = useState(true);
    const [loading2, setLoading2] = useState(true);
    const [loading3, setLoading3] = useState(true);

    useEffect(() => {
      const timer1 = setTimeout(() => setLoading1(false), 1500);
      const timer2 = setTimeout(() => setLoading2(false), 2000);
      const timer3 = setTimeout(() => setLoading3(false), 2500);
      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
      };
    }, []);

    return (
      <div className="grid gap-4 md:grid-cols-3">
        <LoadingTransition
          loading={loading1}
          skeleton={
            <Card2 className="p-4">
              <Skeleton2 height={100} />
              <Skeleton2 height={16} width="80%" className="mt-3" />
            </Card2>
          }
        >
          <Card2 className="p-4">
            <div className="flex h-24 items-center justify-center rounded-lg bg-primary-100 text-4xl">
              📊
            </div>
            <p className="mt-3 text-sm font-medium text-neutral-900">Analytics</p>
          </Card2>
        </LoadingTransition>

        <LoadingTransition
          loading={loading2}
          skeleton={
            <Card2 className="p-4">
              <Skeleton2 height={100} />
              <Skeleton2 height={16} width="80%" className="mt-3" />
            </Card2>
          }
        >
          <Card2 className="p-4">
            <div className="flex h-24 items-center justify-center rounded-lg bg-success-100 text-4xl">
              ✅
            </div>
            <p className="mt-3 text-sm font-medium text-neutral-900">Tasks</p>
          </Card2>
        </LoadingTransition>

        <LoadingTransition
          loading={loading3}
          skeleton={
            <Card2 className="p-4">
              <Skeleton2 height={100} />
              <Skeleton2 height={16} width="80%" className="mt-3" />
            </Card2>
          }
        >
          <Card2 className="p-4">
            <div className="flex h-24 items-center justify-center rounded-lg bg-warning-100 text-4xl">
              📧
            </div>
            <p className="mt-3 text-sm font-medium text-neutral-900">Messages</p>
          </Card2>
        </LoadingTransition>
      </div>
    );
  },
};

/**
 * Custom timing
 */
export const CustomTiming: Story = {
  render: () => {
    const [loading, setLoading] = useState(true);

    useEffect(() => {
      const timer = setTimeout(() => setLoading(false), 2000);
      return () => clearTimeout(timer);
    }, []);

    return (
      <div className="w-96">
        <LoadingTransition
          loading={loading}
          skeleton={<Skeleton2 height={200} />}
          delay={0.3}
          duration={0.5}
        >
          <div className="flex h-48 items-center justify-center rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 text-white">
            <div className="text-center">
              <h3 className="text-2xl font-bold">Welcome!</h3>
              <p className="mt-2">Content loaded with custom timing</p>
            </div>
          </div>
        </LoadingTransition>
      </div>
    );
  },
};
