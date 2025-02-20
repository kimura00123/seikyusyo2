import { create } from 'zustand';
import { DocumentStructure, ValidationResult, documentApi } from '../services/api';

interface DetailWithCustomer {
  no: string;
  description: string;
  tax_rate: string;
  amount: string;
  stock_info?: {
    carryover: number;
    incoming: number;
    w_value: number;
    outgoing: number;
    remaining: number;
    total: number;
    unit_price: number;
  };
  quantity_info?: {
    quantity: number;
    unit_price?: number;
  };
  date_range?: string;
  page_no: number;
  customer_code: string;
  customer_name: string;
}

interface DocumentState {
  // 状態
  taskId: string | null;
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';
  document: DocumentStructure | null;
  validation: ValidationResult | null;
  error: string | null;
  selectedDetail: DetailWithCustomer | null;
  approvedDetails: Map<string, { approved_at: string; approved_by: string }>;

  // アクション
  uploadDocument: (file: File) => Promise<void>;
  checkStatus: () => Promise<void>;
  getValidation: () => Promise<void>;
  reset: () => void;
  selectDetail: (detail: DetailWithCustomer) => void;
  clearSelectedDetail: () => void;
  approveDetail: (detailNo: string, userId: string) => Promise<void>;
  approveMultipleDetails: (detailNos: string[], userId: string) => Promise<void>;
  approveAllDetails: (userId: string) => Promise<void>;
  cancelApproval: (detailNo: string, userId: string) => Promise<void>;
  cancelMultipleApprovals: (detailNos: string[], userId: string) => Promise<void>;
  loadApprovalStatus: () => Promise<void>;
  getNextUnapprovedDetail: () => DetailWithCustomer | null;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  // 初期状態
  taskId: null,
  status: 'idle',
  document: null,
  validation: null,
  error: null,
  selectedDetail: null,
  approvedDetails: new Map(),

  // アクション
  uploadDocument: async (file: File) => {
    try {
      set({ status: 'uploading', error: null });
      const { task_id } = await documentApi.uploadPdf(file);
      set({ taskId: task_id, status: 'processing' });

      // 処理状態の監視を開始
      const checkStatus = async () => {
        const result = await documentApi.getProcessingStatus(task_id);
        if (result.status === 'completed') {
          set({ status: 'completed', document: result.result || null });
        } else if (result.status === 'failed') {
          set({ status: 'failed', error: result.error || '処理に失敗しました' });
        } else {
          // 処理中の場合は1秒後に再確認
          setTimeout(checkStatus, 1000);
        }
      };
      checkStatus();
    } catch (error) {
      set({ 
        status: 'failed', 
        error: error instanceof Error ? error.message : '処理に失敗しました'
      });
    }
  },

  checkStatus: async () => {
    const { taskId } = get();
    if (!taskId) return;

    try {
      const result = await documentApi.getProcessingStatus(taskId);
      if (result.status === 'completed') {
        set({ status: 'completed', document: result.result || null });
      } else if (result.status === 'failed') {
        set({ status: 'failed', error: result.error || '処理に失敗しました' });
      }
    } catch (error) {
      set({ 
        status: 'failed', 
        error: error instanceof Error ? error.message : '処理に失敗しました'
      });
    }
  },

  getValidation: async () => {
    const { taskId } = get();
    if (!taskId) return;

    try {
      const validation = await documentApi.getValidationResult(taskId);
      set({ validation });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'バリデーションの取得に失敗しました'
      });
    }
  },

  reset: () => {
    set({
      taskId: null,
      status: 'idle',
      document: null,
      validation: null,
      error: null,
      selectedDetail: null,
      approvedDetails: new Map(),
    });
  },

  approveDetail: async (detailNo: string, userId: string) => {
    const { taskId } = get();
    if (!taskId) return;

    try {
      const result = await documentApi.approveDetail(taskId, detailNo, userId);
      if (result.success) {
        set(state => ({
          approvedDetails: new Map(state.approvedDetails).set(detailNo, {
            approved_at: result.approved_at,
            approved_by: result.approved_by,
          }),
        }));
      }
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '承認に失敗しました'
      });
    }
  },

  approveMultipleDetails: async (detailNos: string[], userId: string) => {
    const { taskId } = get();
    if (!taskId) return;

    try {
      // 順次承認処理
      for (const detailNo of detailNos) {
        const result = await documentApi.approveDetail(taskId, detailNo, userId);
        if (result.success) {
          set(state => ({
            approvedDetails: new Map(state.approvedDetails).set(detailNo, {
              approved_at: result.approved_at,
              approved_by: result.approved_by,
            }),
          }));
        }
      }
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '一括承認に失敗しました'
      });
    }
  },

  approveAllDetails: async (userId: string) => {
    const { taskId, document } = get();
    if (!taskId || !document) return;

    try {
      // すべての明細番号を取得
      const allDetailNos = document.customers.flatMap(customer =>
        customer.entries.map(entry => entry.no)
      );

      // 一括承認を実行
      await get().approveMultipleDetails(allDetailNos, userId);
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '全件承認に失敗しました'
      });
    }
  },

  cancelApproval: async (detailNo: string, userId: string) => {
    const { taskId } = get();
    if (!taskId) return;

    try {
      const result = await documentApi.cancelApproval(taskId, detailNo, userId);
      if (result.success) {
        set(state => {
          const newApprovedDetails = new Map(state.approvedDetails);
          newApprovedDetails.delete(detailNo);
          return { approvedDetails: newApprovedDetails };
        });
      }
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '承認取り消しに失敗しました'
      });
    }
  },

  cancelMultipleApprovals: async (detailNos: string[], userId: string) => {
    const { taskId } = get();
    if (!taskId) return;

    try {
      // 順次承認取り消し処理
      for (const detailNo of detailNos) {
        await get().cancelApproval(detailNo, userId);
      }
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '一括承認取り消しに失敗しました'
      });
    }
  },

  loadApprovalStatus: async () => {
    const { taskId } = get();
    if (!taskId) return;

    try {
      const result = await documentApi.getApprovalStatus(taskId);
      const approvedDetails = new Map(
        result.approved_details.map(detail => [
          detail.detail_no,
          { 
            approved_at: detail.approved_at, 
            approved_by: detail.approved_by 
          },
        ])
      );
      set({ approvedDetails });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '承認状態の取得に失敗しました'
      });
    }
  },

  getNextUnapprovedDetail: () => {
    const { document, approvedDetails, selectedDetail } = get();
    if (!document) return null;

    // すべての明細を取得
    const allDetails = document.customers.flatMap(customer =>
      customer.entries.map(entry => ({
        ...entry,
        customer_code: customer.customer_code,
        customer_name: customer.customer_name,
      }))
    );

    // 現在の明細のインデックスを取得
    const currentIndex = selectedDetail 
      ? allDetails.findIndex(detail => detail.no === selectedDetail.no)
      : -1;

    // 現在の明細以降で最初の未承認明細を探す
    for (let i = currentIndex + 1; i < allDetails.length; i++) {
      if (!approvedDetails.has(allDetails[i].no)) {
        return allDetails[i];
      }
    }

    // 見つからない場合は最初から探す（ただし現在の明細より前まで）
    for (let i = 0; i < currentIndex; i++) {
      if (!approvedDetails.has(allDetails[i].no)) {
        return allDetails[i];
      }
    }

    return null;  // 未承認明細が見つからない場合
  },

  selectDetail: (detail: DetailWithCustomer) => {
    set({ selectedDetail: detail });
  },

  clearSelectedDetail: () => {
    set({ selectedDetail: null });
  },
}));

export type { DetailWithCustomer };
