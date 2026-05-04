import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Settings, LogOut, Play, Pause, Download } from 'lucide-react';
import { authService } from '../services/auth';
import PreferencesModal from '../components/PreferencesModal';
import GeneratePodcastSection from '../components/GeneratePodcastSection';
import ScheduleSettings from '../components/ScheduleSettings';
import { PodcastPreferences, Podcast } from '../types/podcast';
import {
  getPodcasts,
  downloadPodcast,
  generatePodcast,
  pollPodcastStatus,
  updateUserPreferences,
  updateScheduleSettings
} from '../services/api';

// Group podcasts by day
const groupPodcastsByDay = (podcasts: Podcast[]) => {
  const groups: { [key: string]: Podcast[] } = {};

  podcasts.forEach((podcast) => {
    const date = new Date(podcast.created_at);
    const dayKey = date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });

    if (!groups[dayKey]) {
      groups[dayKey] = [];
    }
    groups[dayKey].push(podcast);
  });

  return groups;
};

export const Home: React.FC = () => {
  const navigate = useNavigate();

  // Preferences state
  const [interests, setInterests] = useState<string[]>([]);
  const [preferences, setPreferences] = useState<PodcastPreferences>({
    length: 'medium',
    tone: 'balanced',
  });

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Podcasts state
  const [podcasts, setPodcasts] = useState<Podcast[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Audio player state
  const [playingPodcastId, setPlayingPodcastId] = useState<string | null>(null);

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);

  // Schedule settings
  const [scheduleSettings, setScheduleSettings] = useState({
    enabled: false,
    frequency: 'daily',
    time: '08:00',
    timezone: 'UTC',
    days_of_week: [1, 2, 3, 4, 5],
  });

  // Load podcasts on mount
  useEffect(() => {
    loadPodcasts();
  }, []);

  const loadPodcasts = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await getPodcasts();
      // Parse metadata for each podcast
      const parsedPodcasts = (response.podcasts || []).map((podcast: Podcast) => {
        try {
          const metadata = podcast.metadata ? JSON.parse(podcast.metadata) : {};
          return {
            ...podcast,
            interests: metadata.interests || [],
            preferences: metadata.preferences,
            duration: metadata.duration,
          };
        } catch (e) {
          return podcast;
        }
      });
      setPodcasts(parsedPodcasts);
    } catch (err) {
      console.error('Failed to load podcasts:', err);
      setError('Failed to load podcasts');
    } finally {
      setLoading(false);
    }
  };

  // Handle logout
  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  // Handle save preferences
  const handleSavePreferences = async () => {
    try {
      await updateUserPreferences({
        interests,
        duration_minutes: preferences.length === 'short' ? 5 : preferences.length === 'medium' ? 10 : 20,
      });
      console.log('Preferences saved successfully');
    } catch (err) {
      console.error('Failed to save preferences:', err);
    }
  };

  // Handle generate podcast
  const handleGeneratePodcast = async () => {
    if (interests.length === 0) {
      setError('Please add at least one interest in your preferences');
      return;
    }

    try {
      setIsGenerating(true);
      setError(null);

      const response = await generatePodcast({
        interests,
        preferences,
      });

      // Poll for status
      await pollPodcastStatus(
        response.podcastId,
        () => {
          // Status update callback
        },
        2000,
        300000
      );

      // Reload podcasts list
      await loadPodcasts();
    } catch (err) {
      console.error('Failed to generate podcast:', err);
      setError('Failed to generate podcast. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle save schedule settings
  const handleSaveScheduleSettings = async (settings: any) => {
    try {
      const response = await updateScheduleSettings(settings);
      setScheduleSettings(response.schedule_settings);
    } catch (err) {
      console.error('Failed to save schedule settings:', err);
      throw err;
    }
  };

  // Handle play/pause
  const togglePlay = (podcastId: string) => {
    if (playingPodcastId === podcastId) {
      setPlayingPodcastId(null);
    } else {
      setPlayingPodcastId(podcastId);
    }
  };

  // Handle download
  const handleDownload = async (podcastId: string) => {
    try {
      await downloadPodcast(podcastId, `podcast-${podcastId}.mp3`);
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  // Group podcasts by day
  const groupedPodcasts = groupPodcastsByDay(podcasts);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                My Podcasts
              </h1>
              <p className="text-gray-600 text-sm mt-1">
                Your personalized AI-powered podcast library
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsModalOpen(true)}
                className="
                  flex items-center gap-2 px-4 py-2 rounded-lg
                  bg-blue-600 hover:bg-blue-700 text-white
                  transition-colors duration-200 font-medium
                "
              >
                <Settings size={20} />
                <span>Preferences</span>
              </button>
              <Link
                to="/admin"
                className="
                  flex items-center gap-2 px-4 py-2 rounded-lg
                  bg-gray-100 hover:bg-gray-200 text-gray-700
                  transition-colors duration-200
                "
              >
                <Settings size={20} />
                <span>Admin</span>
              </Link>
              <button
                onClick={handleLogout}
                className="
                  flex items-center gap-2 px-4 py-2 rounded-lg
                  bg-red-100 hover:bg-red-200 text-red-700
                  transition-colors duration-200
                "
              >
                <LogOut size={20} />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Podcasts List */}
          <div className="lg:col-span-2">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">{error}</p>
              </div>
            ) : podcasts.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-600 text-lg mb-4">No podcasts yet</p>
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
                >
                  Set up your preferences to get started
                </button>
              </div>
            ) : (
          <div className="space-y-8">
            {Object.entries(groupedPodcasts).map(([day, dayPodcasts]) => (
              <div key={day}>
                {/* Day Header */}
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  {day}
                </h2>

                {/* Podcasts List */}
                <div className="space-y-3">
                  {dayPodcasts.map((podcast) => (
                    <div
                      key={podcast.id}
                      className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 flex-1">
                          {/* Play/Pause Button */}
                          {podcast.status === 'completed' && podcast.audio_url ? (
                            <button
                              onClick={() => togglePlay(podcast.id)}
                              className="
                                w-12 h-12 flex items-center justify-center
                                bg-blue-600 hover:bg-blue-700 text-white rounded-full
                                transition-colors
                              "
                            >
                              {playingPodcastId === podcast.id ? (
                                <Pause size={20} />
                              ) : (
                                <Play size={20} className="ml-1" />
                              )}
                            </button>
                          ) : (
                            <div className="w-12 h-12 flex items-center justify-center bg-gray-200 rounded-full">
                              <span className="text-xs text-gray-600">
                                {podcast.status === 'processing' ? '...' : '!'}
                              </span>
                            </div>
                          )}

                          {/* Podcast Info */}
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900">
                              {podcast.interests && podcast.interests.length > 0 ? (
                                <>
                                  {podcast.interests.slice(0, 3).join(', ')}
                                  {podcast.interests.length > 3 && ` +${podcast.interests.length - 3} more`}
                                </>
                              ) : (
                                'Podcast'
                              )}
                            </h3>
                            <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                              <span>
                                {new Date(podcast.created_at).toLocaleTimeString('en-US', {
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })}
                              </span>
                              {podcast.duration && (
                                <span>{Math.round(podcast.duration / 60)} min</span>
                              )}
                              <span className={`
                                px-2 py-0.5 rounded-full text-xs font-medium
                                ${podcast.status === 'completed'
                                  ? 'bg-green-100 text-green-800'
                                  : podcast.status === 'failed'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-blue-100 text-blue-800'
                                }
                              `}>
                                {podcast.status}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Download Button */}
                        {podcast.status === 'completed' && (
                          <button
                            onClick={() => handleDownload(podcast.id)}
                            className="
                              p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50
                              rounded-lg transition-colors
                            "
                            title="Download"
                          >
                            <Download size={20} />
                          </button>
                        )}
                      </div>

                      {/* Audio Player (for currently playing) */}
                      {playingPodcastId === podcast.id && podcast.audio_url && (
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <audio
                            src={podcast.audio_url}
                            controls
                            autoPlay
                            className="w-full"
                            onEnded={() => setPlayingPodcastId(null)}
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
            )}
          </div>

          {/* Right Column - Actions & Schedule */}
          <div className="lg:col-span-1 space-y-6">
            {/* Generate Podcast Section */}
            <GeneratePodcastSection
              onGenerate={handleGeneratePodcast}
              isGenerating={isGenerating}
              disabled={interests.length === 0}
            />

            {/* Schedule Settings */}
            <ScheduleSettings
              initialSettings={scheduleSettings}
              onSave={handleSaveScheduleSettings}
            />
          </div>
        </div>
      </main>

      {/* Preferences Modal */}
      <PreferencesModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        interests={interests}
        preferences={preferences}
        onInterestsChange={setInterests}
        onPreferencesChange={setPreferences}
        onSave={handleSavePreferences}
      />
    </div>
  );
};

export default Home;
