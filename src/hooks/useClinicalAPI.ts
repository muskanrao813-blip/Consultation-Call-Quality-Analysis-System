import { useState, useEffect } from 'react';
import { Recording } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useClinicalAPI() {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecordings = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`${API_BASE_URL}/api/clinical/calls`);
        if (!response.ok) {
          throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        // Transform BE response to match FE Recording type if needed
        const transformed = Array.isArray(data) ? data : [data];
        setRecordings(transformed);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error';
        setError(message);
        console.error('Failed to fetch recordings:', err);
        // Fallback to empty array instead of crashing
        setRecordings([]);
      } finally {
        setLoading(false);
      }
    };

    fetchRecordings();

    // Optional: Refresh every 30 seconds for real-time updates
    const interval = setInterval(fetchRecordings, 30000);
    return () => clearInterval(interval);
  }, []);

  return { recordings, loading, error };
}

export async function fetchCallDetail(callId: string): Promise<Recording | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/clinical/calls/${callId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch call: ${response.status}`);
    }
    return await response.json();
  } catch (err) {
    console.error('Failed to fetch call detail:', err);
    return null;
  }
}

export async function fetchDashboardStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/clinical/dashboard/stats`);
    if (!response.ok) {
      throw new Error(`Failed to fetch stats: ${response.status}`);
    }
    return await response.json();
  } catch (err) {
    console.error('Failed to fetch dashboard stats:', err);
    return null;
  }
}
