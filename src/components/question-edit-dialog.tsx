import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useQuestionEditStore } from "@/stores/use-question-edit-store";
import type { Question, MultipleChoiceQuestion, FillInTheBlankQuestion } from "@/types";
import { Trash2Icon, PlusIcon } from "lucide-react";

interface QuestionEditDialogProps {
  question: Question;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function QuestionEditDialog({
  question,
  open,
  onOpenChange,
}: QuestionEditDialogProps) {
  const { setQuestionEdit, removeQuestionEdit, questionEdits } = useQuestionEditStore();

  const [content, setContent] = useState("");
  const [explanation, setExplanation] = useState("");
  // MC-specific
  const [options, setOptions] = useState<string[]>([]);
  const [correctIndex, setCorrectIndex] = useState(0);
  // Fill-blank-specific
  const [answer, setAnswer] = useState("");

  useEffect(() => {
    if (!open) return;
    // Merge original with existing edits for initial form state
    const edits = questionEdits[question.id];
    const merged = edits ? { ...question, ...edits } : question;

    setContent(merged.content);
    setExplanation(merged.explanation);

    if (merged.type === "multiple_choice") {
      const mc = merged as MultipleChoiceQuestion;
      setOptions([...mc.options]);
      setCorrectIndex(mc.correctIndex);
    } else {
      const fb = merged as FillInTheBlankQuestion;
      setAnswer(fb.answer);
    }
  }, [open, question, questionEdits]);

  const handleSave = () => {
    if (question.type === "multiple_choice") {
      setQuestionEdit(question.id, {
        content,
        explanation,
        options,
        correctIndex,
      } as Partial<MultipleChoiceQuestion>);
    } else {
      setQuestionEdit(question.id, {
        content,
        explanation,
        answer,
      } as Partial<FillInTheBlankQuestion>);
    }
    onOpenChange(false);
  };

  const handleReset = () => {
    removeQuestionEdit(question.id);
    onOpenChange(false);
  };

  const updateOption = (index: number, value: string) => {
    setOptions((prev) => prev.map((o, i) => (i === index ? value : o)));
  };

  const addOption = () => {
    setOptions((prev) => [...prev, ""]);
  };

  const removeOption = (index: number) => {
    setOptions((prev) => prev.filter((_, i) => i !== index));
    if (correctIndex >= options.length - 1) {
      setCorrectIndex(Math.max(0, options.length - 2));
    }
  };

  const hasEdits = !!questionEdits[question.id];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>문제 편집</DialogTitle>
          <DialogDescription>
            {question.id} ({question.type === "multiple_choice" ? "객관식" : "빈칸뚫기"})
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">문제 내용</label>
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={4}
              className="resize-y"
            />
          </div>

          {question.type === "multiple_choice" && (
            <>
              <div>
                <label className="text-sm font-medium mb-1 block">선택지</label>
                <div className="space-y-2">
                  {options.map((opt, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="text-xs text-muted-foreground w-5 shrink-0">
                        {idx + 1}.
                      </span>
                      <Input
                        value={opt}
                        onChange={(e) => updateOption(idx, e.target.value)}
                        className="flex-1"
                      />
                      {options.length > 2 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="shrink-0 h-8 w-8 p-0"
                          onClick={() => removeOption(idx)}
                        >
                          <Trash2Icon className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-2 gap-1"
                  onClick={addOption}
                >
                  <PlusIcon className="h-3.5 w-3.5" />
                  선택지 추가
                </Button>
              </div>

              <div>
                <label className="text-sm font-medium mb-1 block">정답</label>
                <Select
                  value={String(correctIndex)}
                  onValueChange={(v) => setCorrectIndex(Number(v))}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {options.map((_, idx) => (
                      <SelectItem key={idx} value={String(idx)}>
                        {idx + 1}번
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </>
          )}

          {question.type === "fill_in_the_blank" && (
            <div>
              <label className="text-sm font-medium mb-1 block">정답</label>
              <Input
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
              />
            </div>
          )}

          <div>
            <label className="text-sm font-medium mb-1 block">해설</label>
            <Textarea
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              rows={3}
              className="resize-y"
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          {hasEdits && (
            <Button variant="destructive" size="sm" onClick={handleReset}>
              원래대로
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
            취소
          </Button>
          <Button size="sm" onClick={handleSave}>
            저장
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
