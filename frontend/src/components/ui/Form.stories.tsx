import React from 'react';
import { Form } from './Form';
import Button from './Button2';
import Input from './Input2';
import { useForm } from 'react-hook-form';
import type { Meta, StoryObj } from '@storybook/react';

const meta: Meta<typeof Form> = {
    title: 'Components/UI/Form',
    component: Form,
    tags: ['autodocs'],
};
export default meta;
type Story = StoryObj<typeof Form>;

export const ExampleForm: Story = {
    render: () => {
        const methods = useForm();
        return (
            <Form methods={methods} onSubmit={(data) => alert(JSON.stringify(data))}>
                <Input name="email" label="Email" placeholder="Enter your email" required />
                <Input name="password" label="Password" type="password" placeholder="Enter your password" required />
                <Button type="submit" variant="primary">Submit</Button>
            </Form>
        );
    },
};
