import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach } from "vitest";
import { cleanup } from "@testing-library/react";
import { useQuizStore } from "@/stores/use-quiz-store";
import { useMockExamStore } from "@/stores/use-mock-exam-store";

beforeEach(() => {
  useQuizStore.setState({
    questions: [],
    currentIndex: 0,
    selectedAnswer: null,
    showExplanation: false,
    revealedBlanks: {},
    wrongOnlyMode: false,
    chapterProgress: {},
    shuffleEnabled: false,
  });
  useMockExamStore.setState({
    questions: [],
    answers: {},
    currentIndex: 0,
    remainingSeconds: 50 * 60,
    isStarted: false,
    isFinished: false,
    examId: "",
    subjectId: "",
    subjectName: "",
    examHistory: [],
  });
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
