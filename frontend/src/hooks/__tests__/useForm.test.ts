import { renderHook, act } from '@testing-library/react';

import { useForm } from '../useForm';

describe('useForm', () => {
    const initialValues = {
        email: '',
        password: '',
        remember: false,
    };

    it('should initialize with provided values', () => {
        const { result } = renderHook(() => useForm(initialValues));

        expect(result.current.values).toEqual(initialValues);
        expect(result.current.errors).toEqual({});
        expect(result.current.touched).toEqual({});
    });

    it('should handle value changes', () => {
        const { result } = renderHook(() => useForm(initialValues));

        act(() => {
            result.current.handleChange('email', 'test@example.com');
        });

        expect(result.current.values.email).toBe('test@example.com');
    });

    it('should handle blur events', () => {
        const { result } = renderHook(() => useForm(initialValues));

        act(() => {
            result.current.handleBlur('email');
        });

        expect(result.current.touched.email).toBe(true);
    });

    it('should set errors', () => {
        const { result } = renderHook(() => useForm(initialValues));

        act(() => {
            result.current.setError('email', 'Invalid email');
        });

        expect(result.current.errors.email).toBe('Invalid email');
    });

    it('should clear errors', () => {
        const { result } = renderHook(() => useForm(initialValues));

        act(() => {
            result.current.setError('email', 'Invalid email');
        });

        expect(result.current.errors.email).toBe('Invalid email');

        act(() => {
            result.current.clearError('email');
        });

        expect(result.current.errors.email).toBeUndefined();
    });

    it('should set all errors at once', () => {
        const { result } = renderHook(() => useForm(initialValues));

        act(() => {
            result.current.setAllErrors({
                email: 'Invalid email',
                password: 'Password required',
            });
        });

        expect(result.current.errors.email).toBe('Invalid email');
        expect(result.current.errors.password).toBe('Password required');
    });

    it('should reset form to initial values', () => {
        const { result } = renderHook(() => useForm(initialValues));

        act(() => {
            result.current.handleChange('email', 'test@example.com');
            result.current.setError('email', 'Invalid email');
            result.current.handleBlur('email');
        });

        expect(result.current.values.email).toBe('test@example.com');
        expect(result.current.errors.email).toBe('Invalid email');
        expect(result.current.touched.email).toBe(true);

        act(() => {
            result.current.reset();
        });

        expect(result.current.values).toEqual(initialValues);
        expect(result.current.errors).toEqual({});
        expect(result.current.touched).toEqual({});
    });

    it('should allow setting values directly', () => {
        const { result } = renderHook(() => useForm(initialValues));

        act(() => {
            result.current.setValues({
                email: 'new@example.com',
                password: 'newpass',
                remember: true,
            });
        });

        expect(result.current.values.email).toBe('new@example.com');
        expect(result.current.values.password).toBe('newpass');
        expect(result.current.values.remember).toBe(true);
    });
});
