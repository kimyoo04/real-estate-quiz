import { useEffect, useMemo, useCallback, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useSwipe } from "@/hooks/use-swipe";
import { Progress } from "@/components/ui/progress";
import { MobileLayout } from "@/components/mobile-layout";
import { useQuizStore } from "@/stores/use-quiz-store";
import { useQuestionEditStore } from "@/stores/use-question-edit-store";
import type { MultipleChoiceQuestion, Question } from "@/types";
import { fisherYatesShuffle } from "@/utils/shuffle";
import { PencilIcon } from "lucide-react";
import { QuestionEditDialog } from "@/components/question-edit-dialog";

export function QuizPage() {
  const { examId, subjectId, chapterId } = useParams<{
    examId: string;
    subjectId: string;
    chapterId: string;
  }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const wrongOnly = searchParams.get("mode") === "wrong";

  const {
    questions,
    currentIndex,
    selectedAnswer,
    showExplanation,
    chapterProgress,
    shuffleEnabled,
    setQuestions,
    goToQuestion,
    selectAnswer,
    recordMcAnswer,
  } = useQuizStore();

  const getEditedQuestion = useQuestionEditStore((s) => s.getEditedQuestion);
  const [editTarget, setEditTarget] = useState<Question | null>(null);

  const chapterKey = `${examId}/${subjectId}/${chapterId}`;

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/${examId}/${subjectId}/${chapterId}_quiz.json`)
      .then((res) => res.json())
      .then(setQuestions);
  }, [examId, subjectId, chapterId, setQuestions]);

  const mcQuestions = useMemo(() => {
    let all = questions
      .filter(
        (q): q is MultipleChoiceQuestion => q.type === "multiple_choice"
      )
      .map((q) => getEditedQuestion(q));
    if (wrongOnly) {
      const wrongIds = chapterProgress[chapterKey]?.wrongIds ?? [];
      all = all.filter((q) => wrongIds.includes(q.id));
    }
    if (shuffleEnabled) {
      return fisherYatesShuffle(all, chapterKey);
    }
    return all;
  }, [questions, wrongOnly, chapterProgress, chapterKey, shuffleEnabled, getEditedQuestion]);

  const handleSelect = useCallback(
    (idx: number) => {
      if (selectedAnswer !== null) return;
      selectAnswer(idx);
      const question = mcQuestions[Math.min(currentIndex, mcQuestions.length - 1)];
      const correct = idx === question.correctIndex;
      recordMcAnswer(chapterKey, question.id, correct, mcQuestions.length);
    },
    [selectedAnswer, selectAnswer, mcQuestions, currentIndex, recordMcAnswer, chapterKey]
  );

  const safeIndex = Math.min(currentIndex, Math.max(mcQuestions.length - 1, 0));
  const isLast = safeIndex === mcQuestions.length - 1;

  const swipeHandlers = useSwipe({
    onSwipeLeft: () => !isLast && goToQuestion(safeIndex + 1),
    onSwipeRight: () => safeIndex > 0 && goToQuestion(safeIndex - 1),
  });

  if (mcQuestions.length === 0) {
    const isLoading = questions.length === 0;
    return (
      <MobileLayout title={wrongOnly ? "오답 풀기" : "기출 문제"} showBack>
        <div className="flex flex-col items-center justify-center py-20 text-center">
          {isLoading ? (
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          ) : (
            <>
              <p className="text-4xl mb-3">🎉</p>
              <p className="font-semibold mb-1">오답이 없습니다!</p>
              <p className="text-sm text-muted-foreground mb-4">
                모든 문제를 맞혔습니다
              </p>
              <Button onClick={() => navigate(-1)}>돌아가기</Button>
            </>
          )}
        </div>
      </MobileLayout>
    );
  }

  const question = mcQuestions[safeIndex];
  const isCorrect = selectedAnswer === question.correctIndex;
  const progressPercent = ((safeIndex + 1) / mcQuestions.length) * 100;

  return (
    <MobileLayout
      title={`${wrongOnly ? "오답 풀기" : "기출 문제"} (${safeIndex + 1}/${mcQuestions.length})`}
      showBack
    >
      <div className="space-y-4" {...swipeHandlers}>
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
              {wrongOnly && (
                <Badge variant="destructive" className="text-xs">
                  오답 복습
                </Badge>
              )}
              {import.meta.env.DEV && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="ml-auto h-7 w-7 p-0"
                  onClick={() => setEditTarget(question)}
                >
                  <PencilIcon className="h-3.5 w-3.5" />
                </Button>
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
                      selectedAnswer === null
                        ? "cursor-pointer active:scale-[0.98]"
                        : "cursor-default"
                    }`}
                    onClick={() => handleSelect(idx)}
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

        {showExplanation && (
          <Card className={isCorrect ? "border-green-200" : "border-red-200"}>
            <CardContent className="p-4">
              <div className="mb-2 flex items-center gap-2">
                <span className="text-lg">{isCorrect ? "🎉" : "😢"}</span>
                <span className="font-semibold text-sm">
                  {isCorrect ? "정답입니다!" : "오답입니다"}
                </span>
              </div>
              <p className={`text-sm leading-relaxed ${question.explanation ? "text-muted-foreground" : "italic text-muted-foreground/60"}`}>
                {question.explanation || "해설이 아직 준비되지 않았습니다."}
              </p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3 w-full gap-1 text-xs"
                onClick={() => navigate(`/exam/${examId}/tree/${subjectId}`)}
              >
                📚 관련 개념 보기
              </Button>
            </CardContent>
          </Card>
        )}

        <div className="flex gap-2">
          <Button
            variant="outline"
            className="flex-1"
            disabled={safeIndex === 0}
            onClick={() => goToQuestion(safeIndex - 1)}
          >
            이전 문제
          </Button>
          {isLast && showExplanation ? (
            <Button
              className="flex-1"
              onClick={() =>
                navigate(
                  `/exam/${examId}/study/${subjectId}/${chapterId}/result?mode=${wrongOnly ? "wrong" : "quiz"}`
                )
              }
            >
              결과 보기
            </Button>
          ) : (
            <Button
              className="flex-1"
              disabled={isLast}
              onClick={() => goToQuestion(safeIndex + 1)}
            >
              다음 문제
            </Button>
          )}
        </div>
      </div>

      {import.meta.env.DEV && editTarget && (
        <QuestionEditDialog
          question={editTarget}
          open={!!editTarget}
          onOpenChange={(open) => !open && setEditTarget(null)}
        />
      )}
    </MobileLayout>
  );
}
