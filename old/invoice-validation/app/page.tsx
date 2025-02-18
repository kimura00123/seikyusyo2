"use client"

import * as React from "react"
import { useHotkeys } from "react-hotkeys-hook"
import { StructuredDataTable } from "@/components/structured-data-table"
import { PDFPreviewPane } from "@/components/pdf-preview-pane"
import { ValidationControls } from "@/components/validation-controls"
import type { InvoiceLineItem, LineItemValidation } from "@/types/invoice"

const sampleData: InvoiceLineItem[] = [
  {
    顧客名: "株式会社ＮＴＴフィールドテクノ",
    部署名: "人材戦略部 採用人事担当 様",
    箱番号: 353540070,
    明細番号: "1",
    摘要: "保管料 文書箱(0012000100100)",
    税率: "10%",
    金額: "¥1,600",
    数量情報: "carryover=25 incoming=0 w_value=0 outgoing=0 remaining=25 total=25 unit_price=64",
    対象期間: "2024/08月分(2024/08/01 - 2024/08/31)",
    データ期間: "2024/08月分(2024/08/01 - 2024/08/31)",
    ページ番号: "1",
    繰越在庫: "25",
    入庫数: "0",
    W値: "0",
    出庫数: "0",
    残数: "25",
    在庫合計: "25",
    単価: "64",
    数量: "",
    "単価(数量)": "",
  },
  {
    顧客名: "ＮＴＴビジネスソリューションズ株式会社",
    部署名: "カスタマーサクセス部 ビジネスサービスセンタ(大阪) 様",
    箱番号: 353540071,
    明細番号: "2",
    摘要: "保管料 文書箱(0012000200100)",
    税率: "10%",
    金額: "¥37,312",
    数量情報: "carryover=569 incoming=14 w_value=0 outgoing=0 remaining=583 total=583 unit_price=64",
    対象期間: "2024/08月分(2024/08/01 - 2024/08/31)",
    データ期間: "2024/08月分(2024/08/01 - 2024/08/31)",
    ページ番号: "1",
    繰越在庫: "569",
    入庫数: "14",
    W値: "0",
    出庫数: "0",
    残数: "583",
    在庫合計: "583",
    単価: "64",
    数量: "",
    "単価(数量)": "",
  },
  {
    顧客名: "ＮＴＴビジネスソリューションズ株式会社",
    部署名: "カスタマーサクセス部 ビジネスサービスセンタ(大阪) 様",
    箱番号: 353540071,
    明細番号: "3",
    摘要: "荷役料 - 新規入庫 文書箱(0012000200100)",
    税率: "10%",
    金額: "¥1,120",
    数量情報: "quantity=14 unit_price=80",
    対象期間: "2024/08月分(2024/08/01 - 2024/08/31)",
    データ期間: "2024/08月分(2024/08/01 - 2024/08/31)",
    ページ番号: "1",
    繰越在庫: "",
    入庫数: "",
    W値: "",
    出庫数: "",
    残数: "",
    在庫合計: "",
    単価: "",
    数量: "14",
    "単価(数量)": "80",
  },
]

export default function InvoiceValidationPage() {
  const [data, setData] = React.useState<InvoiceLineItem[]>(sampleData)
  const [validationState, setValidationState] = React.useState<Record<number, LineItemValidation>>(
    Object.fromEntries(sampleData.map((_, index) => [index, { isValid: false }])),
  )
  const [selectedRow, setSelectedRow] = React.useState(0)
  const [showUnvalidatedOnly, setShowUnvalidatedOnly] = React.useState(false)

  // Keyboard shortcuts
  useHotkeys("ctrl+enter", () => handleValidate(selectedRow, true))
  useHotkeys("ctrl+arrowdown", () => setSelectedRow((r) => Math.min(r + 1, data.length - 1)))
  useHotkeys("ctrl+arrowup", () => setSelectedRow((r) => Math.max(r - 1, 0)))

  const handleValidate = (index: number, isValid: boolean) => {
    setValidationState((prev) => ({
      ...prev,
      [index]: { isValid },
    }))
    if (isValid && index < data.length - 1) {
      setSelectedRow(index + 1)
    }
  }

  const handleUpdateCell = (index: number, key: keyof InvoiceLineItem, value: string) => {
    setData((prev) => {
      const next = [...prev]
      next[index] = { ...next[index], [key]: value }
      return next
    })
  }

  const validatedItems = Object.values(validationState).filter((v) => v.isValid).length

  const errorCount = Object.values(validationState).filter((v) =>
    Object.values(v).some((state) => !state.isValid),
  ).length

  const filteredData = showUnvalidatedOnly ? data.filter((_, index) => !validationState[index]?.isValid) : data

  return (
    <div className="h-screen flex flex-col">
      <ValidationControls
        totalItems={data.length}
        validatedItems={validatedItems}
        onValidateAll={() => data.forEach((_, i) => handleValidate(i, true))}
        onShowUnvalidated={() => setShowUnvalidatedOnly(!showUnvalidatedOnly)}
        errorCount={errorCount}
        onJumpToError={() => {
          const errorIndex = Object.entries(validationState).findIndex(([_, v]) =>
            Object.values(v).some((state) => !state.isValid),
          )
          if (errorIndex >= 0) setSelectedRow(Number(errorIndex))
        }}
        allValidated={validatedItems === data.length}
      />
      <div className="flex-1 grid grid-rows-2 gap-4 p-4">
        <StructuredDataTable
          data={filteredData}
          validationState={validationState}
          onValidate={handleValidate}
          onUpdateCell={handleUpdateCell}
          selectedRow={selectedRow}
          onSelectRow={setSelectedRow}
        />
        <PDFPreviewPane selectedInvoiceNumber={data[selectedRow].明細番号} />
      </div>
    </div>
  )
}

