import React, { useState } from 'react';
import { FileUpload2 } from './FileUpload2';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof FileUpload2> = {
    title: 'Components/UI/FileUpload2',
    component: FileUpload2,
    tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof FileUpload2>;

export const Default: Story = {
    render: () => {
        const [files, setFiles] = useState<File[]>([]);
        return <FileUpload2 value={files} onChange={setFiles} />;
    },
};

export const Multiple: Story = {
    render: () => {
        const [files, setFiles] = useState<File[]>([]);
        return <FileUpload2 value={files} onChange={setFiles} multiple />;
    },
};

export const WithPreview: Story = {
    render: () => {
        const [files, setFiles] = useState<File[]>([]);
        return <FileUpload2 value={files} onChange={setFiles} multiple preview />;
    },
};
