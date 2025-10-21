import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import GoalsDashboard from '../components/GoalsDashboard';
import CreateGoalModal from '../components/CreateGoalModal';
import ProgressCelebrationModal, { useCelebrationCheck } from '../components/ProgressCelebration';

const GoalsPage: React.FC = () => {
  const [showCreateGoal, setShowCreateGoal] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const { hasCelebration, checkForCelebration } = useCelebrationCheck();

  useEffect(() => {
    if (hasCelebration) {
      setShowCelebration(true);
    }
  }, [hasCelebration]);

  const handleGoalCreated = () => {
    setShowCreateGoal(false);
    // Refresh the dashboard data
    window.location.reload();
  };

  const handleCelebrationClose = () => {
    setShowCelebration(false);
    checkForCelebration(); // Check for more celebrations
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <GoalsDashboard />
        
        {/* Create Goal Modal */}
        <CreateGoalModal
          isOpen={showCreateGoal}
          onClose={() => setShowCreateGoal(false)}
          onGoalCreated={handleGoalCreated}
        />

        {/* Progress Celebration Modal */}
        {showCelebration && (
          <ProgressCelebrationModal
            onClose={handleCelebrationClose}
          />
        )}
      </div>
    </Layout>
  );
};

export default GoalsPage;