/**
 * Social Features Component
 * 
 * Enables users to share job search progress and connect with mentors.
 * Includes LinkedIn/Twitter sharing and mentor matching functionality.
 * 
 * @module components/social/SocialFeatures
 */

'use client';

import {
    Share2,
    Linkedin,
    Twitter,
    Users,
    MessageCircle,
    Award,
    TrendingUp,
    Copy,
    Check,
} from 'lucide-react';
import { useState } from 'react';

import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Card, { CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import apiClient from '@/lib/api/client';

interface SocialFeaturesProps {
    userId: string;
    achievements?: Achievement[];
}

interface Achievement {
    id: string;
    title: string;
    description: string;
    date: string;
    type: 'application' | 'interview' | 'offer' | 'milestone';
}

interface Mentor {
    id: string;
    name: string;
    title: string;
    company: string;
    expertise: string[];
    matchScore: number;
    imageUrl?: string;
}

/**
 * Share Dialog Component
 */
function ShareDialog({
    achievement,
    onClose,
}: {
    achievement: Achievement;
    onClose: () => void;
}) {
    const [copied, setCopied] = useState(false);

    const shareUrl = `${window.location.origin}/achievements/${achievement.id}`;
    const shareText = `🎉 ${achievement.title}\n\n${achievement.description}`;

    const handleCopyLink = () => {
        navigator.clipboard.writeText(shareUrl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleLinkedInShare = () => {
        const url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
        window.open(url, '_blank', 'width=600,height=600');
    };

    const handleTwitterShare = () => {
        const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`;
        window.open(url, '_blank', 'width=600,height=600');
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="max-w-md w-full mx-4">
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle>Share Achievement</CardTitle>
                        <button
                            onClick={onClose}
                            className="text-gray-500 hover:text-gray-700"
                        >
                            ✕
                        </button>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Achievement Preview */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex items-start gap-3">
                            <Award className="w-8 h-8 text-yellow-500" />
                            <div>
                                <h3 className="font-semibold">{achievement.title}</h3>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    {achievement.description}
                                </p>
                                <p className="text-xs text-gray-500 mt-2">{achievement.date}</p>
                            </div>
                        </div>
                    </div>

                    {/* Share Options */}
                    <div className="space-y-2">
                        <Button
                            onClick={handleLinkedInShare}
                            className="w-full flex items-center justify-center gap-2 bg-[#0077b5] hover:bg-[#006399]"
                        >
                            <Linkedin className="w-5 h-5" />
                            Share on LinkedIn
                        </Button>
                        <Button
                            onClick={handleTwitterShare}
                            className="w-full flex items-center justify-center gap-2 bg-[#1da1f2] hover:bg-[#1a91da]"
                        >
                            <Twitter className="w-5 h-5" />
                            Share on Twitter
                        </Button>
                        <Button
                            onClick={handleCopyLink}
                            variant="outline"
                            className="w-full flex items-center justify-center gap-2"
                        >
                            {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                            {copied ? 'Link Copied!' : 'Copy Link'}
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

/**
 * Mentor Card Component
 */
function MentorCard({
    mentor,
    onConnect,
}: {
    mentor: Mentor;
    onConnect: () => void;
}) {
    return (
        <Card className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
                <div className="flex items-start gap-3">
                    {/* Avatar */}
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                        {mentor.name.charAt(0)}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                        <h3 className="font-semibold truncate">{mentor.name}</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                            {mentor.title} at {mentor.company}
                        </p>

                        {/* Match Score */}
                        <div className="flex items-center gap-2 mt-2">
                            <div className="w-20 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-green-500"
                                    style={{ width: `${mentor.matchScore}%` }}
                                />
                            </div>
                            <span className="text-xs text-gray-600">
                                {mentor.matchScore}% match
                            </span>
                        </div>

                        {/* Expertise Tags */}
                        <div className="flex flex-wrap gap-1 mt-2">
                            {mentor.expertise.slice(0, 3).map((skill) => (
                                <Badge key={skill} variant="secondary" className="text-xs">
                                    {skill}
                                </Badge>
                            ))}
                            {mentor.expertise.length > 3 && (
                                <span className="text-xs text-gray-500">
                                    +{mentor.expertise.length - 3}
                                </span>
                            )}
                        </div>

                        {/* Connect Button */}
                        <Button
                            onClick={onConnect}
                            size="sm"
                            className="mt-3 w-full"
                        >
                            <Users className="w-4 h-4 mr-2" />
                            Connect
                        </Button>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

/**
 * Social Features Main Component
 * 
 * @example
 * ```tsx
 * <SocialFeatures 
 *   userId="user-123"
 *   achievements={userAchievements}
 * />
 * ```
 */
export function SocialFeatures({ userId, achievements = [] }: SocialFeaturesProps) {
    const [showShareDialog, setShowShareDialog] = useState(false);
    const [selectedAchievement, setSelectedAchievement] = useState<Achievement | null>(null);
    const [mentors, setMentors] = useState<Mentor[]>([]);
    const [loading, setLoading] = useState(false);

    // Load mentor recommendations
    const loadMentors = async () => {
        setLoading(true);
        try {
            const { data, error } = await apiClient.social.getMentors(parseInt(userId), 10);

            if (error) {
                console.error('Failed to load mentors:', error);
                return;
            }

            setMentors(data || []);
        } catch (error) {
            console.error('Failed to load mentors:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleShare = (achievement: Achievement) => {
        setSelectedAchievement(achievement);
        setShowShareDialog(true);
    };

    const handleConnect = async (mentorId: string) => {
        try {
            const { error } = await apiClient.social.createConnection(parseInt(userId), mentorId);

            if (error) {
                console.error('Failed to connect:', error);
                alert('Failed to send connection request');
                return;
            }

            // Show success notification
            alert('Connection request sent!');
        } catch (error) {
            console.error('Failed to connect:', error);
            alert('Failed to send connection request');
        }
    };

    return (
        <div className="space-y-6">
            {/* Recent Achievements */}
            {achievements.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Award className="w-5 h-5 text-yellow-500" />
                            Recent Achievements
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {achievements.slice(0, 3).map((achievement) => (
                                <div
                                    key={achievement.id}
                                    className="flex items-start justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                                >
                                    <div className="flex-1">
                                        <h4 className="font-medium">{achievement.title}</h4>
                                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                            {achievement.description}
                                        </p>
                                        <p className="text-xs text-gray-500 mt-1">{achievement.date}</p>
                                    </div>
                                    <Button
                                        onClick={() => handleShare(achievement)}
                                        variant="outline"
                                        size="sm"
                                    >
                                        <Share2 className="w-4 h-4" />
                                    </Button>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Find Mentors */}
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <Users className="w-5 h-5 text-blue-500" />
                            Find Mentors
                        </CardTitle>
                        <Button
                            onClick={loadMentors}
                            variant="outline"
                            size="sm"
                            disabled={loading}
                        >
                            <TrendingUp className="w-4 h-4 mr-2" />
                            {loading ? 'Loading...' : 'Get Recommendations'}
                        </Button>
                    </div>
                </CardHeader>
                <CardContent>
                    {mentors.length === 0 ? (
                        <div className="text-center py-8 text-gray-600 dark:text-gray-400">
                            <Users className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                            <p>Click "Get Recommendations" to find mentors</p>
                            <p className="text-sm mt-1">
                                We'll match you with professionals in your field
                            </p>
                        </div>
                    ) : (
                        <div className="grid gap-4 md:grid-cols-2">
                            {mentors.map((mentor) => (
                                <MentorCard
                                    key={mentor.id}
                                    mentor={mentor}
                                    onConnect={() => handleConnect(mentor.id)}
                                />
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Share Dialog */}
            {showShareDialog && selectedAchievement && (
                <ShareDialog
                    achievement={selectedAchievement}
                    onClose={() => setShowShareDialog(false)}
                />
            )}
        </div>
    );
}
