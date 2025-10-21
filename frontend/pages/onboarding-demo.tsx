import React, { useState } from 'react'
import { Layout } from '@/components/Layout'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { 
  TutorialOverlay,
  FeatureHighlight,
  FeedbackModal,
  HelpCenter
} from '@/components'
import { 
  AcademicCapIcon,
  LightBulbIcon,
  ChatBubbleLeftRightIcon,
  QuestionMarkCircleIcon,
  BriefcaseIcon,
  ChartBarIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'

// Mock tutorial data
const mockTutorial = {
  id: "demo-tutorial",
  title: "Demo Tutorial",
  description: "A demonstration of the tutorial system",
  category: "demo",
  difficulty: "beginner" as const,
  estimated_time: 5,
  prerequisites: [],
  steps: [
    {
      id: "step-1",
      title: "Welcome to the Demo",
      description: "This is the first step of our demo tutorial",
      target_element: "[data-testid='demo-card-1']",
      position: "bottom" as const,
      content: "This card demonstrates how tutorials can highlight specific elements on the page and provide contextual guidance.",
      action_required: false
    },
    {
      id: "step-2", 
      title: "Interactive Elements",
      description: "Learn about interactive tutorial steps",
      target_element: "[data-testid='demo-button']",
      position: "top" as const,
      content: "Some tutorial steps require user interaction. Try clicking this button to proceed!",
      action_required: true,
      action_text: "Click the Demo Button"
    },
    {
      id: "step-3",
      title: "Tutorial Complete",
      description: "You've completed the demo tutorial",
      position: "center" as const,
      content: "Congratulations! You've successfully completed the demo tutorial. This shows how tutorials can guide users through complex workflows step by step.",
      action_required: false
    }
  ],
  is_required: false
}

// Mock feature highlight data
const mockFeatureHighlight = {
  id: "demo-feature",
  title: "New Feature Available!",
  description: "Check out this amazing new feature that will help improve your workflow.",
  target_element: "[data-testid='demo-card-2']",
  position: "left" as const,
  priority: 1,
  show_once: true
}

export default function OnboardingDemo() {
  const [showTutorial, setShowTutorial] = useState(false)
  const [showFeatureHighlight, setShowFeatureHighlight] = useState(false)
  const [showFeedbackModal, setShowFeedbackModal] = useState(false)
  const [showHelpCenter, setShowHelpCenter] = useState(false)
  const [demoButtonClicked, setDemoButtonClicked] = useState(false)

  const handleTutorialComplete = (tutorialId: string) => {
    console.log(`Tutorial completed: ${tutorialId}`)
    setShowTutorial(false)
  }

  const handleStepComplete = (stepId: string) => {
    console.log(`Step completed: ${stepId}`)
  }

  const handleFeatureDiscover = (featureId: string) => {
    console.log(`Feature discovered: ${featureId}`)
    setShowFeatureHighlight(false)
  }

  const handleFeatureDismiss = (featureId: string) => {
    console.log(`Feature dismissed: ${featureId}`)
    setShowFeatureHighlight(false)
  }

  const handleFeedbackSubmit = async (feedbackData: any) => {
    console.log('Feedback submitted:', feedbackData)
    // In a real app, this would submit to the API
    alert('Feedback submitted successfully! (Demo mode)')
  }

  return (
    <Layout 
      title="Onboarding System Demo"
      description="Demonstration of the comprehensive help and onboarding system"
    >
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Onboarding System Demo
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Experience the comprehensive help and onboarding system with interactive tutorials, 
            feature highlights, contextual help, and feedback collection.
          </p>
        </div>

        {/* Demo Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AcademicCapIcon className="h-6 w-6 mr-2" />
              Demo Controls
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Button
                onClick={() => setShowTutorial(true)}
                className="flex flex-col items-center p-4 h-auto"
              >
                <AcademicCapIcon className="h-8 w-8 mb-2" />
                Start Tutorial
              </Button>
              
              <Button
                variant="secondary"
                onClick={() => setShowFeatureHighlight(true)}
                className="flex flex-col items-center p-4 h-auto"
              >
                <LightBulbIcon className="h-8 w-8 mb-2" />
                Show Feature Highlight
              </Button>
              
              <Button
                variant="ghost"
                onClick={() => setShowHelpCenter(true)}
                className="flex flex-col items-center p-4 h-auto"
              >
                <QuestionMarkCircleIcon className="h-8 w-8 mb-2" />
                Open Help Center
              </Button>
              
              <Button
                variant="ghost"
                onClick={() => setShowFeedbackModal(true)}
                className="flex flex-col items-center p-4 h-auto"
              >
                <ChatBubbleLeftRightIcon className="h-8 w-8 mb-2" />
                Send Feedback
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Demo Content */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card data-testid="demo-card-1" className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6 text-center">
              <div className="mx-auto h-12 w-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center mb-4">
                <BriefcaseIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Job Management
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                This card will be highlighted during the tutorial to demonstrate contextual guidance.
              </p>
              <Badge variant="secondary">Tutorial Target</Badge>
            </CardContent>
          </Card>

          <Card data-testid="demo-card-2" className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6 text-center">
              <div className="mx-auto h-12 w-12 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg flex items-center justify-center mb-4">
                <LightBulbIcon className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Feature Discovery
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                This card will show a feature highlight when you click the demo button.
              </p>
              <Badge variant="outline">Feature Highlight Target</Badge>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardContent className="p-6 text-center">
              <div className="mx-auto h-12 w-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center mb-4">
                <ChartBarIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Analytics
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                This card demonstrates the overall system design and layout.
              </p>
              <Badge variant="secondary">Demo Content</Badge>
            </CardContent>
          </Card>
        </div>

        {/* Interactive Demo Section */}
        <Card>
          <CardHeader>
            <CardTitle>Interactive Demo Section</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-gray-600 dark:text-gray-400">
              This section contains interactive elements that are referenced in the tutorial.
            </p>
            
            <div className="flex items-center space-x-4">
              <Button
                data-testid="demo-button"
                onClick={() => setDemoButtonClicked(true)}
                variant={demoButtonClicked ? "primary" : "secondary"}
              >
                {demoButtonClicked ? "✓ Demo Button Clicked!" : "Demo Button"}
              </Button>
              
              {demoButtonClicked && (
                <Badge variant="secondary">
                  Great! This action would be tracked in a real tutorial.
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Features Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Onboarding System Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                  Interactive Tutorials
                </h4>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li>• Step-by-step guided walkthroughs</li>
                  <li>• Element highlighting and positioning</li>
                  <li>• Action-required steps with validation</li>
                  <li>• Progress tracking and completion</li>
                  <li>• Responsive design for all devices</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                  Feature Discovery
                </h4>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li>• Contextual feature highlights</li>
                  <li>• Priority-based display system</li>
                  <li>• Condition-based triggering</li>
                  <li>• User preference controls</li>
                  <li>• Analytics and tracking</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                  Help Center
                </h4>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li>• Searchable knowledge base</li>
                  <li>• Categorized help articles</li>
                  <li>• Popular and trending content</li>
                  <li>• User voting and feedback</li>
                  <li>• Mobile-responsive design</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                  Feedback System
                </h4>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                  <li>• Multiple feedback types</li>
                  <li>• Context capture and metadata</li>
                  <li>• Priority classification</li>
                  <li>• User voting and engagement</li>
                  <li>• Admin response system</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tutorial Overlay */}
      <TutorialOverlay
        tutorial={mockTutorial}
        isOpen={showTutorial}
        onClose={() => setShowTutorial(false)}
        onComplete={handleTutorialComplete}
        onStepComplete={handleStepComplete}
      />

      {/* Feature Highlight */}
      <FeatureHighlight
        highlight={mockFeatureHighlight}
        isVisible={showFeatureHighlight}
        onDismiss={handleFeatureDismiss}
        onDiscover={handleFeatureDiscover}
      />

      {/* Help Center Modal */}
      <HelpCenter
        isOpen={showHelpCenter}
        onClose={() => setShowHelpCenter(false)}
      />

      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => setShowFeedbackModal(false)}
        onSubmit={handleFeedbackSubmit}
      />
    </Layout>
  )
}