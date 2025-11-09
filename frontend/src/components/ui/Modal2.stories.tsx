import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';

import Button2 from './Button2';
import Modal2 from './Modal2';

const meta: Meta<typeof Modal2> = {
  title: 'UI/Modal2',
  component: Modal2,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof Modal2>;

// Wrapper component to handle state
const ModalWrapper = (args: any) => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button2 onClick={() => setOpen(true)}>Open Modal</Button2>
      <Modal2 {...args} open={open} onClose={() => setOpen(false)}>
        <div className="space-y-4">
          <p className="text-neutral-600 dark:text-neutral-300">
            This is a modal with smooth animations. It features:
          </p>
          <ul className="list-disc list-inside space-y-2 text-neutral-600 dark:text-neutral-300">
            <li>Backdrop fade animation</li>
            <li>Content scale animation on desktop</li>
            <li>Slide-in from bottom on mobile</li>
            <li>Smooth exit animations</li>
          </ul>
          <div className="flex gap-2 justify-end mt-6">
            <Button2 variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button2>
            <Button2 onClick={() => setOpen(false)}>Confirm</Button2>
          </div>
        </div>
      </Modal2>
    </>
  );
};

export const Default: Story = {
  render: (args) => <ModalWrapper {...args} />,
  args: {
    title: 'Modal Title',
    description: 'This is a description of the modal',
  },
};

export const Small: Story = {
  render: (args) => <ModalWrapper {...args} />,
  args: {
    title: 'Small Modal',
    description: 'This modal uses the small size variant',
    size: 'sm',
  },
};

export const Large: Story = {
  render: (args) => <ModalWrapper {...args} />,
  args: {
    title: 'Large Modal',
    description: 'This modal uses the large size variant',
    size: 'lg',
  },
};

export const ExtraLarge: Story = {
  render: (args) => <ModalWrapper {...args} />,
  args: {
    title: 'Extra Large Modal',
    description: 'This modal uses the extra large size variant',
    size: 'xl',
  },
};

export const NoCloseButton: Story = {
  render: (args) => <ModalWrapper {...args} />,
  args: {
    title: 'No Close Button',
    description: 'This modal hides the close button',
    showClose: false,
  },
};

export const NoTitleOrDescription: Story = {
  render: (args) => <ModalWrapper {...args} />,
  args: {
    showClose: true,
  },
};

export const LongContent: Story = {
  render: (args) => <ModalWrapper {...args} />,
  args: {
    title: 'Modal with Long Content',
    description: 'This modal contains a lot of content to demonstrate scrolling',
    children: (
      <div className="space-y-4">
        {Array.from({ length: 20 }, (_, i) => (
          <p key={i} className="text-neutral-600 dark:text-neutral-300">
            This is paragraph {i + 1}. Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
          </p>
        ))}
      </div>
    ),
  },
};

export const WithForm: Story = {
  render: (args) => <ModalWrapper {...args} />,
  args: {
    title: 'Contact Form',
    description: 'Fill out the form below to get in touch',
    children: (
      <form className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
            Name
          </label>
          <input
            type="text"
            id="name"
            className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-neutral-800 dark:text-neutral-100"
            placeholder="Enter your name"
          />
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
            Email
          </label>
          <input
            type="email"
            id="email"
            className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-neutral-800 dark:text-neutral-100"
            placeholder="Enter your email"
          />
        </div>
        <div>
          <label htmlFor="message" className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
            Message
          </label>
          <textarea
            id="message"
            rows={4}
            className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-neutral-800 dark:text-neutral-100"
            placeholder="Enter your message"
          />
        </div>
        <div className="flex gap-2 justify-end">
          <Button2 type="button" variant="outline">
            Cancel
          </Button2>
          <Button2 type="submit">Send Message</Button2>
        </div>
      </form>
    ),
  },
};
