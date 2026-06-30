export const getApiUrl = (): string => {
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    // If accessing via LAN IP or custom domain, map port 8000 on the same host
    if (hostname !== "localhost" && hostname !== "127.0.0.1" && !hostname.startsWith("::")) {
      // Respect protocol (ws/http)
      return `${window.location.protocol}//${hostname}:8000/api/v1`;
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
};
