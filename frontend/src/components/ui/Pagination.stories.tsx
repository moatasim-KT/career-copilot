
import { Meta, StoryObj } from '@storybook/react';
import Pagination from './Pagination';

const meta: Meta<typeof Pagination> = {
  title: 'UI/Pagination',
  component: Pagination,
};

export default meta;

type Story = StoryObj<typeof Pagination>;

export const Default: Story = {
  args: {
    currentPage: 1,
    totalPages: 10,
    onPageChange: (page) => console.log(`Page changed to: ${page}`),
  },
};

export const MiddlePage: Story = {
  args: {
    currentPage: 5,
    totalPages: 10,
    onPageChange: (page) => console.log(`Page changed to: ${page}`),
  },
};

export const LastPage: Story = {
  args: {
    currentPage: 10,
    totalPages: 10,
    onPageChange: (page) => console.log(`Page changed to: ${page}`),
  },
};
