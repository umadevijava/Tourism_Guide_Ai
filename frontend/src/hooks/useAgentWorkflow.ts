/**
 * Hook for managing multi-agent workflows
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import {
  AgentWorkflowWebSocket,
  AgentWorkflowUpdate,
} from '../services/agent-workflow';
import { Phase, WorkflowState } from '../components/chat/agent-workflow-display';

const initialPhases: Phase[] = [
  {
    name: 'Planning',
    status: 'pending',
    icon: '🎯',
  },
  {
    name: 'Reasoning',
    status: 'pending',
    icon: '🧠',
  },
  {
    name: 'Execution',
    status: 'pending',
    icon: '⚡',
  },
  {
    name: 'Memory',
    status: 'pending',
    icon: '💾',
  },
];

export const useAgentWorkflow = () => {
  const [workflow, setWorkflow] = useState<WorkflowState>({
    goal: '',
    query: '',
    iteration: 0,
    phases: initialPhases,
    completed: false,
  });

  const [isLoading, setIsLoading] = useState(false);
  const wsRef = useRef<AgentWorkflowWebSocket | null>(null);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, []);

  const startWorkflow = useCallback(
    async (goal: string, query: string) => {
      setIsLoading(true);
      setWorkflow({
        goal,
        query,
        iteration: 0,
        phases: initialPhases.map(p => ({ ...p, status: 'pending' })),
        completed: false,
      });

      try {
        wsRef.current = new AgentWorkflowWebSocket(
          (update) => handleWorkflowUpdate(update, goal, query),
          (error) => handleWorkflowError(error)
        );

        await wsRef.current.executeWorkflow(goal, query);
      } catch (error) {
        handleWorkflowError(
          error instanceof Error ? error.message : 'Unknown error'
        );
      }
    },
    []
  );

  const handleWorkflowUpdate = useCallback(
    (update: AgentWorkflowUpdate, goal: string, query: string) => {
      console.log('Workflow update:', update);

      switch (update.type) {
        case 'workflow_start':
          setWorkflow((prev) => ({
            ...prev,
            goal,
            query,
            iteration: update.iteration || 1,
            phases: prev.phases.map((p, idx) => ({
              ...p,
              status: idx === 0 ? 'running' : 'pending',
              startTime: idx === 0 ? new Date() : undefined,
            })),
          }));
          break;

        case 'phase_complete':
          setWorkflow((prev) => {
            const phaseIndex = prev.phases.findIndex(
              (p) => p.name === update.phase_name
            );
            if (phaseIndex === -1) return prev;

            const newPhases = [...prev.phases];
            const now = new Date();
            const startTime = newPhases[phaseIndex].startTime || now;

            newPhases[phaseIndex] = {
              ...newPhases[phaseIndex],
              status: 'completed',
              results: update.phase_results,
              endTime: now,
              duration: now.getTime() - startTime.getTime(),
            };

            // Start next phase
            if (phaseIndex + 1 < newPhases.length) {
              newPhases[phaseIndex + 1] = {
                ...newPhases[phaseIndex + 1],
                status: 'running',
                startTime: now,
              };
            }

            return {
              ...prev,
              phases: newPhases,
            };
          });
          break;

        case 'workflow_complete':
          setWorkflow((prev) => ({
            ...prev,
            completed: true,
            finalResults: update.final_results,
            phases: prev.phases.map((p) =>
              p.status === 'running'
                ? { ...p, status: 'completed', endTime: new Date() }
                : p
            ),
          }));
          setIsLoading(false);
          break;

        case 'error':
          setWorkflow((prev) => ({
            ...prev,
            error: update.message,
            completed: true,
            phases: prev.phases.map((p) =>
              p.status === 'running'
                ? { ...p, status: 'error' }
                : p
            ),
          }));
          setIsLoading(false);
          break;
      }
    },
    []
  );

  const handleWorkflowError = useCallback((error: string) => {
    console.error('Workflow error:', error);
    setWorkflow((prev) => ({
      ...prev,
      error,
      completed: true,
    }));
    setIsLoading(false);
  }, []);

  return {
    workflow,
    isLoading,
    startWorkflow,
  };
};
