export interface Exam {
  id: string;
  name: string;
  description: string;
  isActive: boolean;
}

export interface Chapter {
  id: string;
  name: string;
}

export interface Subject {
  id: string;
  name: string;
  chapters: Chapter[];
}

export interface Curriculum {
  examId: string;
  subjects: Subject[];
}

export interface FillInTheBlankQuestion {
  id: string;
  type: "fill_in_the_blank";
  content: string;
  answer: string;
  explanation: string;
}

export interface MultipleChoiceQuestion {
  id: string;
  type: "multiple_choice";
  year: number;
  content: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

export type Question = FillInTheBlankQuestion | MultipleChoiceQuestion;

export interface QuizProgress {
  examId: string;
  subjectId: string;
  chapterId: string;
  currentIndex: number;
  answers: Record<string, number | string>;
  wrongIds: string[];
}
