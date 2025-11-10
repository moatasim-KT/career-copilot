/**
 * Card2 Visual Test Component
 * 
 * This component demonstrates all the enhanced Card2 features.
 * Use this for manual visual testing and verification.
 * 
 * To test:
 * 1. Import this component in a page
 * 2. Toggle dark mode to test theme support
 * 3. Hover over cards to see animations
 * 4. Verify smooth transitions and effects
 */

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '../Card2';

export function Card2VisualTest() {
  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900 p-8">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-neutral-900 dark:text-neutral-100">
            Card2 Enhanced Features
          </h1>
          <p className="text-lg text-neutral-600 dark:text-neutral-400">
            Hover over cards to see the enhanced effects
          </p>
        </div>

        {/* Section 1: Enhanced Hover Effects */}
        <section className="space-y-4">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            1. Enhanced Hover Effects
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Smooth shadow expansion with increased lift and scale
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card hover elevation={1}>
              <CardHeader>
                <CardTitle>Elevation 1</CardTitle>
                <CardDescription>Hover for shadow expansion</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-neutral-600 dark:text-neutral-400">
                  Shadow expands from sm to xl with 6px lift
                </p>
              </CardContent>
            </Card>

            <Card hover elevation={2}>
              <CardHeader>
                <CardTitle>Elevation 2</CardTitle>
                <CardDescription>Enhanced animation</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-neutral-600 dark:text-neutral-400">
                  Smooth easeOut timing with subtle scale
                </p>
              </CardContent>
            </Card>

            <Card hover elevation={3} interactive>
              <CardHeader>
                <CardTitle>Interactive</CardTitle>
                <CardDescription>With cursor pointer</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-neutral-600 dark:text-neutral-400">
                  Perfect for clickable cards
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Section 2: Featured Cards with Glow */}
        <section className="space-y-4">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            2. Featured Cards with Glow Effect
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Colored glow effects for premium content
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card featured hover glowColor="primary">
              <CardHeader>
                <CardTitle>Primary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-primary-600 dark:text-primary-400">
                  $99
                </div>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                  Blue glow effect
                </p>
              </CardContent>
            </Card>

            <Card featured hover glowColor="success">
              <CardHeader>
                <CardTitle>Success</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-success-600 dark:text-success-400">
                  ✓
                </div>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                  Green glow effect
                </p>
              </CardContent>
            </Card>

            <Card featured hover glowColor="warning">
              <CardHeader>
                <CardTitle>Warning</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-warning-600 dark:text-warning-400">
                  ⚠
                </div>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                  Orange glow effect
                </p>
              </CardContent>
            </Card>

            <Card featured hover glowColor="error">
              <CardHeader>
                <CardTitle>Error</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-error-600 dark:text-error-400">
                  ✕
                </div>
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-2">
                  Red glow effect
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Section 3: Gradient Border */}
        <section className="space-y-4">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            3. Animated Gradient Border
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Gradient border reveals on hover with continuous animation
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card gradientBorder hover>
              <CardHeader>
                <CardTitle>Gradient Border</CardTitle>
                <CardDescription>Hover to reveal</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-neutral-600 dark:text-neutral-400">
                  The gradient border smoothly fades in on hover and continuously
                  animates with a shifting gradient effect.
                </p>
              </CardContent>
            </Card>

            <Card gradientBorder hover gradient>
              <CardHeader>
                <CardTitle>Combined Effects</CardTitle>
                <CardDescription>Gradient border + background</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-neutral-600 dark:text-neutral-400">
                  Combine gradient border with gradient background for
                  enhanced visual appeal.
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Section 4: Ultimate Cards */}
        <section className="space-y-4">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            4. Ultimate Cards (All Effects Combined)
          </h2>
          <p className="text-neutral-600 dark:text-neutral-400">
            Maximum visual impact with all enhancements
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card featured gradientBorder hover glowColor="primary" elevation={3}>
              <CardHeader>
                <CardTitle>Premium Plan</CardTitle>
                <CardDescription>Most Popular</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-4xl font-bold text-primary-600 dark:text-primary-400">
                    $149/mo
                  </div>
                  <ul className="space-y-2 text-sm text-neutral-600 dark:text-neutral-400">
                    <li>✓ All features included</li>
                    <li>✓ Priority support</li>
                    <li>✓ Advanced analytics</li>
                    <li>✓ Custom integrations</li>
                  </ul>
                </div>
              </CardContent>
              <CardFooter>
                <button className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-semibold">
                  Get Started
                </button>
                <span className="text-xs text-neutral-500 dark:text-neutral-400">
                  30-day guarantee
                </span>
              </CardFooter>
            </Card>

            <Card featured gradientBorder hover glowColor="success" elevation={3}>
              <CardHeader>
                <CardTitle>Enterprise</CardTitle>
                <CardDescription>For large teams</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="text-4xl font-bold text-success-600 dark:text-success-400">
                    Custom
                  </div>
                  <ul className="space-y-2 text-sm text-neutral-600 dark:text-neutral-400">
                    <li>✓ Everything in Premium</li>
                    <li>✓ Dedicated account manager</li>
                    <li>✓ SLA guarantee</li>
                    <li>✓ Custom contracts</li>
                  </ul>
                </div>
              </CardContent>
              <CardFooter>
                <button className="px-6 py-3 bg-success-600 text-white rounded-lg hover:bg-success-700 transition-colors font-semibold">
                  Contact Sales
                </button>
                <span className="text-xs text-neutral-500 dark:text-neutral-400">
                  Custom pricing
                </span>
              </CardFooter>
            </Card>
          </div>
        </section>

        {/* Section 5: Comparison Grid */}
        <section className="space-y-4">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            5. Feature Comparison
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Basic</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  No effects
                </p>
              </CardContent>
            </Card>

            <Card hover>
              <CardHeader>
                <CardTitle className="text-base">Hover</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  Enhanced hover
                </p>
              </CardContent>
            </Card>

            <Card featured hover glowColor="primary">
              <CardHeader>
                <CardTitle className="text-base">Featured</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  With glow
                </p>
              </CardContent>
            </Card>

            <Card featured gradientBorder hover glowColor="primary">
              <CardHeader>
                <CardTitle className="text-base">Ultimate</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  All effects
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Testing Instructions */}
        <section className="space-y-4 p-6 bg-neutral-100 dark:bg-neutral-800 rounded-xl">
          <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            Testing Checklist
          </h2>
          <ul className="space-y-2 text-neutral-600 dark:text-neutral-400">
            <li>✓ Hover over cards to see shadow expansion</li>
            <li>✓ Verify smooth animations (200ms easeOut)</li>
            <li>✓ Check glow effects on featured cards</li>
            <li>✓ Hover to reveal gradient borders</li>
            <li>✓ Toggle dark mode to verify theme support</li>
            <li>✓ Test on different screen sizes</li>
            <li>✓ Verify all color variants (primary, success, warning, error)</li>
            <li>✓ Check combined effects work together</li>
            <li>✓ Verify performance (60fps animations)</li>
            <li>✓ Test keyboard navigation and focus states</li>
          </ul>
        </section>
      </div>
    </div>
  );
}

export default Card2VisualTest;
