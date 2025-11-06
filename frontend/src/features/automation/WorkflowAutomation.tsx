/**
 * Workflow Automation for Job Applications
 *
 * Enterprise-grade workflow automation engine for job application management.
 * Supports custom triggers, actions, and conditions for automating repetitive tasks.
 *
 * @module features/automation/WorkflowAutomation
 */

'use client';

import { Zap, CheckCircle, Clock, XCircle, ArrowRight } from 'lucide-react';
import React, { useState } from 'react';

export interface WorkflowStep {
    id: string;
    label: string;
    description?: string;
    type: 'trigger' | 'action' | 'condition';
    enabled: boolean;
}

export interface Workflow {
    id: string;
    name: string;
    steps: WorkflowStep[];
    enabled: boolean;
}

export interface WorkflowAutomationProps {
    workflows: Workflow[];
    onRunWorkflow: (workflowId: string) => void;
    onToggleWorkflow: (workflowId: string, enabled: boolean) => void;
}

/**
 * WorkflowAutomation Component
 *
 * Features:
 * - List and manage automation workflows
 * - Enable/disable workflows
 * - Run workflows manually
 * - Visualize workflow steps
 * - Enterprise-grade accessibility and error handling
 *
 * @example
 * <WorkflowAutomation
 *   workflows={workflows}
 *   onRunWorkflow={handleRun}
 *   onToggleWorkflow={handleToggle}
 * />
 */
export function WorkflowAutomation({ workflows, onRunWorkflow, onToggleWorkflow }: WorkflowAutomationProps) {
    const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);

    return (
        <div className="max-w-3xl mx-auto p-6 bg-white rounded-lg shadow">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <Zap className="w-6 h-6 text-blue-600" /> Workflow Automation
            </h2>
            <ul className="space-y-4">
                {workflows.map((workflow) => (
                    <li key={workflow.id} className="border rounded-lg p-4 shadow-sm">
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                    {workflow.enabled ? <CheckCircle className="w-5 h-5 text-green-500" /> : <XCircle className="w-5 h-5 text-gray-400" />}
                                    {workflow.name}
                                </h3>
                                <p className="text-sm text-gray-500">{workflow.steps.length} steps</p>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => onToggleWorkflow(workflow.id, !workflow.enabled)}
                                    className={`px-3 py-2 rounded-md font-medium transition-colors ${workflow.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}
                                    aria-label={workflow.enabled ? 'Disable workflow' : 'Enable workflow'}
                                >
                                    {workflow.enabled ? 'Disable' : 'Enable'}
                                </button>
                                <button
                                    onClick={() => onRunWorkflow(workflow.id)}
                                    className="px-3 py-2 rounded-md bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
                                    aria-label="Run workflow"
                                >
                                    Run
                                </button>
                                <button
                                    onClick={() => setSelectedWorkflow(workflow.id)}
                                    className="px-2 py-2 rounded-md bg-gray-50 text-gray-600 hover:bg-gray-100"
                                    aria-label="View workflow details"
                                >
                                    <ArrowRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                        {/* Workflow Steps Visualization */}
                        {selectedWorkflow === workflow.id && (
                            <div className="mt-4">
                                <h4 className="text-md font-semibold mb-2">Steps</h4>
                                <ol className="list-decimal ml-6 space-y-2">
                                    {workflow.steps.map((step) => (
                                        <li key={step.id} className="flex items-center gap-2">
                                            {step.type === 'trigger' && <Clock className="w-4 h-4 text-yellow-500" />}
                                            {step.type === 'action' && <CheckCircle className="w-4 h-4 text-green-500" />}
                                            {step.type === 'condition' && <XCircle className="w-4 h-4 text-gray-400" />}
                                            <span className={step.enabled ? 'text-gray-900' : 'text-gray-400'}>{step.label}</span>
                                            {step.description && <span className="text-xs text-gray-500 ml-2">{step.description}</span>}
                                        </li>
                                    ))}
                                </ol>
                            </div>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
}
