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
  isApproved?: boolean;
  approvedAt?: string;
  approvedBy?: string;
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

export interface DetailWithCustomer extends EntryDetail {
  customer_code: string;
  customer_name: string;
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
  downloadExcel: async (taskId: string, editedDetails?: Map<string, DetailWithCustomer>) => {
    try {
      console.log('Excel出力リクエスト開始:', taskId);
      
      // 編集データがある場合はログ出力
      if (editedDetails && editedDetails.size > 0) {
        console.log(`編集データあり: ${editedDetails.size}件`);
      }
      
      const response = await api.post<Blob>(
        `/documents/excel/${taskId}`,
        editedDetails ? { edited_details: Object.fromEntries(editedDetails) } : null,
        { 
          responseType: 'blob',
          timeout: 30000, // タイムアウトを30秒に設定
          headers: {
            'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          }
        }
      );
      
      console.log('Excel出力レスポンス受信:', {
        status: response.status,
        contentType: response.headers['content-type'],
        contentLength: response.headers['content-length'],
        contentDisposition: response.headers['content-disposition'],
        blobSize: response.data.size
      });
      
      // Content-Dispositionヘッダーからファイル名を抽出（サーバーから提供されている場合）
      const contentDisposition = response.headers['content-disposition'];
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          // ファイル名を抽出して引用符を削除
          let extractedFilename = filenameMatch[1].replace(/['"]/g, '');
          console.log('サーバーから提供されたファイル名:', extractedFilename);
          
          // ファイル名をレスポンスデータに添付
          Object.defineProperty(response.data, 'filename', {
            value: extractedFilename,
            writable: true
          });
        }
      }
      
      // レスポンスの検証
      if (!response.data || response.data.size === 0) {
        throw new Error('サーバーから空のファイルが返されました');
      }
      
      // Content-Typeの検証
      const contentType = response.headers['content-type'];
      if (contentType && (
        contentType.includes('json') || 
        contentType.includes('text/plain') || 
        contentType.includes('text/html')
      )) {
        // JSONまたはテキストの場合はエラーメッセージとして読み取る
        const text = await response.data.text();
        try {
          const errorData = JSON.parse(text);
          throw new Error(errorData.detail || 'サーバーエラーが発生しました');
        } catch (parseError) {
          throw new Error(`サーバーエラー: ${text}`);
        }
      }
      
      return response.data;
    } catch (error) {
      console.error('Excel出力エラー:', error);
      
      // Axiosエラーの詳細情報を出力
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any;
        console.error('API Error Details:', {
          status: axiosError.response?.status,
          statusText: axiosError.response?.statusText,
          data: axiosError.response?.data,
          headers: axiosError.response?.headers,
          message: axiosError.message
        });
        
        // エラーレスポンスがBlobの場合はテキストとして読み取る
        if (axiosError.response?.data instanceof Blob) {
          axiosError.response.data.text().then((text: string) => {
            console.error('エラーレスポンスの内容:', text);
            try {
              const errorData = JSON.parse(text);
              console.error('解析されたエラー:', errorData);
            } catch (e) {
              // JSONとして解析できない場合は何もしない
            }
          }).catch((e: any) => {
            console.error('エラーレスポンスの読み取りに失敗:', e);
          });
        }
      }
      
      throw error;
    }
  },

  // 明細を承認
  approveDetail: async (taskId: string, detailNo: string, userId: string, editedDetail?: DetailWithCustomer) => {
    const response = await api.post<{
      success: boolean;
      detail_no: string;
      approved: boolean;
      approved_at: string;
      approved_by: string;
      message: string;
    }>(`/approvals/${taskId}/${detailNo}`, editedDetail, {
      params: { user_id: userId },
    });
    return response.data;
  },

  // 承認を取り消し
  cancelApproval: async (taskId: string, detailNo: string, userId: string) => {
    const response = await api.delete<{
      success: boolean;
      detail_no: string;
      approved: boolean;
      approved_at: string | null;
      approved_by: string | null;
      message: string;
    }>(`/approvals/${taskId}/${detailNo}`, {
      params: { user_id: userId },
    });
    return response.data;
  },

  // 承認状態を取得
  getApprovalStatus: async (taskId: string) => {
    const response = await api.get<{
      task_id: string;
      approved_details: Array<{
        detail_no: string;
        approved: boolean;
        approved_at: string;
        approved_by: string;
        task_id: string;
      }>;
      total_details: number;
      approved_count: number;
    }>(`/approvals/${taskId}`);
    return response.data;
  },

  // 承認履歴を取得
  getApprovalHistory: async (taskId: string, detailNo?: string) => {
    const url = detailNo 
      ? `/approvals/${taskId}/history?detail_no=${detailNo}`
      : `/approvals/${taskId}/history`;
    const response = await api.get<Array<{
      detail_no: string;
      action: "approve" | "cancel";
      timestamp: string;
      user_id: string;
      task_id: string;
      reason?: string;
    }>>(url);
    return response.data;
  },
};
