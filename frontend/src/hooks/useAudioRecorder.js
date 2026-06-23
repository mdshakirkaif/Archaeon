// OWNER: Abhay
// PURPOSE: Custom hook wrapping the MediaRecorder API
// - startRecording() → begins mic capture
// - stopRecording() → returns audio blob
// - state: idle | recording | stopped | error
// - Handles browser permission requests
//
// USED BY: AudioRecorder.jsx
