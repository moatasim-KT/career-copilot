
'use client';

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Video, VideoOff, Send, Loader, AlertCircle } from 'lucide-react';

export default function InterviewPractice() {
  const [isAudioEnabled, setIsAudioEnabled] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [messages, setMessages] = useState<any[]>([]);
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    // Clean up media streams on component unmount
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const setupMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: isVideoEnabled, 
        audio: isAudioEnabled 
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      setError('Could not access camera or microphone. Please check permissions.');
    }
  };

  const handleToggleAudio = () => {
    setIsAudioEnabled(!isAudioEnabled);
    setupMedia();
  };

  const handleToggleVideo = () => {
    setIsVideoEnabled(!isVideoEnabled);
    setupMedia();
  };

  const handleStartRecording = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      mediaRecorderRef.current = new MediaRecorder(stream);
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(recordedChunksRef.current, {
          type: 'video/webm'
        });
        // Here you would send the blob to the backend
        console.log('Recording stopped, blob created:', blob);
        recordedChunksRef.current = [];
      };
      mediaRecorderRef.current.start();
      setIsRecording(true);
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle sending text message
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">AI Interview Practice</h3>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 m-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
          {/* Video Feed */}
          <div className="bg-gray-900 rounded-lg overflow-hidden aspect-video">
            <video ref={videoRef} autoPlay muted className="w-full h-full object-cover"></video>
          </div>

          {/* Chat/Transcript */}
          <div className="flex flex-col bg-gray-50 rounded-lg border">
            <div className="flex-1 p-4 space-y-4 overflow-y-auto">
              {messages.map((msg, index) => (
                <div key={index} className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}>
                  <div className={`px-4 py-2 rounded-lg ${msg.isUser ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-center">
                  <Loader className="animate-spin h-6 w-6 text-blue-500" />
                </div>
              )}
            </div>
            <form onSubmit={handleSendMessage} className="p-4 border-t flex items-center">
              <input type="text" placeholder="Type your answer..." className="flex-1 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
              <button type="submit" className="ml-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                <Send className="h-5 w-5" />
              </button>
            </form>
          </div>
        </div>

        {/* Controls */}
        <div className="p-4 border-t flex justify-center items-center space-x-4">
          <button onClick={handleToggleAudio} className={`p-3 rounded-full ${isAudioEnabled ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'}`}>
            {isAudioEnabled ? <Mic className="h-6 w-6" /> : <MicOff className="h-6 w-6" />}
          </button>
          <button onClick={handleToggleVideo} className={`p-3 rounded-full ${isVideoEnabled ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'}`}>
            {isVideoEnabled ? <Video className="h-6 w-6" /> : <VideoOff className="h-6 w-6" />}
          </button>
          {!isRecording ? (
            <button onClick={handleStartRecording} disabled={!isAudioEnabled && !isVideoEnabled} className="px-6 py-3 bg-green-500 text-white rounded-full font-semibold disabled:opacity-50">
              Start Practice
            </button>
          ) : (
            <button onClick={handleStopRecording} className="px-6 py-3 bg-red-500 text-white rounded-full font-semibold">
              End Practice
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
