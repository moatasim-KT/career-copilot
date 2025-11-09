import * as z from 'zod';

export const emailSchema = z.string().email('Invalid email address');
export const passwordSchema = z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Must contain an uppercase letter')
    .regex(/[a-z]/, 'Must contain a lowercase letter')
    .regex(/[0-9]/, 'Must contain a number')
    .regex(/[^A-Za-z0-9]/, 'Must contain a special character');
export const phoneSchema = z.string().regex(/^\+?[0-9]{10,15}$/, 'Invalid phone number');
export const urlSchema = z.string().url('Invalid URL');

export const profileSchema = z.object({
    email: emailSchema,
    password: passwordSchema.optional(),
    phone: phoneSchema.optional(),
    website: urlSchema.optional(),
});

export type ProfileFormValues = z.infer<typeof profileSchema>;
