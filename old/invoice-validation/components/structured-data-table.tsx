"use client"

import * as React from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { cn } from "@/lib/utils"
import type { InvoiceLineItem, LineItemValidation } from "../types/invoice"

interface StructuredDataTableProps {
  data: InvoiceLineItem[]
  validationState: Record<number, LineItemValidation>
  onValidate: (index: number, checked: boolean) => void
  onUpdateCell: (index: number, key: keyof InvoiceLineItem, value: string) => void
  selectedRow: number
  onSelectRow: (index: number) => void
}

export function StructuredDataTable({
  data,
  validationState,
  onValidate,
  onUpdateCell,
  selectedRow,
  onSelectRow,
}: StructuredDataTableProps) {
  const columns: (keyof InvoiceLineItem)[] = ["明細番号", "顧客名", "部署名", "箱番号", "摘要", "税率", "金額"]

  const renderTableCell = (row: InvoiceLineItem, column: keyof InvoiceLineItem, index: number) => (
    <TableCell key={column} className="p-0">
      <Input
        value={row[column]}
        onChange={(e) => onUpdateCell(index, column, e.target.value)}
        className={cn(
          "border-0 focus:ring-0",
          validationState[index]?.isValid
            ? "bg-gray-500 text-white"
            : selectedRow === index
              ? "bg-yellow-100"
              : "bg-gray-200",
        )}
      />
    </TableCell>
  )

  return (
    <div className="rounded-md border overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[50px]" rowSpan={2}>
              確認
            </TableHead>
            <TableHead className="w-12">明細番号</TableHead>
            <TableHead colSpan={3}>顧客情報</TableHead>
          </TableRow>
          <TableRow>
            <TableHead className="w-32">箱番号</TableHead>
            <TableHead>顧客名</TableHead>
            <TableHead>部署名</TableHead>
            <TableHead>摘要</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row, index) => (
            <React.Fragment key={index}>
              <TableRow
                className={cn(
                  validationState[index]?.isValid
                    ? "bg-gray-500 text-white"
                    : selectedRow === index
                      ? "bg-yellow-100"
                      : "bg-gray-200",
                )}
                onClick={() => onSelectRow(index)}
              >
                <TableCell
                  rowSpan={2}
                  className={cn(
                    "align-middle",
                    validationState[index]?.isValid
                      ? "bg-gray-500 text-white"
                      : selectedRow === index
                        ? "bg-yellow-100"
                        : "bg-gray-200",
                  )}
                >
                  <Checkbox
                    checked={validationState[index]?.isValid || false}
                    onCheckedChange={(checked) => onValidate(index, checked)}
                  />
                </TableCell>
                {renderTableCell(row, "箱番号", index)}
                {renderTableCell(row, "顧客名", index)}
                {renderTableCell(row, "部署名", index)}
                {renderTableCell(row, "摘要", index)}
              </TableRow>
              <TableRow
                className={cn(
                  validationState[index]?.isValid
                    ? "bg-gray-500 text-white"
                    : selectedRow === index
                      ? "bg-yellow-100"
                      : "bg-gray-200",
                )}
                onClick={() => onSelectRow(index)}
              >
                {renderTableCell(row, "明細番号", index)}
                {renderTableCell(row, "税率", index)}
                {renderTableCell(row, "金額", index)}
                <TableCell />
              </TableRow>
            </React.Fragment>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

