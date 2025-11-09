import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import LoadingOverlay from './LoadingOverlay';
import Button2 from './Button2';
import Card2 from './Card2';

const meta = {
  title: 'UI/Loading/LoadingOverlay',
  component: LoadingOverlay,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof LoadingOverlay>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Basic loading overlay
 */
export const Default: Story = {
  render: () => {
    const [visible, setVisible] = useState(false);

    return (
      <div className="relative h-screen p-8">
        <Button2 onClick={() => setVisible(!visible)}>
          Toggle Overlay
        </Button2>

        <div className="mt-8">
          <h1 className="text-2xl font-bold text-neutral-900">Page Content</h1>
          <p className="mt-4 text-neutral-600">
            This is the main content of the page. Click the button to show the loading overlay.
          </p>
        </div>

        <LoadingOverlay visible={visible} />
      </div>
    );
  },
};

/**
 * With message
 */
export const WithMessage: Story = {
  render: () => {
    const [visible, setVisible] = useState(false);

    return (
      <div className="relative h-screen p-8">
        <Button2 onClick={() => setVisible(!visible)}>
          Toggle Overlay
        </Button2>

        <div className="mt-8">
          <h1 className="text-2xl font-bold text-neutral-900">Page Content</h1>
          <p className="mt-4 text-neutral-600">
            Loading overlay with a custom message.
          </p>
        </div>

        <LoadingOverlay visible={visible} message="Loading your data..." />
      </div>
    );
  },
};

/**
 * Dots indicator
 */
export const DotsIndicator: Story = {
  render: () => {
    const [visible, setVisible] = useState(false);

    return (
      <div className="relative h-screen p-8">
        <Button2 onClick={() => setVisible(!visible)}>
          Toggle Overlay
        </Button2>

        <div className="mt-8">
          <h1 className="text-2xl font-bold text-neutral-900">Page Content</h1>
          <p className="mt-4 text-neutral-600">
            Loading overlay with dots indicator.
          </p>
        </div>

        <LoadingOverlay
          visible={visible}
          indicator="dots"
          message="Processing your request..."
        />
      </div>
    );
  },
};

/**
 * Container-relative overlay
 */
export const ContainerRelative: Story = {
  render: () => {
    const [visible, setVisible] = useState(false);

    return (
      <div className="p-8">
        <Button2 onClick={() => setVisible(!visible)} className="mb-4">
          Toggle Overlay
        </Button2>

        <Card2 className="relative p-8">
          <h2 className="text-xl font-semibold text-neutral-900">Card Content</h2>
          <p className="mt-4 text-neutral-600">
            This card has a loading overlay that only covers the card area, not the entire screen.
          </p>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <div className="rounded-lg bg-neutral-100 p-4">
              <h3 className="font-medium text-neutral-900">Section 1</h3>
              <p className="mt-2 text-sm text-neutral-600">Some content here</p>
            </div>
            <div className="rounded-lg bg-neutral-100 p-4">
              <h3 className="font-medium text-neutral-900">Section 2</h3>
              <p className="mt-2 text-sm text-neutral-600">More content here</p>
            </div>
          </div>

          <LoadingOverlay
            visible={visible}
            fullScreen={false}
            message="Loading card data..."
          />
        </Card2>
      </div>
    );
  },
};

/**
 * Without blur
 */
export const WithoutBlur: Story = {
  render: () => {
    const [visible, setVisible] = useState(false);

    return (
      <div className="relative h-screen p-8">
        <Button2 onClick={() => setVisible(!visible)}>
          Toggle Overlay
        </Button2>

        <div className="mt-8">
          <h1 className="text-2xl font-bold text-neutral-900">Page Content</h1>
          <p className="mt-4 text-neutral-600">
            Loading overlay without backdrop blur.
          </p>
        </div>

        <LoadingOverlay visible={visible} blur={false} message="Loading..." />
      </div>
    );
  },
};

/**
 * Custom opacity
 */
export const CustomOpacity: Story = {
  render: () => {
    const [visible, setVisible] = useState(false);

    return (
      <div className="relative h-screen p-8">
        <Button2 onClick={() => setVisible(!visible)}>
          Toggle Overlay
        </Button2>

        <div className="mt-8">
          <h1 className="text-2xl font-bold text-neutral-900">Page Content</h1>
          <p className="mt-4 text-neutral-600">
            Loading overlay with custom opacity (0.95).
          </p>
        </div>

        <LoadingOverlay
          visible={visible}
          opacity={0.95}
          message="Almost there..."
        />
      </div>
    );
  },
};

/**
 * Auto-dismiss after delay
 */
export const AutoDismiss: Story = {
  render: () => {
    const [visible, setVisible] = useState(false);

    const handleShow = () => {
      setVisible(true);
      setTimeout(() => setVisible(false), 3000);
    };

    return (
      <div className="relative h-screen p-8">
        <Button2 onClick={handleShow}>
          Show Overlay (Auto-dismiss in 3s)
        </Button2>

        <div className="mt-8">
          <h1 className="text-2xl font-bold text-neutral-900">Page Content</h1>
          <p className="mt-4 text-neutral-600">
            The overlay will automatically dismiss after 3 seconds.
          </p>
        </div>

        <LoadingOverlay
          visible={visible}
          message="Loading... (will auto-dismiss)"
        />
      </div>
    );
  },
};

/**
 * Multiple containers
 */
export const MultipleContainers: Story = {
  render: () => {
    const [visible1, setVisible1] = useState(false);
    const [visible2, setVisible2] = useState(false);

    return (
      <div className="space-y-4 p-8">
        <div className="flex gap-4">
          <Button2 onClick={() => setVisible1(!visible1)}>
            Toggle Card 1
          </Button2>
          <Button2 onClick={() => setVisible2(!visible2)}>
            Toggle Card 2
          </Button2>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Card2 className="relative p-6">
            <h3 className="text-lg font-semibold text-neutral-900">Card 1</h3>
            <p className="mt-2 text-neutral-600">
              This card has its own loading overlay.
            </p>
            <LoadingOverlay
              visible={visible1}
              fullScreen={false}
              indicator="dots"
              message="Loading Card 1..."
            />
          </Card2>

          <Card2 className="relative p-6">
            <h3 className="text-lg font-semibold text-neutral-900">Card 2</h3>
            <p className="mt-2 text-neutral-600">
              This card has its own loading overlay.
            </p>
            <LoadingOverlay
              visible={visible2}
              fullScreen={false}
              message="Loading Card 2..."
            />
          </Card2>
        </div>
      </div>
    );
  },
};
