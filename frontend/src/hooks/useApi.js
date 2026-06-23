// OWNER: Shared (whoever writes it first, both use it)
// PURPOSE: Centralized fetch wrapper for all API calls
// - Base URL: import.meta.env.VITE_API_URL || "http://localhost:8000"
// - Automatically adds Content-Type headers
// - Handles errors consistently
// - Can accept FormData for audio uploads
//
// EXPORTS:
//   useApi() → { get, post, uploadAudio }
//
// EXAMPLE:
//   const api = useApi()
//   const question = await api.get(`/api/interview/${sessionId}/next-question`)
//   const answer = await api.uploadAudio(`/api/interview/${sessionId}/upload-answer`, blob)
//
// NOTE: Tansiq will swap mock URLs/endpoints for real ones when backend is live
