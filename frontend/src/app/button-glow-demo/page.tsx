'use client';

import { Sparkles, Trash2, Check, Zap, Download, Upload, Save, Send } from 'lucide-react';
import { useState } from 'react';

import Button from '@/components/ui/Button2';

export default function ButtonGlowDemo() {
  const [showSuccess, setShowSuccess] = useState(false);

  const handleCriticalAction = () => {
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100 dark:from-neutral-900 dark:to-neutral-950 p-8">
      <div className="max-w-6xl mx-auto space-y-12">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-neutral-900 dark:text-white">
            Button Glow Effects Demo
          </h1>
          <p className="text-lg text-neutral-600 dark:text-neutral-400">
            Showcasing enhanced button interactions with glow effects, gradients, and pulse animations
          </p>
        </div>

        {/* Primary CTAs with Glow */}
        <section className="bg-white dark:bg-neutral-800 rounded-2xl p-8 shadow-lg">
          <h2 className="text-2xl font-semibold mb-6 text-neutral-900 dark:text-white">
            Primary CTAs with Glow
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-6">
            Primary buttons with glow effects that intensify on hover
          </p>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary" glow size="lg" icon={<Sparkles className="w-5 h-5" />}>
              Get Started
            </Button>
            <Button variant="primary" glow icon={<Download className="w-4 h-4" />}>
              Download Now
            </Button>
            <Button variant="primary" glow size="sm" icon={<Send className="w-4 h-4" />}>
              Send Message
            </Button>
          </div>
        </section>

        {/* Gradient Buttons */}
        <section className="bg-white dark:bg-neutral-800 rounded-2xl p-8 shadow-lg">
          <h2 className="text-2xl font-semibold mb-6 text-neutral-900 dark:text-white">
            Gradient Variant
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-6">
            New gradient button variant with animated background shift on hover
          </p>
          <div className="flex flex-wrap gap-4">
            <Button variant="gradient" size="xl" icon={<Zap className="w-5 h-5" />}>
              Upgrade to Pro
            </Button>
            <Button variant="gradient" glow size="lg" icon={<Sparkles className="w-5 h-5" />}>
              Premium Feature
            </Button>
            <Button variant="gradient" glow icon={<Upload className="w-4 h-4" />}>
              Upload File
            </Button>
          </div>
        </section>

        {/* Success Actions */}
        <section className="bg-white dark:bg-neutral-800 rounded-2xl p-8 shadow-lg">
          <h2 className="text-2xl font-semibold mb-6 text-neutral-900 dark:text-white">
            Success Actions with Glow
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-6">
            Success variant buttons with green glow effects
          </p>
          <div className="flex flex-wrap gap-4">
            <Button variant="success" glow size="lg" icon={<Check className="w-5 h-5" />}>
              Confirm
            </Button>
            <Button variant="success" glow icon={<Save className="w-4 h-4" />}>
              Save Changes
            </Button>
            <Button 
              variant="success" 
              glow 
              success={showSuccess}
              onClick={handleCriticalAction}
            >
              {showSuccess ? 'Saved!' : 'Click Me'}
            </Button>
          </div>
        </section>

        {/* Critical Actions with Pulse */}
        <section className="bg-white dark:bg-neutral-800 rounded-2xl p-8 shadow-lg">
          <h2 className="text-2xl font-semibold mb-6 text-neutral-900 dark:text-white">
            Critical Actions with Pulse Animation
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-6">
            Buttons with pulsing glow to draw attention to critical actions
          </p>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary" glow pulse size="lg" icon={<Zap className="w-5 h-5" />}>
              Start Free Trial
            </Button>
            <Button variant="gradient" glow pulse size="lg" icon={<Sparkles className="w-5 h-5" />}>
              Limited Offer
            </Button>
            <Button variant="destructive" glow pulse icon={<Trash2 className="w-4 h-4" />}>
              Delete Account
            </Button>
          </div>
        </section>

        {/* Destructive Actions */}
        <section className="bg-white dark:bg-neutral-800 rounded-2xl p-8 shadow-lg">
          <h2 className="text-2xl font-semibold mb-6 text-neutral-900 dark:text-white">
            Destructive Actions with Glow
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-6">
            Destructive buttons with red glow for dangerous actions
          </p>
          <div className="flex flex-wrap gap-4">
            <Button variant="destructive" glow size="lg" icon={<Trash2 className="w-5 h-5" />}>
              Delete Forever
            </Button>
            <Button variant="destructive" glow icon={<Trash2 className="w-4 h-4" />}>
              Remove Item
            </Button>
          </div>
        </section>

        {/* Size Variations */}
        <section className="bg-white dark:bg-neutral-800 rounded-2xl p-8 shadow-lg">
          <h2 className="text-2xl font-semibold mb-6 text-neutral-900 dark:text-white">
            All Sizes with Glow
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-6">
            Glow effects work across all button sizes
          </p>
          <div className="flex flex-wrap items-center gap-4">
            <Button variant="primary" glow size="xs">Extra Small</Button>
            <Button variant="primary" glow size="sm">Small</Button>
            <Button variant="primary" glow size="md">Medium</Button>
            <Button variant="primary" glow size="lg">Large</Button>
            <Button variant="primary" glow size="xl">Extra Large</Button>
          </div>
        </section>

        {/* Comparison Grid */}
        <section className="bg-white dark:bg-neutral-800 rounded-2xl p-8 shadow-lg">
          <h2 className="text-2xl font-semibold mb-6 text-neutral-900 dark:text-white">
            With vs Without Glow
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-6">
            Side-by-side comparison of buttons with and without glow effects
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-medium mb-4 text-neutral-700 dark:text-neutral-300">
                Without Glow
              </h3>
              <div className="space-y-3">
                <Button variant="primary" fullWidth>Primary</Button>
                <Button variant="success" fullWidth>Success</Button>
                <Button variant="destructive" fullWidth>Destructive</Button>
                <Button variant="gradient" fullWidth>Gradient</Button>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-medium mb-4 text-neutral-700 dark:text-neutral-300">
                With Glow
              </h3>
              <div className="space-y-3">
                <Button variant="primary" glow fullWidth>Primary</Button>
                <Button variant="success" glow fullWidth>Success</Button>
                <Button variant="destructive" glow fullWidth>Destructive</Button>
                <Button variant="gradient" glow fullWidth>Gradient</Button>
              </div>
            </div>
          </div>
        </section>

        {/* Dark Background Demo */}
        <section className="bg-neutral-900 rounded-2xl p-8 shadow-lg">
          <h2 className="text-2xl font-semibold mb-6 text-white">
            Glow Effects on Dark Background
          </h2>
          <p className="text-neutral-400 mb-6">
            Glow effects are optimized for dark backgrounds with enhanced visibility
          </p>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary" glow size="lg">Primary Glow</Button>
            <Button variant="gradient" glow size="lg">Gradient Glow</Button>
            <Button variant="success" glow size="lg">Success Glow</Button>
            <Button variant="destructive" glow size="lg">Destructive Glow</Button>
          </div>
        </section>

        {/* Interactive Demo */}
        <section className="bg-white dark:bg-neutral-800 rounded-2xl p-8 shadow-lg">
          <h2 className="text-2xl font-semibold mb-6 text-neutral-900 dark:text-white">
            Interactive Demo
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400 mb-6">
            Hover over buttons to see the glow intensity increase
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center space-y-4">
              <Button variant="primary" glow fullWidth size="lg">
                Hover Me
              </Button>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Primary with glow
              </p>
            </div>
            <div className="text-center space-y-4">
              <Button variant="gradient" glow fullWidth size="lg">
                Hover Me
              </Button>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Gradient with glow
              </p>
            </div>
            <div className="text-center space-y-4">
              <Button variant="primary" glow pulse fullWidth size="lg">
                Hover Me
              </Button>
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                With pulse animation
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
