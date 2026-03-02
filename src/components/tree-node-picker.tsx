import { useState, useMemo } from "react";
import { ChevronRight, Check, Search } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { useTreeStore } from "@/stores/use-tree-store";
import { getLevelColor, getLevelLabel, filterTree } from "@/utils/tree-utils";
import type { TreeNode } from "@/types/tree";

interface TreeNodePickerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  subjectId: string;
  selectedNodeId?: string;
  onSelect: (nodeId: string, nodePath: string) => void;
}

function getNodePath(nodes: TreeNode[], targetId: string, path: string[] = []): string | null {
  for (const node of nodes) {
    const currentPath = [...path, node.label];
    if (node.id === targetId) return currentPath.join(" > ");
    if (node.children) {
      const found = getNodePath(node.children, targetId, currentPath);
      if (found) return found;
    }
  }
  return null;
}

function PickerNode({
  node,
  depth = 0,
  selectedId,
  onSelect,
  defaultOpen = false,
}: {
  node: TreeNode;
  depth?: number;
  selectedId?: string;
  onSelect: (id: string) => void;
  defaultOpen?: boolean;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = node.id === selectedId;
  const indent = depth * 16;

  if (!hasChildren) {
    return (
      <button
        className={`flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-left hover:bg-accent/50 ${
          isSelected ? "bg-primary/10 ring-1 ring-primary/30" : ""
        }`}
        style={{ paddingLeft: `${indent + 8}px` }}
        onClick={() => onSelect(node.id)}
      >
        <div className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/40" />
        <Badge className={`text-[10px] px-1.5 py-0 ${getLevelColor(node.level)}`}>
          {getLevelLabel(node.level)}
        </Badge>
        <span className="text-sm flex-1">{node.label}</span>
        {isSelected && <Check className="h-4 w-4 text-primary shrink-0" />}
      </button>
    );
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div
        className={`flex items-center gap-1 rounded-md hover:bg-accent/50 ${
          isSelected ? "bg-primary/10 ring-1 ring-primary/30" : ""
        }`}
        style={{ paddingLeft: `${indent}px` }}
      >
        <CollapsibleTrigger asChild>
          <button className="flex flex-1 items-center gap-1.5 px-2 py-1.5 text-left">
            <ChevronRight
              className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform ${
                isOpen ? "rotate-90" : ""
              }`}
            />
            <Badge className={`text-[10px] px-1.5 py-0 ${getLevelColor(node.level)}`}>
              {getLevelLabel(node.level)}
            </Badge>
            <span className="text-sm font-medium flex-1">{node.label}</span>
          </button>
        </CollapsibleTrigger>
        <Button
          variant={isSelected ? "default" : "ghost"}
          size="sm"
          className="h-6 text-xs mr-1 shrink-0"
          onClick={() => onSelect(node.id)}
        >
          {isSelected ? <Check className="h-3 w-3" /> : "선택"}
        </Button>
      </div>
      <CollapsibleContent>
        {node.children!.map((child) => (
          <PickerNode
            key={child.id}
            node={child}
            depth={depth + 1}
            selectedId={selectedId}
            onSelect={onSelect}
            defaultOpen={defaultOpen}
          />
        ))}
      </CollapsibleContent>
    </Collapsible>
  );
}

export function TreeNodePicker({
  open,
  onOpenChange,
  subjectId,
  selectedNodeId,
  onSelect,
}: TreeNodePickerProps) {
  const [search, setSearch] = useState("");
  const tree = useTreeStore((s) => s.getTree(subjectId));

  const filteredTree = useMemo(
    () => (search ? filterTree(tree, search) : tree),
    [tree, search]
  );

  const handleSelect = (nodeId: string) => {
    const path = getNodePath(tree, nodeId);
    onSelect(nodeId, path ?? nodeId);
    onOpenChange(false);
    setSearch("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] flex flex-col p-4 gap-3">
        <DialogHeader>
          <DialogTitle className="text-base">트리 노드 선택</DialogTitle>
        </DialogHeader>

        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="개념 검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 h-9"
          />
        </div>

        {selectedNodeId && (
          <div className="text-xs text-muted-foreground bg-muted/50 rounded-md px-2 py-1">
            현재: {getNodePath(tree, selectedNodeId) ?? selectedNodeId}
          </div>
        )}

        <div className="flex-1 overflow-y-auto rounded-lg border p-1 min-h-0">
          {filteredTree.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-6">
              {search ? "검색 결과가 없습니다." : "트리 데이터가 없습니다."}
            </p>
          ) : (
            filteredTree.map((node) => (
              <PickerNode
                key={node.id}
                node={node}
                selectedId={selectedNodeId}
                onSelect={handleSelect}
                defaultOpen={!!search}
              />
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
