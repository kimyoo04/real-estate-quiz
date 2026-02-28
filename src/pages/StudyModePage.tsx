import { useParams, useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { MobileLayout } from "@/components/MobileLayout";

export function StudyModePage() {
  const { examId, subjectId, chapterId } = useParams<{
    examId: string;
    subjectId: string;
    chapterId: string;
  }>();
  const navigate = useNavigate();
  const basePath = `/exam/${examId}/study/${subjectId}/${chapterId}`;

  const modes = [
    {
      id: "blank",
      title: "빈칸 뚫기",
      description: "핵심 키워드를 빈칸으로 가린 문장을 학습합니다",
      icon: "📝",
    },
    {
      id: "quiz",
      title: "기출 문제 풀기",
      description: "1문제씩 객관식 기출문제를 풀어봅니다",
      icon: "📋",
    },
  ];

  return (
    <MobileLayout title="학습 모드 선택" showBack>
      <div className="space-y-3">
        {modes.map((mode) => (
          <Card
            key={mode.id}
            className="cursor-pointer transition-colors hover:border-primary/50"
            onClick={() => navigate(`${basePath}/${mode.id}`)}
          >
            <CardHeader className="p-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{mode.icon}</span>
                <div>
                  <CardTitle className="text-base">{mode.title}</CardTitle>
                  <CardDescription className="text-sm">
                    {mode.description}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>
    </MobileLayout>
  );
}
