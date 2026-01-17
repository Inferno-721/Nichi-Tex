"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { checkHealth, type HealthResponse } from "@/lib/api";
import { Loader2 } from "lucide-react";

export function HealthBadge() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await checkHealth();
        setHealth(data);
      } catch (error) {
        setHealth(null);
      } finally {
        setLoading(false);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Badge variant="outline" className="gap-2">
        <Loader2 className="h-3 w-3 animate-spin" />
        Checking...
      </Badge>
    );
  }

  return (
    <Badge
      variant={health?.status === "healthy" ? "success" : "destructive"}
      className="gap-2"
    >
      <div
        className={`h-2 w-2 rounded-full ${
          health?.status === "healthy" ? "bg-green-500" : "bg-red-500"
        }`}
      />
      {health?.status === "healthy" ? "Backend Online" : "Backend Offline"}
    </Badge>
  );
}
