'use client';

/**
 * LoadingStatesDemo - Comprehensive demonstration of all loading state components
 * 
 * This file demonstrates the usage of:
 * - Spinner2: Smooth rotating spinner with multiple variants
 * - DotsLoader: Three-dot bouncing animation
 * - LoadingTransition: Skeleton to content crossfade
 * - StaggerReveal: Sequential reveal animation for multiple items
 * - LoadingOverlay: Full-screen or container loading overlay
 * - ProgressBar: Determinate and indeterminate progress indicators
 */

import { useState, useEffect } from 'react';
import Spinner2 from './Spinner2';
import DotsLoader from './DotsLoader';
import LoadingTransition from './LoadingTransition';
import StaggerReveal, { StaggerRevealItem } from './StaggerReveal';
import LoadingOverlay from './LoadingOverlay';
import ProgressBar from './ProgressBar';
import Skeleton2 from './Skeleton2';
import Card2 from './Card2';
import Button2 from './Button2';

export default function LoadingStatesDemo() {
  const [showOverlay, setShowOverlay] = useState(false);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0);

  // Simulate loading completion
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  // Simulate progress
  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) return 0;
        return prev + 2;
      });
    }, 100);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-neutral-50 p-8">
      <div className="mx-auto max-w-7xl space-y-12">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Loading States Demo</h1>
          <p className="mt-2 text-neutral-600">
            Comprehensive demonstration of all loading state components with smooth animations
          </p>
        </div>

        {/* Spinners */}
        <section>
          <h2 className="mb-4 text-2xl font-semibold text-neutral-900">Spinners</h2>
          <Card2 className="p-6">
            <div className="flex flex-wrap items-center gap-8">
              <div className="flex flex-col items-center gap-2">
                <Spinner2 size="sm" variant="smooth" />
                <span className="text-xs text-neutral-600">Small</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <Spinner2 size="md" variant="smooth" />
                <span className="text-xs text-neutral-600">Medium</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <Spinner2 size="lg" variant="smooth" />
                <span className="text-xs text-neutral-600">Large</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <Spinner2 size="lg" variant="pulsing" />
                <span className="text-xs text-neutral-600">Pulsing</span>
              </div>
              <div className="flex flex-col items-center gap-2">
                <DotsLoader size="lg" />
                <span className="text-xs text-neutral-600">Dots</span>
              </div>
            </div>
          </Card2>
        </section>

        {/* Progress Bars */}
        <section>
          <h2 className="mb-4 text-2xl font-semibold text-neutral-900">Progress Bars</h2>
          <Card2 className="space-y-6 p-6">
            <ProgressBar value={progress} showLabel label="Animated Progress" />
            <ProgressBar value={75} color="success" showLabel label="Success" />
            <ProgressBar value={45} color="warning" showLabel label="Warning" />
            <ProgressBar color="primary" label="Indeterminate" />
          </Card2>
        </section>

        {/* Loading Transition */}
        <section>
          <h2 className="mb-4 text-2xl font-semibold text-neutral-900">
            Skeleton to Content Transition
          </h2>
          <LoadingTransition
            loading={loading}
            skeleton={
              <Card2 className="p-6">
                <div className="space-y-4">
                  <Skeleton2 height={24} width="60%" />
                  <Skeleton2 height={16} width="100%" />
                  <Skeleton2 height={16} width="90%" />
                  <Skeleton2 height={16} width="95%" />
                </div>
              </Card2>
            }
          >
            <Card2 className="p-6">
              <h3 className="text-xl font-semibold text-neutral-900">Content Loaded!</h3>
              <p className="mt-4 text-neutral-600">
                This content smoothly faded in after the skeleton loading state. The transition
                provides a seamless user experience without jarring layout shifts.
              </p>
            </Card2>
          </LoadingTransition>
        </section>

        {/* Stagger Reveal */}
        <section>
          <h2 className="mb-4 text-2xl font-semibold text-neutral-900">Stagger Reveal</h2>
          <StaggerReveal className="grid gap-4 md:grid-cols-3">
            {[
              { icon: '🚀', title: 'Fast', desc: 'Optimized performance' },
              { icon: '🎨', title: 'Beautiful', desc: 'Modern design' },
              { icon: '🔒', title: 'Secure', desc: 'Enterprise-grade' },
            ].map((item, index) => (
              <StaggerRevealItem key={index}>
                <Card2 className="p-6 text-center">
                  <div className="text-4xl">{item.icon}</div>
                  <h3 className="mt-4 text-lg font-semibold text-neutral-900">{item.title}</h3>
                  <p className="mt-2 text-sm text-neutral-600">{item.desc}</p>
                </Card2>
              </StaggerRevealItem>
            ))}
          </StaggerReveal>
        </section>

        {/* Loading Overlay */}
        <section>
          <h2 className="mb-4 text-2xl font-semibold text-neutral-900">Loading Overlay</h2>
          <Card2 className="relative p-6">
            <h3 className="text-lg font-semibold text-neutral-900">Card with Overlay</h3>
            <p className="mt-2 text-neutral-600">
              Click the button to show a loading overlay on this card.
            </p>
            <Button2 onClick={() => setShowOverlay(!showOverlay)} className="mt-4">
              Toggle Overlay
            </Button2>

            <LoadingOverlay
              visible={showOverlay}
              fullScreen={false}
              message="Loading card data..."
            />
          </Card2>
        </section>

        {/* Inline Loading States */}
        <section>
          <h2 className="mb-4 text-2xl font-semibold text-neutral-900">Inline Loading States</h2>
          <Card2 className="space-y-4 p-6">
            <div className="flex items-center gap-2">
              <span className="text-sm text-neutral-700">Processing</span>
              <Spinner2 size="sm" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-neutral-700">Loading</span>
              <DotsLoader size="sm" />
            </div>
            <Button2 loading>Loading Button</Button2>
            <Button2 loading loadingText="Saving...">
              Save
            </Button2>
          </Card2>
        </section>

        {/* Best Practices */}
        <section>
          <h2 className="mb-4 text-2xl font-semibold text-neutral-900">Best Practices</h2>
          <Card2 className="p-6">
            <ul className="space-y-3 text-neutral-700">
              <li className="flex gap-2">
                <span className="text-success-600">✓</span>
                <span>Use skeleton screens for content that takes time to load</span>
              </li>
              <li className="flex gap-2">
                <span className="text-success-600">✓</span>
                <span>Show progress bars for operations with known duration</span>
              </li>
              <li className="flex gap-2">
                <span className="text-success-600">✓</span>
                <span>Use spinners for quick operations (under 2 seconds)</span>
              </li>
              <li className="flex gap-2">
                <span className="text-success-600">✓</span>
                <span>Provide loading messages for operations over 3 seconds</span>
              </li>
              <li className="flex gap-2">
                <span className="text-success-600">✓</span>
                <span>Use stagger reveal for lists to create visual interest</span>
              </li>
              <li className="flex gap-2">
                <span className="text-success-600">✓</span>
                <span>Ensure all loading states are accessible with ARIA labels</span>
              </li>
            </ul>
          </Card2>
        </section>
      </div>
    </div>
  );
}
