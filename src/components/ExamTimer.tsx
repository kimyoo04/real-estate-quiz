import { useEffect } from "react";
import { useMockExamStore } from "@/stores/useMockExamStore";

export function ExamTimer() {
  const remainingSeconds = useMockExamStore((s) => s.remainingSeconds);
  const isStarted = useMockExamStore((s) => s.isStarted);
  const tick = useMockExamStore((s) => s.tick);

  useEffect(() => {
    if (!isStarted) return;
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [isStarted, tick]);

  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;
  const isLow = remainingSeconds < 300; // less than 5 minutes

  return (
    <span
      className={`font-mono text-sm font-medium tabular-nums ${
        isLow ? "text-red-600 animate-pulse" : "text-muted-foreground"
      }`}
    >
      {String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
    </span>
  );
}
