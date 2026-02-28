import { useEffect, useMemo } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { MobileLayout } from "@/components/MobileLayout";
import { useQuizStore } from "@/stores/useQuizStore";
import type { MultipleChoiceQuestion } from "@/types";

export function QuizPage() {
  const { examId, subjectId, chapterId } = useParams<{
    examId: string;
    subjectId: string;
    chapterId: string;
  }>();

  const {
    questions,
    currentIndex,
    selectedAnswer,
    showExplanation,
    setQuestions,
    goToQuestion,
    selectAnswer,
  } = useQuizStore();

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/${examId}/${subjectId}/${chapterId}_quiz.json`)
      .then((res) => res.json())
      .then(setQuestions);
  }, [examId, subjectId, chapterId, setQuestions]);

  const mcQuestions = useMemo(
    () => questions.filter((q): q is MultipleChoiceQuestion => q.type === "multiple_choice"),
    [questions]
  );

  if (mcQuestions.length === 0) {
    return (
      <MobileLayout title="기출 문제" showBack>
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      </MobileLayout>
    );
  }

  const safeIndex = Math.min(currentIndex, mcQuestions.length - 1);
  const question = mcQuestions[safeIndex];
  const isCorrect = selectedAnswer === question.correctIndex;
  const progressPercent = ((safeIndex + 1) / mcQuestions.length) * 100;

  return (
    <MobileLayout title={`기출 문제 (${safeIndex + 1}/${mcQuestions.length})`} showBack>
      <div className="space-y-4">
        <Progress value={progressPercent} className="h-2" />

        <Card>
          <CardContent className="p-5">
            <div className="mb-4 flex items-center gap-2">
              <Badge variant="outline">Q{safeIndex + 1}</Badge>
              {question.year && (
                <Badge variant="secondary" className="text-xs">
                  {question.year}년 기출
                </Badge>
              )}
            </div>

            <p className="mb-5 text-base font-medium leading-relaxed">
              {question.content}
            </p>

            <div className="space-y-2">
              {question.options.map((option, idx) => {
                let optionStyle = "border-border hover:border-primary/50";

                if (selectedAnswer !== null) {
                  if (idx === question.correctIndex) {
                    optionStyle = "border-green-500 bg-green-50 dark:bg-green-950";
                  } else if (idx === selectedAnswer && !isCorrect) {
                    optionStyle = "border-red-500 bg-red-50 dark:bg-red-950";
                  } else {
                    optionStyle = "border-border opacity-50";
                  }
                }

                return (
                  <button
                    key={idx}
                    className={`w-full rounded-lg border p-3 text-left text-sm transition-colors ${optionStyle} ${
                      selectedAnswer === null ? "cursor-pointer active:scale-[0.98]" : "cursor-default"
                    }`}
                    onClick={() => selectedAnswer === null && selectAnswer(idx)}
                    disabled={selectedAnswer !== null}
                  >
                    <span className="mr-2 font-medium text-muted-foreground">
                      {idx + 1}.
                    </span>
                    {option}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Explanation */}
        {showExplanation && (
          <Card className={isCorrect ? "border-green-200" : "border-red-200"}>
            <CardContent className="p-4">
              <div className="mb-2 flex items-center gap-2">
                <span className="text-lg">{isCorrect ? "🎉" : "😢"}</span>
                <span className="font-semibold text-sm">
                  {isCorrect ? "정답입니다!" : "오답입니다"}
                </span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {question.explanation}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Navigation */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="flex-1"
            disabled={safeIndex === 0}
            onClick={() => goToQuestion(safeIndex - 1)}
          >
            이전 문제
          </Button>
          <Button
            className="flex-1"
            disabled={safeIndex === mcQuestions.length - 1}
            onClick={() => goToQuestion(safeIndex + 1)}
          >
            다음 문제
          </Button>
        </div>
      </div>
    </MobileLayout>
  );
}
