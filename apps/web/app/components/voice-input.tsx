"use client";

import React, { useState, useEffect } from "react";
import { Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import toast from "react-hot-toast";

interface VoiceInputProps {
  onTranscript: (text: string) => void;
}

export function VoiceInput({ onTranscript }: VoiceInputProps) {
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState<any>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const reco = new SpeechRecognition();
        reco.continuous = false;
        reco.interimResults = false;
        reco.lang = "en-US";

        reco.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          if (transcript) {
            onTranscript(transcript);
            toast.success("Voice transcribed!");
          }
          setIsListening(false);
        };

        reco.onerror = (err: any) => {
          console.error("Speech recognition error:", err);
          setIsListening(false);
          toast.error("Voice input error");
        };

        reco.onend = () => {
          setIsListening(false);
        };

        setRecognition(reco);
      }
    }
  }, [onTranscript]);

  const toggleListening = () => {
    if (!recognition) {
      toast.error("Speech recognition is not supported in your browser.");
      return;
    }

    if (isListening) {
      recognition.stop();
      setIsListening(false);
    } else {
      recognition.start();
      setIsListening(true);
      toast("Listening... speak now", { icon: "🎙️" });
    }
  };

  return (
    <button
      type="button"
      onClick={toggleListening}
      className={`voice-btn ${isListening ? "listening" : ""}`}
      title={isListening ? "Stop listening" : "Speak prompt"}
      style={{
        background: isListening ? "#ef4444" : "#f1f5f9",
        color: isListening ? "#ffffff" : "#475569",
        border: "none",
        borderRadius: "8px",
        padding: "8px",
        cursor: "pointer",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transition: "all 0.2s ease",
      }}
    >
      {isListening ? <MicOff size={16} className="animate-pulse" /> : <Mic size={16} />}
    </button>
  );
}

export function SpeechPlayer({ text }: { text: string }) {
  const [isPlaying, setIsPlaying] = useState(false);

  const toggleSpeech = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      toast.error("Text-to-speech is not supported in your browser.");
      return;
    }

    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
    } else {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text.slice(0, 500));
      utterance.rate = 1.0;
      utterance.onend = () => setIsPlaying(false);
      utterance.onerror = () => setIsPlaying(false);

      window.speechSynthesis.speak(utterance);
      setIsPlaying(true);
    }
  };

  return (
    <button
      type="button"
      onClick={toggleSpeech}
      className="action-btn"
      title={isPlaying ? "Stop audio" : "Read aloud"}
      style={{ display: "flex", alignItems: "center", gap: 4 }}
    >
      {isPlaying ? <VolumeX size={12} style={{ color: "#ef4444" }} /> : <Volume2 size={12} />}
      <span>{isPlaying ? "Stop" : "Read Aloud"}</span>
    </button>
  );
}
