import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ValidationResult {
  is_valid: boolean;
  errors: Array<{
    field: string;
    message: string;
    severity: 'error' | 'warning';
  }>;
}

export interface DocumentStructure {
  pdf_filename: string;
  total_amount: string;
  customers: CustomerEntry[];
}

export interface CustomerEntry {
  customer_code: string;
  customer_name: string;
  department: string;
  box_number: string;
  entries: EntryDetail[];
}

export interface EntryDetail {
  no: string;
  description: string;
  tax_rate: string;
  amount: string;
  stock_info?: StockInfo;
  quantity_info?: QuantityInfo;
  date_range?: string;
  page_no: number;
}

export interface StockInfo {
  carryover: number;
  incoming: number;
  w_value: number;
  outgoing: number;
  remaining: number;
  total: number;
  unit_price: number;
}

export interface QuantityInfo {
  quantity: number;
  unit_price?: number;
}

export const documentApi = {
  // PDFファイルをアップロード
  uploadPdf: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<{ task_id: string }>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // 処理状態を取得
  getProcessingStatus: async (taskId: string) => {
    const response = await api.get<{
      status: 'pending' | 'processing' | 'completed' | 'failed';
      result?: DocumentStructure;
      error?: string;
    }>(`/documents/status/${taskId}`);
    return response.data;
  },

  // バリデーション結果を取得
  getValidationResult: async (taskId: string) => {
    const response = await api.get<ValidationResult>(`/documents/validation/${taskId}`);
    return response.data;
  },

  // 明細画像を取得
  getDetailImage: async (taskId: string, detailNo: string) => {
    const response = await api.get<Blob>(`/documents/images/${taskId}/${detailNo}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // エクセルファイルをダウンロード
  downloadExcel: async (taskId: string) => {
    const response = await api.get<Blob>(`/documents/excel/${taskId}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};
