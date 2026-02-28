import { useEffect, useMemo } from "react";
import { useParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { MobileLayout } from "@/components/MobileLayout";
import { useQuizStore } from "@/stores/useQuizStore";
import type { FillInTheBlankQuestion } from "@/types";

export function FillBlankPage() {
  const { examId, subjectId, chapterId } = useParams<{
    examId: string;
    subjectId: string;
    chapterId: string;
  }>();

  const {
    questions,
    currentIndex,
    revealedBlanks,
    setQuestions,
    goToQuestion,
    revealBlank,
  } = useQuizStore();

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/${examId}/${subjectId}/${chapterId}_quiz.json`)
      .then((res) => res.json())
      .then(setQuestions);
  }, [examId, subjectId, chapterId, setQuestions]);

  const blankQuestions = useMemo(
    () => questions.filter((q): q is FillInTheBlankQuestion => q.type === "fill_in_the_blank"),
    [questions]
  );

  if (blankQuestions.length === 0) {
    return (
      <MobileLayout title="빈칸 뚫기" showBack>
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      </MobileLayout>
    );
  }

  const safeIndex = Math.min(currentIndex, blankQuestions.length - 1);
  const question = blankQuestions[safeIndex];
  const isRevealed = !!revealedBlanks[question.id];
  const progressPercent = ((safeIndex + 1) / blankQuestions.length) * 100;

  const renderContent = (content: string, answer: string, revealed: boolean) => {
    const parts = content.split("[BLANK]");
    return (
      <span className="text-base leading-relaxed">
        {parts[0]}
        <span
          className={`inline-block min-w-[3rem] rounded-md px-2 py-0.5 text-center font-bold transition-all ${
            revealed
              ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
              : "bg-primary/10 text-primary cursor-pointer border-b-2 border-dashed border-primary"
          }`}
          onClick={() => !revealed && revealBlank(question.id)}
        >
          {revealed ? answer : "?"}
        </span>
        {parts[1]}
      </span>
    );
  };

  return (
    <MobileLayout title={`빈칸 뚫기 (${safeIndex + 1}/${blankQuestions.length})`} showBack>
      <div className="space-y-4">
        <Progress value={progressPercent} className="h-2" />

        <Card>
          <CardContent className="p-5">
            <div className="mb-4">
              <Badge variant="outline" className="mb-3">
                Q{safeIndex + 1}
              </Badge>
              <div className="mt-2">
                {renderContent(question.content, question.answer, isRevealed)}
              </div>
            </div>

            {!isRevealed && (
              <Button
                variant="outline"
                size="sm"
                className="mt-3 w-full"
                onClick={() => revealBlank(question.id)}
              >
                정답 보기
              </Button>
            )}

            {isRevealed && (
              <div className="mt-4 rounded-lg bg-muted p-3">
                <p className="text-xs font-medium text-muted-foreground mb-1">해설</p>
                <p className="text-sm">{question.explanation}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="flex-1"
            disabled={safeIndex === 0}
            onClick={() => goToQuestion(safeIndex - 1)}
          >
            이전
          </Button>
          <Button
            className="flex-1"
            disabled={safeIndex === blankQuestions.length - 1}
            onClick={() => goToQuestion(safeIndex + 1)}
          >
            다음
          </Button>
        </div>
      </div>
    </MobileLayout>
  );
}
