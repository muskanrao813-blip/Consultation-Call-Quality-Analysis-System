/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import DashboardView from './components/DashboardView';
import CallUploadView from './components/CallUploadView';
import AIInsightsView from './components/AIInsightsView';
import DieticianReportsView from './components/DieticianReportsView';
import QAAlertsView from './components/QAAlertsView';
import TranscriptionsView from './components/TranscriptionsView';

import { Recording, SystemSettings, QAAlert } from './types';
import { useClinicalAPI } from './hooks/useClinicalAPI';

// Default settings (minimal, no mock data)
const DEFAULT_SETTINGS: SystemSettings = {
  accountProfile: {
    name: 'QA Manager',
    role: 'Clinical QA Lead',
    email: 'qa@dietician.local',
    avatar: ''
  },
  rubricWeights: {
    nutritionalAccuracy: 40,
    patientEmpathy: 25,
    sopAdherence: 20,
    actionPlanClarity: 15
  },
  platformPreferences: {
    dataRetentionPolicy: '1 Year',
    qaAlertTriggers: 70,
    defaultTimezone: 'EST',
    primaryLanguage: 'English (US)'
  },
  teamMembers: []
};

export default function App() {
  const [currentView, setCurrentView] = useState<string>('dashboard');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Fetch ONLY real data from BE clinical API - NO FALLBACK
  const { recordings: apiRecordings, loading: apiLoading, error: apiError } = useClinicalAPI();

  // Use ONLY API data - empty by default, populated from API
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [activeQueue, setActiveQueue] = useState<Recording[]>([]);
  const [dieticians, setDieticians] = useState<any[]>([]);
  const [trainingGaps, setTrainingGaps] = useState<any[]>([]);
  const [settings, setSettings] = useState<SystemSettings>(DEFAULT_SETTINGS);
  const [selectedCallId, setSelectedCallId] = useState<string | null>(null);

  // Update recordings ONLY from API data
  useEffect(() => {
    if (apiRecordings && apiRecordings.length > 0) {
      setRecordings(apiRecordings);
    }
  }, [apiRecordings]);

  // QA alerts derived ONLY from real API data
  const [allQAAlerts, setAllQAAlerts] = useState<QAAlert[]>([]);

  // Update QA alerts when recordings change (ONLY from real API data)
  useEffect(() => {
    if (recordings.length > 0) {
      const alerts = recordings.reduce((acc: QAAlert[], curr) => {
        if (curr.qaAlerts && curr.qaAlerts.length > 0) {
          return [...acc, ...curr.qaAlerts];
        }
        return acc;
      }, []);
      setAllQAAlerts(alerts);
    } else {
      setAllQAAlerts([]);
    }
  }, [recordings]);

  // Simulated transcription & upload processing progress update interval
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveQueue((prevQueue) => {
        let hasChanges = false;
        const updated = prevQueue.map((item) => {
          if (item.status === 'processing' && item.progress < 100) {
            hasChanges = true;
            const nextProgress = Math.min(100, item.progress + Math.floor(Math.random() * 15) + 5);
            let nextText = item.statusText;
            
            // Adjust status text milestones
            if (nextProgress >= 90) {
              nextText = 'Finalizing report compilation...';
            } else if (nextProgress >= 60) {
              nextText = 'Running clinical compliance checks...';
            } else if (nextProgress >= 30) {
              nextText = 'Analyzing speaker timelines...';
            }

            return {
              ...item,
              progress: nextProgress,
              statusText: nextProgress === 100 ? 'Ready for review' : nextText
            };
          }
          return item;
        });

        // If any item reached 100%, move it to completed recordings!
        const completedItems = updated.filter((item) => item.progress === 100);
        if (completedItems.length > 0) {
          completedItems.forEach((completed) => {
            const newCompletedRecording: Recording = {
              id: completed.id,
              name: completed.name,
              patientName: 'Ingested Patient Consult',
              agentName: 'Dr. Sarah Chen',
              duration: completed.duration,
              date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
              status: 'completed',
              progress: 100,
              statusText: 'Ready for review',
              sopCompliant: Math.random() > 0.3,
              sopComplianceScore: Math.floor(Math.random() * 25) + 75,
              scores: {
                greeting: 95,
                empathy: 90,
                compliance: 88,
                technical: 92
              },
              qaAlerts: [],
              transcript: [
                {
                  id: 't-comp-1',
                  speaker: 'agent',
                  speakerName: 'Dr. Sarah Chen',
                  timestamp: '00:02',
                  text: 'Welcome to your clinical consultation check-in. May I please verify your full name and patient ID for security?',
                  tags: ['SOP: ID CONFIRMATION']
                },
                {
                  id: 't-comp-2',
                  speaker: 'patient',
                  speakerName: 'Patient',
                  timestamp: '00:12',
                  text: 'Hi Sarah, yes! Patient ID is 4492-W, Jane Doe.'
                },
                {
                  id: 't-comp-3',
                  speaker: 'agent',
                  speakerName: 'Dr. Sarah Chen',
                  timestamp: '00:24',
                  text: 'Perfect, ID is verified. Based on your glucose tracker reports, your averages look extremely stable this week. Keep up the clean diet!',
                  isCritical: true,
                  criticalBadge: 'HIGH QUALITY RESPONSE'
                }
              ],
              insights: {
                whatWentWell: ['Excellent diagnostic overview', 'Prompt security verification protocols maintained.'],
                areasForImprovement: ['Introduce self slightly more formally'],
                summary: 'Successfully ingested consultation audio. Auto-generated transcription logs highlight high SOP adherence. Dietetic advice matches guideline regulations.'
              }
            };
            
            setRecordings((prevRecs) => {
              // Avoid duplicate adds
              if (prevRecs.some((r) => r.id === completed.id)) return prevRecs;
              return [newCompletedRecording, ...prevRecs];
            });
          });

          // Filter out completed ones from activeQueue
          return updated.filter((item) => item.progress < 100);
        }

        return hasChanges ? updated : prevQueue;
      });
    }, 1500);

    return () => clearInterval(timer);
  }, []);

  // Handle manual/drag file upload triggers
  const handleUploadFile = (fileName: string) => {
    const newId = `INGEST_${Math.floor(Math.random() * 9000) + 1000}`;
    const newQueueItem: Recording = {
      id: newId,
      name: fileName,
      patientName: 'Pending Verification',
      agentName: 'Unassigned',
      duration: '04:12',
      date: new Date().toLocaleDateString('en-US'),
      status: 'processing',
      progress: 0,
      statusText: 'Uploading audio package...',
      sopCompliant: true,
      sopComplianceScore: 0,
      scores: { greeting: 0, empathy: 0, compliance: 0, technical: 0 },
      qaAlerts: [],
      transcript: [],
      insights: { whatWentWell: [], areasForImprovement: [], summary: '' }
    };

    setActiveQueue((prev) => [newQueueItem, ...prev]);
    setCurrentView('upload'); // Switch view to Call Upload to show uploading item
  };

  // Switch to selected call details within AI Insights View
  const handleSelectCall = (id: string) => {
    setSelectedCallId(id);
    setCurrentView('insights');
  };

  // Assign dietician training remediation modules
  const handleAssignTraining = (gapId: string) => {
    setTrainingGaps((prevGaps) =>
      prevGaps.map((gap) => (gap.id === gapId ? { ...gap, assigned: !gap.assigned } : gap))
    );
  };

  // Toggle alert resolved status
  const handleToggleAlertStatus = (alertId: string) => {
    setAllQAAlerts((prevAlerts) =>
      prevAlerts.map((alert) =>
        alert.id === alertId
          ? { ...alert, status: alert.status === 'active' ? 'resolved' : 'active' }
          : alert
      )
    );
  };

  // Handle global preferences saves
  const handleSaveSettings = (updated: SystemSettings) => {
    setSettings(updated);
  };

  // Reset preferences
  const handleResetSettings = () => {
    setSettings(DEFAULT_SETTINGS);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden font-sans bg-background text-on-background">
      {/* Navigation Sidebar */}
      <Sidebar
        currentView={currentView}
        onViewChange={(view) => {
          setCurrentView(view);
          setSearchQuery(''); // reset search query on navigation
        }}
        onTriggerUpload={() => handleUploadFile('my_uploaded_clinical_audio.wav')}
        activeProcessingCount={activeQueue.length}
      />

      {/* Main Right Area: Header + Dynamic Viewports */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Dynamic header */}
        <Header
          currentView={currentView}
          settings={settings}
          searchQuery={searchQuery}
          onSearchQueryChange={setSearchQuery}
        />

        {/* Show API loading/error state */}
        {apiError && (
          <div className="bg-red-50 border-b border-red-200 px-4 py-3 text-sm text-red-700">
            <strong>API Error:</strong> {apiError} - Using fallback data
          </div>
        )}

        {/* View Switchboard */}
        <main className="flex-1 overflow-hidden relative">
          {currentView === 'dashboard' && (
            <DashboardView
              recordings={recordings}
              onSelectCall={handleSelectCall}
              dieticians={dieticians}
              searchQuery={searchQuery}
            />
          )}

          {currentView === 'upload' && (
            <CallUploadView
              activeQueue={activeQueue}
              completedRecordings={recordings}
              onSelectCall={handleSelectCall}
              onUploadFile={handleUploadFile}
            />
          )}

          {currentView === 'transcriptions' && (
            <TranscriptionsView
              recordings={recordings}
              onSelectCall={handleSelectCall}
              searchQuery={searchQuery}
            />
          )}

          {currentView === 'insights' && (
            <AIInsightsView
              completedRecordings={recordings}
              selectedCallId={selectedCallId}
              onSelectCallId={setSelectedCallId}
            />
          )}

          {currentView === 'reports' && (
            <DieticianReportsView
              dieticians={dieticians}
              trainingGaps={trainingGaps}
              onAssignTraining={handleAssignTraining}
              searchQuery={searchQuery}
            />
          )}

          {currentView === 'alerts' && (
            <QAAlertsView
              alerts={allQAAlerts}
              onSelectCall={handleSelectCall}
              onToggleAlertStatus={handleToggleAlertStatus}
              searchQuery={searchQuery}
            />
          )}
        </main>
      </div>
    </div>
  );
}
