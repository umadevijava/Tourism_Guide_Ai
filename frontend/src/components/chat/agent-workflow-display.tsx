/**
 * Agent Workflow Display Component
 * Shows planning, reasoning, execution, and memory consolidation phases
 */

import React from 'react';
import { Brain, Zap, ThermometerSun, Database, Loader } from 'lucide-react';

export interface Phase {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  icon: React.ReactNode;
  results?: Record<string, unknown>;
  startTime?: Date;
  endTime?: Date;
  duration?: number;
}

export interface WorkflowState {
  goal: string;
  query: string;
  iteration: number;
  phases: Phase[];
  completed: boolean;
  error?: string;
  finalResults?: Record<string, unknown>;
}

interface AgentWorkflowDisplayProps {
  workflow: WorkflowState;
  isLoading: boolean;
}

const phaseIcons: Record<string, React.ReactNode> = {
  Planning: <Brain className="w-5 h-5" />,
  Reasoning: <ThermometerSun className="w-5 h-5" />,
  Execution: <Zap className="w-5 h-5" />,
  Memory: <Database className="w-5 h-5" />,
};

const statusColors: Record<string, string> = {
  pending: 'bg-gray-600 text-white',
  running: 'bg-blue-600 text-white animate-pulse',
  completed: 'bg-green-600 text-white',
  error: 'bg-red-600 text-white',
};

export const AgentWorkflowDisplay: React.FC<AgentWorkflowDisplayProps> = ({
  workflow,
  isLoading,
}) => {
  return (
    <div className="w-full space-y-6 p-4 bg-slate-900 rounded-lg border border-slate-700">
      {/* Header */}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <Brain className="w-5 h-5 text-blue-400" />
          Multi-Agent Workflow
        </h3>
        <p className="text-sm text-slate-400">
          Goal: {workflow.goal}
        </p>
        {workflow.iteration > 0 && (
          <p className="text-sm text-slate-400">
            Iteration: {workflow.iteration}
          </p>
        )}
      </div>

      {/* Phases Timeline */}
      <div className="space-y-3">
        {workflow.phases.map((phase, index) => (
          <div key={index} className="space-y-2">
            {/* Phase Header */}
            <div className="flex items-center gap-3 p-3 bg-slate-800 rounded border border-slate-700 hover:border-slate-600 transition">
              <div
                className={`p-2 rounded ${statusColors[phase.status]}`}
              >
                {phaseIcons[phase.name] || <Zap className="w-4 h-4" />}
              </div>
              <div className="flex-1">
                <p className="font-medium text-white">{phase.name}</p>
                <p className="text-xs text-slate-400 capitalize">
                  {phase.status}
                  {phase.duration && ` (${phase.duration}ms)`}
                </p>
              </div>
              {phase.status === 'running' && <Loader className="w-4 h-4 animate-spin text-blue-400" />}
            </div>

            {/* Phase Results */}
            {phase.results && (
              <div className="ml-10 p-3 bg-slate-800 bg-opacity-50 rounded text-sm text-slate-300 border-l-2 border-blue-500 max-h-48 overflow-y-auto">
                <PhaseResultsRenderer results={phase.results} />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Error Display */}
      {workflow.error && (
        <div className="p-4 bg-red-900 bg-opacity-20 border border-red-700 rounded text-red-300 text-sm">
          <p className="font-semibold mb-1">Error</p>
          <p>{workflow.error}</p>
        </div>
      )}

      {/* Final Results */}
      {workflow.completed && workflow.finalResults && (
        <div className="p-4 bg-green-900 bg-opacity-20 border border-green-700 rounded">
          <p className="font-semibold text-green-300 mb-2">Workflow Complete</p>
          <div className="text-sm text-slate-300">
            <p>Iterations: {workflow.iteration}</p>
            {workflow.finalResults?.memory_summary ? (
              <div className="mt-2 text-xs">
                <p className="text-slate-400">Memory Summary:</p>
                <pre className="mt-1 p-2 bg-slate-800 rounded overflow-x-auto">
                  {(() => {
                    const summary = JSON.stringify(
                      workflow.finalResults?.memory_summary,
                      null,
                      2
                    );
                    return typeof summary === 'string' ? summary : '';
                  })()}
                </pre>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="flex items-center justify-center p-4">
          <Loader className="w-6 h-6 animate-spin text-blue-400" />
          <span className="ml-2 text-slate-300">Processing...</span>
        </div>
      )}
    </div>
  );
};

/**
 * Render phase results in a readable format
 */
const PhaseResultsRenderer: React.FC<{ results: Record<string, unknown> }> = ({
  results,
}) => {
  return (
    <div className="space-y-2">
      {Object.entries(results).map(([key, value]) => (
        <div key={key}>
          <p className="font-semibold text-slate-200">{key}:</p>
          <div className="ml-2 text-slate-400">
            {renderValue(value)}
          </div>
        </div>
      ))}
    </div>
  );
};

/**
 * Recursively render values in a readable format
 */
const renderValue = (value: unknown): React.ReactNode => {
  if (typeof value === 'string') {
    return <p>{value}</p>;
  }
  if (typeof value === 'number') {
    return <p>{value}</p>;
  }
  if (typeof value === 'boolean') {
    return <p>{value ? 'true' : 'false'}</p>;
  }
  if (Array.isArray(value)) {
    return (
      <div className="space-y-1">
        {value.map((item, index) => (
          <div key={index} className="ml-2">
            {renderValue(item)}
          </div>
        ))}
      </div>
    );
  }
  if (typeof value === 'object' && value !== null) {
    return (
      <pre className="p-2 bg-slate-800 rounded text-xs overflow-x-auto mt-1">
        {JSON.stringify(value, null, 2)}
      </pre>
    );
  }
  return <p>{String(value)}</p>;
};
