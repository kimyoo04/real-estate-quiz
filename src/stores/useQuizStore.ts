import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Question, QuizProgress } from "@/types";

interface QuizState {
  questions: Question[];
  currentIndex: number;
  selectedAnswer: number | null;
  showExplanation: boolean;
  revealedBlanks: Record<string, boolean>;
  progress: Record<string, QuizProgress>;

  setQuestions: (questions: Question[]) => void;
  goToQuestion: (index: number) => void;
  selectAnswer: (index: number) => void;
  toggleExplanation: () => void;
  revealBlank: (questionId: string) => void;
  resetRevealedBlanks: () => void;
  saveProgress: (key: string, progress: QuizProgress) => void;
  getProgress: (key: string) => QuizProgress | undefined;
  reset: () => void;
}

export const useQuizStore = create<QuizState>()(
  persist(
    (set, get) => ({
      questions: [],
      currentIndex: 0,
      selectedAnswer: null,
      showExplanation: false,
      revealedBlanks: {},
      progress: {},

      setQuestions: (questions) =>
        set({ questions, currentIndex: 0, selectedAnswer: null, showExplanation: false, revealedBlanks: {} }),

      goToQuestion: (index) =>
        set({ currentIndex: index, selectedAnswer: null, showExplanation: false }),

      selectAnswer: (index) =>
        set({ selectedAnswer: index, showExplanation: true }),

      toggleExplanation: () =>
        set((state) => ({ showExplanation: !state.showExplanation })),

      revealBlank: (questionId) =>
        set((state) => ({
          revealedBlanks: {
            ...state.revealedBlanks,
            [questionId]: !state.revealedBlanks[questionId],
          },
        })),

      resetRevealedBlanks: () => set({ revealedBlanks: {} }),

      saveProgress: (key, progress) =>
        set((state) => ({
          progress: { ...state.progress, [key]: progress },
        })),

      getProgress: (key) => get().progress[key],

      reset: () =>
        set({
          questions: [],
          currentIndex: 0,
          selectedAnswer: null,
          showExplanation: false,
          revealedBlanks: {},
        }),
    }),
    {
      name: "certipass-quiz",
      partialize: (state) => ({ progress: state.progress }),
    }
  )
);
