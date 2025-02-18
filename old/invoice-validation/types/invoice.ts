export interface InvoiceLineItem {
  顧客名: string
  部署名: string
  箱番号: number
  明細番号: string
  摘要: string
  税率: string
  金額: string
  数量情報: string
  対象期間: string
  データ期間: string
  ページ番号: string
  繰越在庫: string
  入庫数: string
  W値: string
  出庫数: string
  残数: string
  在庫合計: string
  単価: string
  数量: string
  "単価(数量)": string
}

export interface ValidationState {
  isValid: boolean
  message?: string
}

export interface LineItemValidation {
  [key: string]: ValidationState
}

