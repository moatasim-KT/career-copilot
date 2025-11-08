
import Button from '@/components/ui/Button2';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card2';

export default function DesignSystemTest() {
  return (
    <div className="p-8 space-y-8">
      <h1 className="text-4xl font-bold">Design System Test</h1>
      
      {/* Test Buttons */}
      <Card>
        <CardHeader>
          <CardTitle>Buttons</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="success">Success</Button>
            <Button loading>Loading</Button>
          </div>
        </CardContent>
      </Card>

      {/* Test Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card elevation={1} hover>
          <CardHeader>
            <CardTitle>Card 1</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Elevation 1 with hover effect</p>
          </CardContent>
        </Card>
        <Card elevation={2} gradient>
          <CardHeader>
            <CardTitle>Card 2</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Elevation 2 with gradient</p>
          </CardContent>
        </Card>
        <Card elevation={3} interactive>
          <CardHeader>
            <CardTitle>Card 3</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Elevation 3 and interactive</p>
          </CardContent>
        </Card>
      </div>

      {/* Test Colors */}
      <Card>
        <CardHeader>
          <CardTitle>Color Palette</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-4">
            <div className="space-y-2">
              <div className="h-12 bg-primary-500 rounded"></div>
              <p className="text-xs">Primary</p>
            </div>
            <div className="space-y-2">
              <div className="h-12 bg-success-500 rounded"></div>
              <p className="text-xs">Success</p>
            </div>
            <div className="space-y-2">
              <div className="h-12 bg-warning-500 rounded"></div>
              <p className="text-xs">Warning</p>
            </div>
            <div className="space-y-2">
              <div className="h-12 bg-error-500 rounded"></div>
              <p className="text-xs">Error</p>
            </div>
            <div className="space-y-2">
              <div className="h-12 bg-neutral-500 rounded"></div>
              <p className="text-xs">Neutral</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
