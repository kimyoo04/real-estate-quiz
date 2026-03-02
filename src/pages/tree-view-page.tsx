import { useState, useMemo, useCallback, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Search, ChevronsUpDown, Pencil, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { MobileLayout } from "@/components/mobile-layout";
import { TreeNodeItem } from "@/components/tree-node-item";
import { TreeNodeForm } from "@/components/tree-node-form";
import { useTreeStore } from "@/stores/use-tree-store";
import { useClassifyStore } from "@/stores/use-classify-store";
import { allSubjects } from "@/data/exam-tree";
import { filterTree, countNodes, generateNodeId, getChildLevel } from "@/utils/tree-utils";
import type { TreeNode } from "@/types/tree";

export function TreeViewPage() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const subject = allSubjects.find((s) => s.id === subjectId);

  const { getTree, addNode, updateNode, deleteNode, resetSubject, customTrees } = useTreeStore();
  const tree = getTree(subjectId!);
  const isCustomized = !!customTrees[subjectId!];

  const { overrides: classifyOverrides, defaults: classifyDefaults, loadDefaults } = useClassifyStore();

  // Load classification defaults from JSON
  useEffect(() => {
    if (!subjectId) return;
    fetch(`${import.meta.env.BASE_URL}data/realtor/${subjectId}/question_tree_map.json`)
      .then((res) => res.json())
      .then((data: { classified?: Record<string, string> }) => {
        if (data.classified) loadDefaults(data.classified);
      })
      .catch(() => {});
  }, [subjectId, loadDefaults]);

  // Compute per-node question counts from classification data
  const questionCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    const allMappings = { ...classifyDefaults, ...classifyOverrides };
    for (const [qId, nodeId] of Object.entries(allMappings)) {
      // Only count questions belonging to this subject
      if (qId.startsWith(subjectId + "_")) {
        counts[nodeId] = (counts[nodeId] || 0) + 1;
      }
    }
    return counts;
  }, [classifyDefaults, classifyOverrides, subjectId]);

  const hasQuestionCounts = Object.keys(questionCounts).length > 0;

  const [search, setSearch] = useState("");
  const [expandAll, setExpandAll] = useState(false);
  const [editMode, setEditMode] = useState(false);

  // CRUD state
  const [formOpen, setFormOpen] = useState(false);
  const [editingNode, setEditingNode] = useState<TreeNode | null>(null);
  const [addParentId, setAddParentId] = useState<string | null>(null);
  const [addParentLevel, setAddParentLevel] = useState<TreeNode["level"]>("major");
  const [deleteTarget, setDeleteTarget] = useState<TreeNode | null>(null);
  const [resetDialogOpen, setResetDialogOpen] = useState(false);

  const filteredTree = useMemo(
    () => (search ? filterTree(tree, search) : tree),
    [tree, search]
  );

  const nodeCount = useMemo(() => countNodes(tree), [tree]);

  const handleEdit = useCallback((node: TreeNode) => {
    setEditingNode(node);
    setAddParentId(null);
    setFormOpen(true);
  }, []);

  const handleAddChild = useCallback((parentNode: TreeNode) => {
    setEditingNode(null);
    setAddParentId(parentNode.id);
    setAddParentLevel(getChildLevel(parentNode.level));
    setFormOpen(true);
  }, []);

  const handleDelete = useCallback((node: TreeNode) => {
    setDeleteTarget(node);
  }, []);

  const confirmDelete = useCallback(() => {
    if (deleteTarget && subjectId) {
      deleteNode(subjectId, deleteTarget.id);
      setDeleteTarget(null);
    }
  }, [deleteTarget, subjectId, deleteNode]);

  const handleFormSubmit = useCallback(
    (data: Omit<TreeNode, "id" | "children">) => {
      if (!subjectId) return;

      if (editingNode) {
        updateNode(subjectId, editingNode.id, data);
      } else if (addParentId) {
        const newNode: TreeNode = {
          id: generateNodeId(addParentId),
          ...data,
        };
        addNode(subjectId, addParentId, newNode);
      }
      setFormOpen(false);
      setEditingNode(null);
      setAddParentId(null);
    },
    [subjectId, editingNode, addParentId, updateNode, addNode]
  );

  if (!subject) {
    return (
      <MobileLayout title="오류" showBack>
        <p className="text-center py-10 text-muted-foreground">과목을 찾을 수 없습니다.</p>
      </MobileLayout>
    );
  }

  return (
    <MobileLayout title={subject.name} showBack>
      <div className="space-y-3">
        {/* Toolbar */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="개념 검색..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 h-9"
            />
          </div>
          <Button
            variant="outline"
            size="icon"
            className="h-9 w-9 shrink-0"
            onClick={() => setExpandAll((v) => !v)}
            title={expandAll ? "모두 접기" : "모두 펼치기"}
          >
            <ChevronsUpDown className="h-4 w-4" />
          </Button>
          <Button
            variant={editMode ? "default" : "outline"}
            size="icon"
            className="h-9 w-9 shrink-0"
            onClick={() => setEditMode((v) => !v)}
            title={editMode ? "편집 완료" : "편집 모드"}
          >
            <Pencil className="h-4 w-4" />
          </Button>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="outline" className="text-xs">
            {nodeCount}개 개념
          </Badge>
          {isCustomized && (
            <Badge variant="secondary" className="text-xs">편집됨</Badge>
          )}
          {editMode && isCustomized && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-xs gap-1"
              onClick={() => setResetDialogOpen(true)}
            >
              <RotateCcw className="h-3 w-3" />
              초기화
            </Button>
          )}
        </div>

        {/* Tree */}
        <div className="rounded-lg border p-1">
          {filteredTree.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-6">
              {search ? "검색 결과가 없습니다." : "트리 데이터가 없습니다."}
            </p>
          ) : (
            filteredTree.map((node) => (
              <TreeNodeItem
                key={node.id}
                node={node}
                editMode={editMode}
                defaultOpen={expandAll}
                questionCounts={hasQuestionCounts ? questionCounts : undefined}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onAddChild={handleAddChild}
              />
            ))
          )}
        </div>
      </div>

      {/* Add/Edit Dialog */}
      <TreeNodeForm
        open={formOpen}
        onOpenChange={setFormOpen}
        node={editingNode}
        defaultLevel={addParentId ? addParentLevel : undefined}
        onSubmit={handleFormSubmit}
      />

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>노드 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              "{deleteTarget?.label}"을(를) 삭제하시겠습니까?
              {deleteTarget?.children && deleteTarget.children.length > 0 && (
                <span className="block mt-1 text-destructive font-medium">
                  하위 {deleteTarget.children.length}개 노드도 함께 삭제됩니다.
                </span>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-destructive text-destructive-foreground">
              삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reset Confirmation */}
      <AlertDialog open={resetDialogOpen} onOpenChange={setResetDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>기본값으로 초기화</AlertDialogTitle>
            <AlertDialogDescription>
              편집한 내용을 모두 삭제하고 기본 트리로 복원하시겠습니까?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                resetSubject(subjectId!);
                setResetDialogOpen(false);
              }}
            >
              초기화
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </MobileLayout>
  );
}
