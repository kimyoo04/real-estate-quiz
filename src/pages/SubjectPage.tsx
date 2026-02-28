import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MobileLayout } from "@/components/MobileLayout";
import type { Curriculum } from "@/types";

export function SubjectPage() {
  const { examId } = useParams<{ examId: string }>();
  const [curriculum, setCurriculum] = useState<Curriculum | null>(null);
  const navigate = useNavigate();

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
              {subject.chapters.map((chapter) => (
                <Card
                  key={chapter.id}
                  className="cursor-pointer transition-colors hover:border-primary/50"
                  onClick={() =>
                    navigate(
                      `/exam/${examId}/study/${subject.id}/${chapter.id}`
                    )
                  }
                >
                  <CardHeader className="p-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-sm font-medium">
                        {chapter.name}
                      </CardTitle>
                      <Badge variant="outline" className="text-xs">
                        학습하기
                      </Badge>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>
        ))}
      </div>
    </MobileLayout>
  );
}
