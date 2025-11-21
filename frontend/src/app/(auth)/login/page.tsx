'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import React, { useState, useEffect } from 'react';
import {
    LayoutDashboard,
    ArrowRight,
    CheckCircle2
} from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { OptimizedLogo } from '@/components/ui/OptimizedImage';

export default function LoginPage() {
    const { login, isAuthenticated } = useAuth();
    const router = useRouter();
    const [formData, setFormData] = useState({
        identifier: '', // Can be username or email
        password: '',
    });
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (isAuthenticated) {
            router.push('/dashboard');
        }
    }, [isAuthenticated, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await login(formData.identifier, formData.password);
            // login() handles redirect to dashboard
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An unexpected error occurred');
        } finally {
            setIsLoading(false);
        }
    };

    const handleOAuthLogin = (provider: 'google' | 'linkedin' | 'github') => {
        // Redirect to OAuth endpoint
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        window.location.href = `${baseUrl}/api/v1/auth/oauth/${provider}/login`;
    };

    return (
        <div className="min-h-screen flex flex-row bg-slate-50 dark:bg-slate-950">
            {/* Hero Section (Left Side) */}
            <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-slate-900 min-h-screen">
                <div className="absolute inset-0 bg-gradient-brand opacity-90 z-10"></div>
                <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center mask-[linear-gradient(180deg,white,rgba(255,255,255,0))] z-0"></div>

                <div className="relative z-20 flex flex-col justify-between h-full p-12 text-white">
                    <div className="flex items-center space-x-3">
                        <div className="p-2 bg-white/10 backdrop-blur-md rounded-lg border border-white/20">
                            <LayoutDashboard className="h-8 w-8 text-white" />
                        </div>
                        <span className="text-3xl font-bold tracking-tight">Career Copilot</span>
                    </div>

                    <div className="space-y-8 max-w-lg">
                        <h1 className="text-5xl font-bold leading-tight">
                            Accelerate your <br />
                            <span className="text-transparent bg-clip-text bg-linear-to-r from-indigo-200 to-white">
                                career growth
                            </span>
                        </h1>
                        <p className="text-lg text-indigo-100 leading-relaxed">
                            AI-powered job tracking, smart recommendations, and real-time analytics to help you land your dream job faster.
                        </p>

                        <div className="space-y-4 pt-4">
                            {[
                                'Smart Job Matching',
                                'Automated Application Tracking',
                                'Skill Gap Analysis',
                                'Real-time Market Insights'
                            ].map((feature, index) => (
                                <div key={index} className="flex items-center space-x-3 text-indigo-50">
                                    <CheckCircle2 className="h-5 w-5 text-indigo-300" />
                                    <span>{feature}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="text-sm text-indigo-200">
                        © {new Date().getFullYear()} Career Copilot. All rights reserved.
                    </div>
                </div>
            </div>

            {/* Login Form (Right Side) */}
            <div className="w-full lg:w-1/2 flex items-center justify-center p-8 relative z-30 min-h-screen">
                <div className="w-full max-w-md space-y-8">
                    <div className="text-center lg:text-left">
                        <div className="lg:hidden flex justify-center mb-6">
                            <div className="p-2 bg-indigo-600 rounded-lg">
                                <LayoutDashboard className="h-8 w-8 text-white" />
                            </div>
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
                            Welcome back
                        </h2>
                        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                            Please enter your details to sign in.
                        </p>
                    </div>


                    <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                        {error && (
                            <div className="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 text-red-600 dark:text-red-400 text-sm font-medium animate-fade-in">
                                {error}
                            </div>
                        )}

                        <div className="space-y-6">
                            <div>
                                <label htmlFor="identifier" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                                    Email or Username
                                </label>
                                <input
                                    id="identifier"
                                    name="identifier"
                                    type="text"
                                    required
                                    className="input-field"
                                    placeholder="Enter your email"
                                    value={formData.identifier}
                                    onChange={(e) => setFormData({ ...formData, identifier: e.target.value })}
                                />
                            </div>

                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <label htmlFor="password" className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                                        Password
                                    </label>
                                    <Link
                                        href="/forgot-password"
                                        className="text-sm font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400"
                                    >
                                        Forgot password?
                                    </Link>
                                </div>
                                <input
                                    id="password"
                                    name="password"
                                    type="password"
                                    required
                                    className="input-field"
                                    placeholder="••••••••"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                />
                            </div>
                        </div>

                        <div className="flex items-center pt-2">
                            <input
                                id="remember-me"
                                name="remember-me"
                                type="checkbox"
                                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded"
                            />
                            <label htmlFor="remember-me" className="ml-2 block text-sm text-slate-700 dark:text-slate-300">
                                Remember me for 30 days
                            </label>
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full btn-primary flex items-center justify-center space-x-2 mt-6"
                        >
                            {isLoading ? (
                                <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <span>Sign in</span>
                                    <ArrowRight className="h-4 w-4" />
                                </>
                            )}
                        </button>

                        <div className="relative my-10">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-slate-200 dark:border-slate-700" />
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-4 bg-slate-50 dark:bg-slate-950 text-slate-600 dark:text-slate-400">
                                    Or continue with
                                </span>
                            </div>
                        </div>


                        <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto">
                            <button
                                type="button"
                                onClick={() => handleOAuthLogin('github')}
                                className="btn-secondary flex items-center justify-center space-x-2 py-3"
                            >
                                <img src="/images/github.svg" alt="GitHub" className="w-5 h-5 object-contain" />
                                <span>GitHub</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => handleOAuthLogin('google')}
                                className="btn-secondary flex items-center justify-center space-x-2 py-3"
                            >
                                <img src="/images/google.svg" alt="Google" className="w-5 h-5 object-contain" />
                                <span>Google</span>
                            </button>
                        </div>

                        <p className="text-center text-sm text-slate-600 dark:text-slate-400 mt-10">
                            Don't have an account?{' '}
                            <Link href="/register" className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 transition-colors">
                                Sign up for free
                            </Link>
                        </p>
                    </form>
                </div>
            </div>
        </div>
    );
}
