import React from 'react';
import { FormProvider, SubmitHandler, UseFormReturn, FieldValues } from 'react-hook-form';

export interface FormProps<T extends FieldValues> {
    methods: UseFormReturn<T>;
    onSubmit: SubmitHandler<T>;
    children: React.ReactNode;
    className?: string;
}

export function Form<T extends FieldValues>({ methods, onSubmit, children, className }: FormProps<T>) {
    return (
        <FormProvider {...methods}>
            <form onSubmit={methods.handleSubmit(onSubmit)} className={className}>
                {children}
            </form>
        </FormProvider>
    );
}

export function FormField({ children, className }: { children: React.ReactNode; className?: string }) {
    return <div className={className}>{children}</div>;
}

export function FormLabel({ children, htmlFor, className }: { children: React.ReactNode; htmlFor?: string; className?: string }) {
    return (
        <label htmlFor={htmlFor} className={`block text-sm font-medium text-neutral-700 mb-1 ${className || ''}`}>
            {children}
        </label>
    );
}

export function FormError({ message, className }: { message?: string; className?: string }) {
    if (!message) return null;
    return <p className={`mt-1 text-sm text-error-600 ${className || ''}`}>{message}</p>;
}
