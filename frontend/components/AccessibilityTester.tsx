import { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent, Button } from '@/components/ui'
import { 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  PlayIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import { A11yTesting } from '@/utils/accessibility'

interface AccessibilityIssue {
  category: string
  issues: string[]
  severity: 'error' | 'warning' | 'info'
}

export function AccessibilityTester() {
  const [isRunning, setIsRunning] = useState(false)
  const [results, setResults] = useState<AccessibilityIssue[]>([])
  const [lastRunTime, setLastRunTime] = useState<Date | null>(null)

  const runTests = async () => {
    setIsRunning(true)
    
    // Simulate test running time
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    try {
      const testResults = A11yTesting.runAllChecks()
      
      // Map results to include severity
      const mappedResults: AccessibilityIssue[] = testResults.map(result => ({
        category: result.category,
        issues: result.issues,
        severity: result.issues.length > 0 ? 'error' : 'info'
      }))
      
      // Add additional custom tests
      const customTests = await runCustomTests()
      mappedResults.push(...customTests)
      
      setResults(mappedResults)
      setLastRunTime(new Date())
    } catch (error) {
      console.error('Accessibility testing failed:', error)
      setResults([{
        category: 'Test Error',
        issues: ['Failed to run accessibility tests'],
        severity: 'error'
      }])
    } finally {
      setIsRunning(false)
    }
  }

  const runCustomTests = async (): Promise<AccessibilityIssue[]> => {
    const customResults: AccessibilityIssue[] = []
    
    // Test for proper ARIA landmarks
    const landmarks = document.querySelectorAll('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], main, nav, header, footer')
    if (landmarks.length === 0) {
      customResults.push({
        category: 'ARIA Landmarks',
        issues: ['No ARIA landmarks found. Consider adding role attributes or semantic HTML elements.'],
        severity: 'warning'
      })
    }
    
    // Test for proper heading structure
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6')
    const h1Count = document.querySelectorAll('h1').length
    if (h1Count === 0) {
      customResults.push({
        category: 'Heading Structure',
        issues: ['No h1 heading found. Each page should have exactly one h1.'],
        severity: 'error'
      })
    } else if (h1Count > 1) {
      customResults.push({
        category: 'Heading Structure',
        issues: [`Multiple h1 headings found (${h1Count}). Each page should have exactly one h1.`],
        severity: 'error'
      })
    }
    
    // Test for color contrast (basic check)
    const buttons = document.querySelectorAll('button')
    let lowContrastButtons = 0
    buttons.forEach(button => {
      const styles = window.getComputedStyle(button)
      const bgColor = styles.backgroundColor
      const textColor = styles.color
      
      // This is a simplified check - in a real implementation, you'd use a proper color contrast library
      if (bgColor === 'rgb(255, 255, 255)' && textColor === 'rgb(200, 200, 200)') {
        lowContrastButtons++
      }
    })
    
    if (lowContrastButtons > 0) {
      customResults.push({
        category: 'Color Contrast',
        issues: [`${lowContrastButtons} buttons may have insufficient color contrast.`],
        severity: 'warning'
      })
    }
    
    // Test for keyboard accessibility
    const interactiveElements = document.querySelectorAll('button, a, input, select, textarea, [tabindex]')
    let elementsWithoutFocus = 0
    interactiveElements.forEach(element => {
      const tabIndex = element.getAttribute('tabindex')
      if (tabIndex === '-1' && element.tagName !== 'DIV') {
        elementsWithoutFocus++
      }
    })
    
    if (elementsWithoutFocus > 0) {
      customResults.push({
        category: 'Keyboard Navigation',
        issues: [`${elementsWithoutFocus} interactive elements may not be keyboard accessible.`],
        severity: 'warning'
      })
    }
    
    // Test for live regions
    const liveRegions = document.querySelectorAll('[aria-live]')
    if (liveRegions.length === 0) {
      customResults.push({
        category: 'Screen Reader Support',
        issues: ['No ARIA live regions found. Consider adding live regions for dynamic content updates.'],
        severity: 'info'
      })
    }
    
    return customResults
  }

  const getSeverityIcon = (severity: AccessibilityIssue['severity']) => {
    switch (severity) {
      case 'error':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
      case 'info':
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />
    }
  }

  const getSeverityColor = (severity: AccessibilityIssue['severity']) => {
    switch (severity) {
      case 'error':
        return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20'
      case 'info':
        return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20'
    }
  }

  const totalIssues = results.reduce((sum, result) => sum + result.issues.length, 0)
  const errorCount = results.filter(r => r.severity === 'error').reduce((sum, r) => sum + r.issues.length, 0)
  const warningCount = results.filter(r => r.severity === 'warning').reduce((sum, r) => sum + r.issues.length, 0)

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <DocumentTextIcon className="h-6 w-6 text-blue-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Accessibility Tester
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Run automated accessibility tests on the current page
              </p>
            </div>
          </div>
          <Button
            onClick={runTests}
            disabled={isRunning}
            loading={isRunning}
            loadingText="Running tests..."
          >
            <PlayIcon className="h-4 w-4 mr-2" />
            Run Tests
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {lastRunTime && (
          <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
            Last run: {lastRunTime.toLocaleString()}
          </div>
        )}

        {results.length > 0 && (
          <>
            {/* Summary */}
            <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {totalIssues}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Total Issues
                </div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {errorCount}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Errors
                </div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {warningCount}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Warnings
                </div>
              </div>
            </div>

            {/* Results */}
            <div className="space-y-4">
              {results.map((result, index) => (
                <div
                  key={index}
                  className={`border rounded-lg p-4 ${getSeverityColor(result.severity)}`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    {getSeverityIcon(result.severity)}
                    <h4 className="font-medium text-gray-900 dark:text-white">
                      {result.category}
                    </h4>
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      ({result.issues.length} {result.issues.length === 1 ? 'issue' : 'issues'})
                    </span>
                  </div>
                  
                  {result.issues.length > 0 ? (
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
                      {result.issues.map((issue, issueIndex) => (
                        <li key={issueIndex}>{issue}</li>
                      ))}
                    </ul>
                  ) : (
                    <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-400">
                      <CheckCircleIcon className="h-4 w-4" />
                      No issues found
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Recommendations */}
            {totalIssues > 0 && (
              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                  Recommendations
                </h4>
                <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
                  <li>• Fix all error-level issues first as they prevent users from accessing content</li>
                  <li>• Address warning-level issues to improve user experience</li>
                  <li>• Consider manual testing with keyboard navigation and screen readers</li>
                  <li>• Test with users who have disabilities for real-world feedback</li>
                </ul>
              </div>
            )}
          </>
        )}

        {results.length === 0 && !isRunning && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            Click "Run Tests" to check the current page for accessibility issues
          </div>
        )}
      </CardContent>
    </Card>
  )
}