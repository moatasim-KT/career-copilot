
import { zodResolver } from '@hookform/resolvers/zod';
import React from 'react';
import { useForm } from 'react-hook-form';

import { profileSchema, ProfileFormValues } from '@/lib/validation';

import { Button } from './Button2';
import { Form, FormField, FormLabel, FormError } from './Form';
import { Input2 } from './Input2';

export default function FormExample() {
    const methods = useForm<ProfileFormValues>({
        resolver: zodResolver(profileSchema),
        defaultValues: { email: '', password: '', phone: '', website: '' },
    });

    const onSubmit = (data: ProfileFormValues) => {
        alert(JSON.stringify(data, null, 2));
    };

    return (
        <Form methods={methods} onSubmit={onSubmit} className="space-y-6 max-w-md mx-auto">
            <FormField>
                <FormLabel htmlFor="email">Email</FormLabel>
                <Input2 {...methods.register('email')} id="email" type="email" autoComplete="email" />
                <FormError message={methods.formState.errors.email?.message} />
            </FormField>
            <FormField>
                <FormLabel htmlFor="password">Password</FormLabel>
                <Input2 {...methods.register('password')} id="password" type="password" autoComplete="new-password" />
                <FormError message={methods.formState.errors.password?.message} />
            </FormField>
            <FormField>
                <FormLabel htmlFor="phone">Phone</FormLabel>
                <Input2 {...methods.register('phone')} id="phone" type="tel" autoComplete="tel" />
                <FormError message={methods.formState.errors.phone?.message} />
            </FormField>
            <FormField>
                <FormLabel htmlFor="website">Website</FormLabel>
                <Input2 {...methods.register('website')} id="website" type="url" autoComplete="url" />
                <FormError message={methods.formState.errors.website?.message} />
            </FormField>
            <Button type="submit">Submit</Button>
        </Form>
    );
}
