import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach } from "vitest";
import { cleanup } from "@testing-library/react";
import { useQuizStore } from "@/stores/useQuizStore";

beforeEach(() => {
  useQuizStore.setState({
    questions: [],
    currentIndex: 0,
    selectedAnswer: null,
    showExplanation: false,
    revealedBlanks: {},
    wrongOnlyMode: false,
    chapterProgress: {},
  });
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
