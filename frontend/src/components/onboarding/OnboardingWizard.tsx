
import React, { useState, useReducer, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { ProgressBar } from '@/components/ui/ProgressBar';
import WelcomeStep from './steps/WelcomeStep';
import SkillsStep from './steps/SkillsStep';
import ResumeStep from './steps/ResumeStep';
import PreferencesStep from './steps/PreferencesStep';
import FeatureTourStep from './steps/FeatureTourStep';
import CompletionStep from './steps/CompletionStep';
import apiClient from '@/lib/api/client';

const steps = [
  { id: 'welcome', component: WelcomeStep },
  { id: 'skills', component: SkillsStep },
  { id: 'resume', component: ResumeStep },
  { id: 'preferences', component: PreferencesStep },
  { id: 'tour', component: FeatureTourStep },
  { id: 'completion', component: CompletionStep },
];

type State = {
  [key: string]: any;
};

type Action = {
  type: 'UPDATE_STEP' | 'SET_STATE';
  payload: any;
};

const initialState: State = {};

function onboardingReducer(state: State, action: Action): State {
  switch (action.type) {
    case 'UPDATE_STEP':
      return {
        ...state,
        [action.payload.step]: {
          ...state[action.payload.step],
          ...action.payload.data,
        },
      };
    case 'SET_STATE':
        return action.payload;
    default:
      return state;
  }
}

const OnboardingWizard = ({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [state, dispatch] = useReducer(onboardingReducer, initialState);

  useEffect(() => {
    const fetchProfile = async () => {
      const response = await apiClient.user.getProfile();
      if (response.data) {
        dispatch({ type: 'SET_STATE', payload: response.data.onboarding || {} });
        const lastCompletedStep = steps.findIndex(step => !response.data.onboarding?.[step.id]?.completed);
        if (lastCompletedStep !== -1) {
            setCurrentStep(lastCompletedStep);
        }
      }
    };
    fetchProfile();
  }, []);

  const handleNext = async () => {
    if (currentStep < steps.length - 1) {
      await apiClient.user.updateProfile({
        onboarding: { ...state, [steps[currentStep].id]: { ...state[steps[currentStep].id], completed: true } },
      });
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    if (currentStep < steps.length - 2) {
        setCurrentStep(currentStep + 1);
    } else {
        onClose();
    }
  };

  const handleStepChange = (data: any) => {
    dispatch({
      type: 'UPDATE_STEP',
      payload: { step: steps[currentStep].id, data },
    });
  };

  const CurrentStepComponent = steps[currentStep].component;

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="p-8">
        <ProgressBar value={(currentStep + 1) / steps.length * 100} />
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
          >
            <CurrentStepComponent
              data={state[steps[currentStep].id] || {}}
              onChange={handleStepChange}
            />
          </motion.div>
        </AnimatePresence>
        <div className="mt-8 flex justify-between">
          {currentStep > 0 && <Button onClick={handleBack}>Back</Button>}
          {currentStep < steps.length - 1 && (
            <Button onClick={handleNext}>Next</Button>
          )}
          {currentStep < steps.length - 2 && (
            <Button onClick={handleSkip} variant="ghost">
              Skip
            </Button>
          )}
          {currentStep === steps.length - 1 && (
            <Button onClick={onClose}>Finish</Button>
          )}
        </div>
      </div>
    </Modal>
  );
};

export default OnboardingWizard;
