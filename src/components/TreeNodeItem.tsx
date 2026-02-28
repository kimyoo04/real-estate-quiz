import { useState } from "react";
import { ChevronRight, Pencil, Trash2, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { TreeNode } from "@/types/tree";
import { getLevelLabel, getLevelColor } from "@/utils/treeUtils";

interface TreeNodeItemProps {
  node: TreeNode;
  depth?: number;
  editMode?: boolean;
  defaultOpen?: boolean;
  onEdit?: (node: TreeNode) => void;
  onDelete?: (node: TreeNode) => void;
  onAddChild?: (parentNode: TreeNode) => void;
}

export function TreeNodeItem({
  node,
  depth = 0,
  editMode = false,
  defaultOpen = false,
  onEdit,
  onDelete,
  onAddChild,
}: TreeNodeItemProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const hasChildren = node.children && node.children.length > 0;
  const indent = depth * 16;

  const importanceStars = node.importance
    ? "★".repeat(node.importance) + "☆".repeat(5 - node.importance)
    : null;

  if (!hasChildren) {
    return (
      <div
        className="group flex items-start gap-2 rounded-md px-2 py-1.5 hover:bg-accent/50"
        style={{ paddingLeft: `${indent + 8}px` }}
      >
        <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/40" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <Badge className={`text-[10px] px-1.5 py-0 ${getLevelColor(node.level)}`}>
              {getLevelLabel(node.level)}
            </Badge>
            <span className="text-sm">{node.label}</span>
            {importanceStars && (
              <span className="text-[10px] text-amber-500">{importanceStars}</span>
            )}
          </div>
          {node.examFrequency && (
            <p className="text-xs text-muted-foreground mt-0.5">{node.examFrequency}</p>
          )}
          {node.description && (
            <p className="text-xs text-muted-foreground mt-0.5">{node.description}</p>
          )}
        </div>
        {editMode && (
          <div className="flex shrink-0 gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onAddChild?.(node)}>
              <Plus className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onEdit?.(node)}>
              <Pencil className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={() => onDelete?.(node)}>
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
    );
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div
        className="group flex items-center gap-1 rounded-md hover:bg-accent/50"
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
            <span className="text-sm font-medium">{node.label}</span>
            {importanceStars && (
              <span className="text-[10px] text-amber-500">{importanceStars}</span>
            )}
            {node.examFrequency && (
              <span className="text-[10px] text-muted-foreground">({node.examFrequency})</span>
            )}
            <span className="text-[10px] text-muted-foreground">
              ({node.children!.length})
            </span>
          </button>
        </CollapsibleTrigger>
        {editMode && (
          <div className="flex shrink-0 gap-0.5 pr-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onAddChild?.(node)}>
              <Plus className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => onEdit?.(node)}>
              <Pencil className="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={() => onDelete?.(node)}>
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
      <CollapsibleContent>
        {node.description && (
          <p
            className="text-xs text-muted-foreground px-2 pb-1"
            style={{ paddingLeft: `${indent + 32}px` }}
          >
            {node.description}
          </p>
        )}
        {node.children!.map((child) => (
          <TreeNodeItem
            key={child.id}
            node={child}
            depth={depth + 1}
            editMode={editMode}
            defaultOpen={defaultOpen}
            onEdit={onEdit}
            onDelete={onDelete}
            onAddChild={onAddChild}
          />
        ))}
      </CollapsibleContent>
    </Collapsible>
  );
}
