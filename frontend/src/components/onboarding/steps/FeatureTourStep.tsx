
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/Button';

const tourSteps = [
  {
    title: 'Discover Job Matches',
    description: 'Our AI algorithm finds the best job opportunities for you.',
    image: 'https://placehold.co/600x400?text=Job+Matches',
  },
  {
    title: 'AI-Powered Resume & Cover Letters',
    description: 'Generate tailored resumes and cover letters for each application.',
    image: 'https://placehold.co/600x400?text=AI+Resume',
  },
  {
    title: 'Track Your Applications',
    description: 'Manage all your job applications from a single dashboard.',
    image: 'https://placehold.co/600x400?text=Application+Tracking',
  },
];

const FeatureTourStep = () => {
  const [currentStep, setCurrentStep] = useState(0);

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold">Feature Tour</h2>
      <p className="mt-2 text-gray-600">
        Let's take a quick tour of the key features.
      </p>
      <div className="mt-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.3 }}
            className="text-center"
          >
            <img src={tourSteps[currentStep].image} alt={tourSteps[currentStep].title} className="mx-auto rounded-lg shadow-md" />
            <h3 className="mt-4 text-xl font-semibold">{tourSteps[currentStep].title}</h3>
            <p className="mt-2 text-gray-600">{tourSteps[currentStep].description}</p>
          </motion.div>
        </AnimatePresence>
        <div className="mt-8 flex justify-between">
          <Button onClick={handlePrev} disabled={currentStep === 0}>Previous</Button>
          <Button onClick={handleNext} disabled={currentStep === tourSteps.length - 1}>Next</Button>
        </div>
      </div>
    </div>
  );
};

export default FeatureTourStep;
