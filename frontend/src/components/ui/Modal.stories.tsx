
import { Meta, StoryObj } from '@storybook/react';
import Modal, { ModalFooter } from './Modal';
import Button from './Button';
import { useState } from 'react';

const meta: Meta<typeof Modal> = {
  title: 'UI/Modal',
  component: Modal,
  argTypes: {
    isOpen: { control: { type: 'boolean' } },
    size: { control: { type: 'select', options: ['sm', 'md', 'lg', 'xl'] } },
  },
};

export default meta;

type Story = StoryObj<typeof Modal>;

const ModalWithState = (args: any) => {
  const [isOpen, setIsOpen] = useState(args.isOpen);

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Open Modal</Button>
      <Modal {...args} isOpen={isOpen} onClose={() => setIsOpen(false)}>
        <p>This is the content of the modal.</p>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsOpen(false)}>Cancel</Button>
          <Button onClick={() => setIsOpen(false)}>Submit</Button>
        </ModalFooter>
      </Modal>
    </>
  );
};

export const Default: Story = {
  render: (args) => <ModalWithState {...args} />,
  args: {
    isOpen: false,
    title: 'Modal Title',
    size: 'md',
  },
};
