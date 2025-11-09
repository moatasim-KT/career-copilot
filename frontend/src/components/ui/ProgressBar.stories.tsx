import type { Meta, StoryObj } from '@storybook/react';
import { useState, useEffect } from 'react';

import ProgressBar from './ProgressBar';
import Button2 from './Button2';
import Card2 from './Card2';

const meta = {
  title: 'UI/Loading/ProgressBar',
  component: ProgressBar,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    value: {
      control: { type: 'range', min: 0, max: 100, step: 1 },
      description: 'Progress value (0-100). Undefined for indeterminate.',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Size of the progress bar',
    },
    color: {
      control: 'select',
      options: ['primary', 'success', 'warning', 'error'],
      description: 'Color of the progress bar',
    },
    showLabel: {
      control: 'boolean',
      description: 'Show percentage label',
    },
  },
} satisfies Meta<typeof ProgressBar>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Indeterminate progress (no value)
 */
export const Indeterminate: Story = {
  args: {
    size: 'md',
    color: 'primary',
  },
};

/**
 * Determinate progress with value
 */
export const Determinate: Story = {
  args: {
    value: 65,
    size: 'md',
    color: 'primary',
  },
};

/**
 * With label showing percentage
 */
export const WithLabel: Story = {
  args: {
    value: 75,
    size: 'md',
    color: 'primary',
    showLabel: true,
    label: 'Upload Progress',
  },
};

/**
 * All sizes
 */
export const Sizes: Story = {
  render: () => (
    <div className="space-y-6">
      <div>
        <p className="mb-2 text-sm text-neutral-600">Small</p>
        <ProgressBar value={60} size="sm" />
      </div>
      <div>
        <p className="mb-2 text-sm text-neutral-600">Medium</p>
        <ProgressBar value={60} size="md" />
      </div>
      <div>
        <p className="mb-2 text-sm text-neutral-600">Large</p>
        <ProgressBar value={60} size="lg" />
      </div>
    </div>
  ),
};

/**
 * All colors
 */
export const Colors: Story = {
  render: () => (
    <div className="space-y-6">
      <div>
        <p className="mb-2 text-sm text-neutral-600">Primary</p>
        <ProgressBar value={70} color="primary" showLabel />
      </div>
      <div>
        <p className="mb-2 text-sm text-neutral-600">Success</p>
        <ProgressBar value={100} color="success" showLabel />
      </div>
      <div>
        <p className="mb-2 text-sm text-neutral-600">Warning</p>
        <ProgressBar value={45} color="warning" showLabel />
      </div>
      <div>
        <p className="mb-2 text-sm text-neutral-600">Error</p>
        <ProgressBar value={25} color="error" showLabel />
      </div>
    </div>
  ),
};

/**
 * Animated progress simulation
 */
export const AnimatedProgress: Story = {
  render: () => {
    const [progress, setProgress] = useState(0);

    useEffect(() => {
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) return 0;
          return prev + 1;
        });
      }, 50);

      return () => clearInterval(interval);
    }, []);

    return (
      <div className="w-96">
        <ProgressBar
          value={progress}
          size="lg"
          color="primary"
          showLabel
          label="Processing"
        />
      </div>
    );
  },
};

/**
 * Upload simulation
 */
export const UploadSimulation: Story = {
  render: () => {
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);

    const handleUpload = () => {
      setUploading(true);
      setProgress(0);

      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            setTimeout(() => setUploading(false), 500);
            return 100;
          }
          return prev + Math.random() * 10;
        });
      }, 200);
    };

    return (
      <Card2 className="w-96 p-6">
        <h3 className="text-lg font-semibold text-neutral-900">File Upload</h3>
        <p className="mt-2 text-sm text-neutral-600">
          Simulate a file upload with progress tracking
        </p>

        <div className="mt-6">
          {uploading ? (
            <ProgressBar
              value={progress}
              size="md"
              color="primary"
              showLabel
              label="Uploading file..."
            />
          ) : (
            <Button2 onClick={handleUpload} fullWidth>
              Start Upload
            </Button2>
          )}
        </div>

        {progress === 100 && (
          <p className="mt-4 text-center text-sm font-medium text-success-600">
            ✓ Upload complete!
          </p>
        )}
      </Card2>
    );
  },
};

/**
 * Multiple progress bars
 */
export const MultipleProgressBars: Story = {
  render: () => (
    <div className="w-96 space-y-6">
      <div>
        <ProgressBar value={85} color="success" showLabel label="Task 1" />
      </div>
      <div>
        <ProgressBar value={60} color="primary" showLabel label="Task 2" />
      </div>
      <div>
        <ProgressBar value={30} color="warning" showLabel label="Task 3" />
      </div>
      <div>
        <ProgressBar color="primary" label="Task 4 (processing...)" />
      </div>
    </div>
  ),
};

/**
 * In a card context
 */
export const InCard: Story = {
  render: () => (
    <Card2 className="w-96 p-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-neutral-900">Processing Data</h3>
        <span className="text-sm text-neutral-600">Step 2 of 3</span>
      </div>
      <p className="mt-2 text-sm text-neutral-600">
        Analyzing your information and generating insights...
      </p>
      <div className="mt-6">
        <ProgressBar value={67} size="lg" color="primary" showLabel />
      </div>
    </Card2>
  ),
};

/**
 * Completion states
 */
export const CompletionStates: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-700">In Progress</p>
        <ProgressBar value={45} color="primary" showLabel label="Processing" />
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-700">Almost Done</p>
        <ProgressBar value={90} color="warning" showLabel label="Finalizing" />
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-700">Complete</p>
        <ProgressBar value={100} color="success" showLabel label="Completed" />
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-700">Failed</p>
        <ProgressBar value={35} color="error" showLabel label="Error occurred" />
      </div>
    </div>
  ),
};
