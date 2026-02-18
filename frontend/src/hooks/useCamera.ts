// useCamera.ts (Final & Best Version)
import { useState, useRef, useCallback, useEffect } from "react";

export const useCamera = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null); // Use a ref to hold the stream

  // State is used to let the component know if the stream is active
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCamera = useCallback(async () => {
    // Stop any existing stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    setError(null);

    try {
      const constraints = {
        video: {
          facingMode: "environment",
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      };
      const newStream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = newStream; // Store in the ref

      if (videoRef.current) {
        videoRef.current.srcObject = newStream;
      }
      setIsStreaming(true); // Update state to trigger re-render
    } catch (err) {
      console.error("Camera access error:", err);
      // ... (error handling code is the same as before) ...
      if (err instanceof DOMException) {
         if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
            setError("Camera permission was denied. Please allow camera access in your browser settings.");
         } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
            setError("No camera found. Please ensure a camera is connected and enabled.");
         } else {
            setError("Could not start camera. Please check your device and permissions.");
         }
      } else {
        setError("An unexpected error occurred while accessing the camera.");
      }
      streamRef.current = null;
      setIsStreaming(false);
    }
  }, []); // Now has an empty, stable dependency array

const stopCamera = useCallback(() => {
  if (streamRef.current) {
    streamRef.current.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }
  if (videoRef.current) {
    videoRef.current.srcObject = null; // important!
  }
  setIsStreaming(false);
  console.log("Camera stopped and video cleared");
}, []);


  const capturePhoto = useCallback((): Promise<File | null> => {
    return new Promise((resolve, reject) => {
      if (videoRef.current && canvasRef.current && streamRef.current) {
        // ... (capture logic is the same, just use streamRef.current) ...
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const context = canvas.getContext("2d");

        if (context) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          context.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);
          
          canvas.toBlob((blob) => {
            if (blob) {
              const fileName = `reading-${Date.now()}.jpeg`;
              const file = new File([blob], fileName, { type: "image/jpeg" });
              resolve(file);
            } else {
              reject(new Error("Could not create blob from canvas."));
            }
          }, "image/jpeg", 0.95);
        } else {
          reject(new Error("Could not get 2D context from canvas."));
        }
      } else {
        resolve(null);
      }
    });
  }, []); // Also stable!

  // Cleanup effect runs only once on mount and unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return { videoRef, canvasRef, stream: streamRef.current, isStreaming, error, startCamera, stopCamera, capturePhoto };
};