import { useParams, useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MobileLayout } from "@/components/MobileLayout";
import { examStructure } from "@/data/examTree";
import { countNodes } from "@/utils/treeUtils";

export function TreeSubjectListPage() {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();

  const sections = [
    { label: "1차 시험", subjects: examStructure.firstExam },
    { label: "2차 시험", subjects: examStructure.secondExam },
  ];

  return (
    <MobileLayout title="개념 트리" showBack>
      <div className="space-y-5">
        {sections.map((section) => (
          <div key={section.label}>
            <h2 className="mb-2 text-sm font-semibold text-muted-foreground">
              {section.label}
            </h2>
            <div className="space-y-2">
              {section.subjects.map((subject) => {
                const nodeCount = countNodes(subject.tree);
                return (
                  <Card
                    key={subject.id}
                    className="cursor-pointer transition-colors hover:border-primary/50"
                    onClick={() => navigate(`/exam/${examId}/tree/${subject.id}`)}
                  >
                    <CardHeader className="p-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm font-medium">
                          {subject.name}
                        </CardTitle>
                        <div className="flex items-center gap-1.5">
                          <Badge variant="outline" className="text-xs">
                            {nodeCount}개 개념
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {subject.questionCount}문항
                          </Badge>
                        </div>
                      </div>
                      <CardDescription className="text-xs mt-1">
                        {subject.tree.map((n) => n.label).join(" · ")}
                      </CardDescription>
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
