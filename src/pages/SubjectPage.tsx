import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { MobileLayout } from "@/components/MobileLayout";
import { useQuizStore } from "@/stores/useQuizStore";
import type { Curriculum } from "@/types";

export function SubjectPage() {
  const { examId } = useParams<{ examId: string }>();
  const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
  const navigate = useNavigate();
  const chapterProgress = useQuizStore((s) => s.chapterProgress);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/${examId}/curriculum.json`)
      .then((res) => res.json())
      .then(setCurriculum);
  }, [examId]);

  if (!curriculum) {
    return (
      <MobileLayout title="로딩 중..." showBack>
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      </MobileLayout>
    );
  }

  return (
    <MobileLayout title="과목 선택" showBack>
      <div className="space-y-4">
        {curriculum.subjects.map((subject) => (
          <div key={subject.id}>
            <h2 className="mb-2 text-base font-semibold">{subject.name}</h2>
            <div className="space-y-2">
              {subject.chapters.map((chapter) => {
                const key = `${examId}/${subject.id}/${chapter.id}`;
                const prog = chapterProgress[key];
                const answered = prog ? prog.correctIds.length + prog.wrongIds.length : 0;
                const total = prog?.totalMc ?? 0;
                const percent = total > 0 ? Math.round((answered / total) * 100) : 0;
                const wrongCount = prog?.wrongIds.length ?? 0;

                return (
                  <Card
                    key={chapter.id}
                    className="cursor-pointer transition-colors hover:border-primary/50"
                    onClick={() =>
                      navigate(`/exam/${examId}/study/${subject.id}/${chapter.id}`)
                    }
                  >
                    <CardHeader className="p-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm font-medium">
                          {chapter.name}
                        </CardTitle>
                        <div className="flex items-center gap-1.5">
                          {wrongCount > 0 && (
                            <Badge variant="destructive" className="text-xs">
                              오답 {wrongCount}
                            </Badge>
                          )}
                          {total > 0 ? (
                            <Badge
                              variant={percent === 100 ? "default" : "outline"}
                              className="text-xs"
                            >
                              {percent}%
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs">
                              학습하기
                            </Badge>
                          )}
                        </div>
                      </div>
                      {total > 0 && (
                        <Progress value={percent} className="mt-2 h-1.5" />
                      )}
                    </CardHeader>
                  </Card>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </MobileLayout>
  );
}
