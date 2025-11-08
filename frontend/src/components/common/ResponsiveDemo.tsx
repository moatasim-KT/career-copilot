'use client';

import { CheckCircle, Monitor, Palette, Smartphone, Tablet } from 'lucide-react';

import Button2 from '../ui/Button2';
import Card, { CardContent, CardHeader, CardTitle } from '../ui/Card';
import Container from '../ui/Container';
import Grid, { GridItem } from '../ui/Grid';

export default function ResponsiveDemo() {
  return (
    <Container size="xl" className="py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-gray-900 mb-4">
          Career Copilot
        </h1>
        <p className="text-lg md:text-xl text-gray-600 max-w-3xl mx-auto mb-8">
          Experience our responsive design that works seamlessly across all devices.
          From mobile phones to desktop computers, your job search tools are always
          accessible.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button2 size="lg" className="w-full sm:w-auto">
            Get Started
          </Button2>
          <Button2 variant="outline" size="lg" className="w-full sm:w-auto">
            Learn More
          </Button2>
        </div>
      </div>

      {/* Responsive Features Grid */}
      <Grid cols={3} gap="lg" className="mb-12">
        <GridItem>
          <Card hover className="h-full text-center">
            <CardContent className="pt-6">
              <Smartphone className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <CardTitle className="mb-2">Mobile First</CardTitle>
              <p className="text-gray-600 text-sm">
                Optimized for mobile devices with touch-friendly interfaces and
                responsive navigation.
              </p>
            </CardContent>
          </Card>
        </GridItem>

        <GridItem>
          <Card hover className="h-full text-center">
            <CardContent className="pt-6">
              <Tablet className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <CardTitle className="mb-2">Tablet Ready</CardTitle>
              <p className="text-gray-600 text-sm">
                Perfect layout adaptation for tablets with optimized spacing and
                component sizing.
              </p>
            </CardContent>
          </Card>
        </GridItem>

        <GridItem>
          <Card hover className="h-full text-center">
            <CardContent className="pt-6">
              <Monitor className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <CardTitle className="mb-2">Desktop Enhanced</CardTitle>
              <p className="text-gray-600 text-sm">
                Full desktop experience with advanced layouts and comprehensive
                navigation.
              </p>
            </CardContent>
          </Card>
        </GridItem>
      </Grid>

      {/* Design System Showcase */}
      <Card className="mb-12">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5" />
            Design System Components
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Grid cols={2} gap="lg">
            <GridItem>
              <h3 className="font-semibold mb-4">Button Variants</h3>
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <Button2 size="sm">Primary</Button2>
                  <Button2 variant="secondary" size="sm">
                    Secondary
                  </Button2>
                  <Button2 variant="outline" size="sm">
                    Outline
                  </Button2>
                  <Button2 variant="ghost" size="sm">
                    Ghost
                  </Button2>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button2>Medium</Button2>
                  <Button2 variant="secondary">Secondary</Button2>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button2 size="lg">Large Primary</Button2>
                  <Button2 variant="outline" size="lg">
                    Large Outline
                  </Button2>
                </div>
              </div>
            </GridItem>

            <GridItem>
              <h3 className="font-semibold mb-4">Responsive Grid</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="bg-blue-100 p-3 rounded text-center text-sm">
                    Item {i}
                  </div>
                ))}
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Grid adapts: 1 column on mobile, 2 on tablet, 4 on desktop
              </p>
            </GridItem>
          </Grid>
        </CardContent>
      </Card>

      {/* Features List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5" />
            Responsive Features
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Grid cols={2} gap="md">
            <GridItem>
              <ul className="space-y-3">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm">Mobile-first responsive design</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm">Flexible grid system</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm">Adaptive navigation menu</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm">Touch-friendly interfaces</span>
                </li>
              </ul>
            </GridItem>

            <GridItem>
              <ul className="space-y-3">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm">Consistent design tokens</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm">Dark mode support</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm">Accessibility compliant</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
                  <span className="text-sm">Performance optimized</span>
                </li>
              </ul>
            </GridItem>
          </Grid>
        </CardContent>
      </Card>
    </Container>
  );
}
