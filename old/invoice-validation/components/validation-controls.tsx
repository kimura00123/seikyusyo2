"use client"

import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { AlertCircle, CheckCircle2, Eye } from "lucide-react"

interface ValidationControlsProps {
  totalItems: number
  validatedItems: number
  onValidateAll: () => void
  onShowUnvalidated: () => void
  errorCount: number
  onJumpToError: () => void
  allValidated: boolean
}

export function ValidationControls({
  totalItems,
  validatedItems,
  onValidateAll,
  onShowUnvalidated,
  errorCount,
  onJumpToError,
  allValidated,
}: ValidationControlsProps) {
  const progress = (validatedItems / totalItems) * 100

  return (
    <div className="flex items-center gap-4 p-4 border-b">
      <Button onClick={onValidateAll}>一括確認</Button>
      <Button onClick={onShowUnvalidated} variant="outline" className="gap-2">
        <Eye className="h-4 w-4" />
        未確認のみ表示
      </Button>
      <div className="flex-1">
        <div className="flex justify-between text-sm mb-1">
          <span>進捗状況</span>
          <span>
            {validatedItems}/{totalItems} 確認済み
          </span>
        </div>
        <Progress value={progress} className={allValidated ? "bg-green-500" : ""} />
        {allValidated && <div className="text-green-600 text-sm mt-1 font-semibold">全ての項目が確認済みです</div>}
      </div>
      {errorCount > 0 && (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="destructive" size="sm" className="gap-2" onClick={onJumpToError}>
                <AlertCircle className="h-4 w-4" />
                {errorCount}件のエラー
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>エラー箇所にジャンプ</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )}
    </div>
  )
}

