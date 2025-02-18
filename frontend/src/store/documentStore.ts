import { create } from 'zustand';
import { DocumentStructure, ValidationResult, documentApi } from '../services/api';

interface DocumentState {
  // 状態
  taskId: string | null;
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';
  document: DocumentStructure | null;
  validation: ValidationResult | null;
  error: string | null;

  // アクション
  uploadDocument: (file: File) => Promise<void>;
  checkStatus: () => Promise<void>;
  getValidation: () => Promise<void>;
  reset: () => void;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  // 初期状態
  taskId: null,
  status: 'idle',
  document: null,
  validation: null,
  error: null,

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
    });
  },
}));
