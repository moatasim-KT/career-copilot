import React, { useState, useEffect } from 'react';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import { 
  TrophyIcon as AwardIcon, 
  TrophyIcon, 
  StarIcon, 
  SparklesIcon, 
  ShareIcon, 
  XMarkIcon,
  FireIcon,
  FlagIcon,
  ArrowTrendingUpIcon
} from '@heroicons/react/24/outline';
import { apiClient } from '../utils/api';

interface ProgressCelebration {
  celebration_type: string;
  title: string;
  message: string;
  achievement_data: any;
  badge_earned?: string;
  points_earned: number;
  share_message?: string;
}

interface ProgressCelebrationProps {
  onClose?: () => void;
}

const ProgressCelebrationModal: React.FC<ProgressCelebrationProps> = ({ onClose }) => {
  const [celebration, setCelebration] = useState<ProgressCelebration | null>(null);
  const [loading, setLoading] = useState(true);
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    fetchCelebration();
  }, []);

  const fetchCelebration = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/goals/celebration`);
      const data = await response.json();
      if (data) {
        setCelebration(data);
        setShowConfetti(true);
        // Hide confetti after animation
        setTimeout(() => setShowConfetti(false), 3000);
      }
    } catch (err) {
      console.error('Failed to fetch celebration:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCelebrationIcon = (type: string) => {
    switch (type) {
      case 'goal_completed':
        return <FlagIcon className="h-12 w-12 text-green-500" />;
      case 'milestone_reached':
        return <AwardIcon className="h-12 w-12 text-yellow-500" />;
      case 'streak_achieved':
        return <FireIcon className="h-12 w-12 text-orange-500" />;
      case 'improvement_made':
        return <ArrowTrendingUpIcon className="h-12 w-12 text-blue-500" />;
      default:
        return <TrophyIcon className="h-12 w-12 text-purple-500" />;
    }
  };

  const getCelebrationColor = (type: string) => {
    switch (type) {
      case 'goal_completed':
        return 'from-green-400 to-green-600';
      case 'milestone_reached':
        return 'from-yellow-400 to-yellow-600';
      case 'streak_achieved':
        return 'from-orange-400 to-orange-600';
      case 'improvement_made':
        return 'from-blue-400 to-blue-600';
      default:
        return 'from-purple-400 to-purple-600';
    }
  };

  const handleShare = () => {
    if (celebration?.share_message && navigator.share) {
      navigator.share({
        title: 'Career Achievement',
        text: celebration.share_message,
        url: window.location.origin
      });
    } else if (celebration?.share_message) {
      // Fallback to clipboard
      navigator.clipboard.writeText(celebration.share_message);
      // Could show a toast notification here
    }
  };

  const handleClose = () => {
    if (onClose) {
      onClose();
    }
  };

  if (loading) {
    return null; // Don't show anything while loading
  }

  if (!celebration) {
    return null; // No celebration to show
  }

  return (
    <>
      {/* Confetti Animation */}
      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50">
          <div className="absolute inset-0 overflow-hidden">
            {[...Array(50)].map((_, i) => (
              <div
                key={i}
                className="absolute animate-bounce"
                style={{
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  animationDelay: `${Math.random() * 2}s`,
                  animationDuration: `${2 + Math.random() * 2}s`
                }}
              >
                <SparklesIcon className="h-4 w-4 text-yellow-400" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Celebration Modal */}
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-40 p-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full overflow-hidden">
          {/* Header with gradient background */}
          <div className={`bg-gradient-to-r ${getCelebrationColor(celebration.celebration_type)} p-6 text-white relative`}>
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 text-white hover:text-gray-200 transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
            
            <div className="text-center">
              <div className="mb-4 flex justify-center">
                {getCelebrationIcon(celebration.celebration_type)}
              </div>
              <h2 className="text-2xl font-bold mb-2">{celebration.title}</h2>
              <p className="text-lg opacity-90">{celebration.message}</p>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            {/* Achievement Details */}
            <div className="text-center space-y-3">
              {celebration.badge_earned && (
                <div>
                  <Badge className="bg-yellow-100 text-yellow-800 px-3 py-1">
                    <StarIcon className="h-4 w-4 mr-1" />
                    {celebration.badge_earned.replace('_', ' ').toUpperCase()}
                  </Badge>
                </div>
              )}

              {celebration.points_earned > 0 && (
                <div className="flex items-center justify-center gap-2 text-lg font-semibold text-gray-900">
                  <TrophyIcon className="h-5 w-5 text-yellow-500" />
                  <span>+{celebration.points_earned} points earned!</span>
                </div>
              )}

              {/* Achievement Data */}
              {celebration.achievement_data && (
                <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
                  {celebration.achievement_data.milestone_type && (
                    <p className="capitalize">
                      Type: {celebration.achievement_data.milestone_type.replace('_', ' ')}
                    </p>
                  )}
                  {celebration.achievement_data.achievement_value && (
                    <p>
                      Value: {celebration.achievement_data.achievement_value}
                    </p>
                  )}
                  {celebration.achievement_data.achievement_date && (
                    <p>
                      Achieved: {new Date(celebration.achievement_data.achievement_date).toLocaleDateString()}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              {celebration.share_message && (
                <Button
                  variant="secondary"
                  onClick={handleShare}
                  className="flex-1 flex items-center justify-center gap-2"
                >
                  <ShareIcon className="h-4 w-4" />
                  Share
                </Button>
              )}
              <Button
                onClick={handleClose}
                className="flex-1"
              >
                Continue
              </Button>
            </div>

            {/* Motivational Footer */}
            <div className="text-center pt-4 border-t">
              <p className="text-sm text-gray-600">
                Keep up the great work! Every step forward counts. 🚀
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

// Hook to check for celebrations
export const useCelebrationCheck = () => {
  const [hasCelebration, setHasCelebration] = useState(false);

  const checkForCelebration = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/goals/celebration`);
      const data = await response.json();
      setHasCelebration(!!data);
    } catch (err) {
      setHasCelebration(false);
    }
  };

  useEffect(() => {
    checkForCelebration();
  }, []);

  return { hasCelebration, checkForCelebration };
};

export default ProgressCelebrationModal;