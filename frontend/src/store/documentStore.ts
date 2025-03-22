import { create } from 'zustand';
import { DocumentStructure, ValidationResult, documentApi, DetailWithCustomer } from '../services/api';

// DetailWithCustomerの型を再エクスポート
export type { DetailWithCustomer };

interface DocumentState {
  // 状態
  taskId: string | null;
  status: 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';
  document: DocumentStructure | null;
  validation: ValidationResult | null;
  error: string | null;
  selectedDetail: DetailWithCustomer | null;
  approvedDetails: Map<string, { approved_at: string; approved_by: string }>;
  editedDetails: Map<string, DetailWithCustomer>;  // 編集中の値を保持
  pendingApprovals: Map<string, { action: 'approve' | 'cancel'; userId: string; detail?: DetailWithCustomer }>;  // 未同期の承認状態
  isSyncing: boolean;  // 同期中かどうか
  isOfflineMode: boolean;  // オフラインモードかどうか
  networkError: string | null;  // ネットワークエラーメッセージ

  // アクション
  uploadDocument: (file: File) => Promise<void>;
  checkStatus: () => Promise<void>;
  getValidation: () => Promise<void>;
  reset: () => void;
  selectDetail: (detail: DetailWithCustomer) => void;
  clearSelectedDetail: () => void;
  updateDetail: (detailNo: string, updatedDetail: Partial<DetailWithCustomer>) => void;
  resetEditedDetail: (detailNo: string) => void;
  
  // 既存の承認関連メソッド（APIリクエストあり）
  approveDetail: (detailNo: string, userId: string) => Promise<void>;
  approveMultipleDetails: (detailNos: string[], userId: string) => Promise<void>;
  approveAllDetails: (userId: string) => Promise<void>;
  cancelApproval: (detailNo: string, userId: string) => Promise<void>;
  cancelMultipleApprovals: (detailNos: string[], userId: string) => Promise<void>;
  
  // 新しいローカル承認関連メソッド（APIリクエストなし）
  localApproveDetail: (detailNo: string, userId: string) => void;
  localApproveMultipleDetails: (detailNos: string[], userId: string) => void;
  localApproveAllDetails: (userId: string) => void;
  localCancelApproval: (detailNo: string, userId: string) => void;
  localCancelMultipleApprovals: (detailNos: string[], userId: string) => void;
  
  // 一括同期メソッド
  syncPendingApprovals: (progressCallback?: (current: number, total: number) => void) => Promise<boolean>;
  
  // オフラインモード関連
  setOfflineMode: (enabled: boolean) => void;
  saveToLocalStorage: () => void;
  loadFromLocalStorage: () => void;
  
  loadApprovalStatus: () => Promise<void>;
  getNextUnapprovedDetail: () => DetailWithCustomer | null;
}

// APIエンドポイントのプレフィックス
// 開発環境と本番環境の両方で /api を使用
const API_PREFIX = '/api';

export const useDocumentStore = create<DocumentState>((set, get) => ({
  // 初期状態
  taskId: null,
  status: 'idle',
  document: null,
  validation: null,
  error: null,
  selectedDetail: null,
  approvedDetails: new Map(),
  editedDetails: new Map(),
  pendingApprovals: new Map(),
  isSyncing: false,
  isOfflineMode: false,
  networkError: null,

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
          // 処理完了時にバリデーション結果も取得
          get().getValidation();
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
        // 処理完了時にバリデーション結果も取得
        get().getValidation();
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
      
      // バリデーション結果をログに出力
      console.log('Validation Result:', {
        isValid: validation.is_valid,
        errorsCount: validation.errors.length,
        errors: validation.errors
      });
      
      // エラーの詳細情報をログに出力
      if (validation.errors.length > 0) {
        console.group('Validation Errors:');
        validation.errors.forEach((error, index) => {
          console.log(`Error ${index + 1}:`, {
            field: error.field,
            message: error.message,
            severity: error.severity
          });
        });
        console.groupEnd();
      }
      
      set({ validation });
    } catch (error) {
      // エラー情報をより詳細にログ出力
      console.error('Validation fetch error:', error);
      
      // Axiosエラーの場合は詳細情報を取得
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any;
        console.error('API Error Details:', {
          status: axiosError.response?.status,
          statusText: axiosError.response?.statusText,
          data: axiosError.response?.data,
          message: axiosError.message
        });
      }
      
      // エラーメッセージをユーザーフレンドリーにする
      const errorMessage = error instanceof Error 
        ? `バリデーションの取得に失敗しました: ${error.message}`
        : 'バリデーションの取得に失敗しました';
      
      set({ 
        error: errorMessage,
        // バリデーションエラーでもアプリケーションは継続できるようにする
        validation: { is_valid: true, errors: [] }
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
      editedDetails: new Map(),
      pendingApprovals: new Map(),
      isSyncing: false,
      isOfflineMode: false,
      networkError: null,
    });
  },

  updateDetail: (detailNo: string, updatedDetail: Partial<DetailWithCustomer>) => {
    set(state => {
      const newEditedDetails = new Map(state.editedDetails);
      const currentDetail = state.editedDetails.get(detailNo) || state.document?.customers
        .flatMap(c => ({
          ...c.entries.find(e => e.no === detailNo),
          customer_code: c.customer_code,
          customer_name: c.customer_name,
        }))
        .find(Boolean) as DetailWithCustomer | undefined;
        
      if (currentDetail) {
        newEditedDetails.set(detailNo, { ...currentDetail, ...updatedDetail });
      }
      return { editedDetails: newEditedDetails };
    });
  },

  resetEditedDetail: (detailNo: string) => {
    set(state => {
      const newEditedDetails = new Map(state.editedDetails);
      newEditedDetails.delete(detailNo);
      return { editedDetails: newEditedDetails };
    });
  },

  approveDetail: async (detailNo: string, userId: string) => {
    const { taskId, editedDetails } = get();
    if (!taskId) return;

    try {
      // 編集された値がある場合は、それを含めて承認
      const editedDetail = editedDetails.get(detailNo);
      const result = await documentApi.approveDetail(taskId, detailNo, userId, editedDetail);
      if (result.success) {
        set(state => {
          const newApprovedDetails = new Map(state.approvedDetails).set(detailNo, {
            approved_at: result.approved_at,
            approved_by: result.approved_by,
          });
          const newEditedDetails = new Map(state.editedDetails);
          newEditedDetails.delete(detailNo); // 承認後は編集値をクリア
          return { 
            approvedDetails: newApprovedDetails,
            editedDetails: newEditedDetails,
          };
        });
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
    const { taskId, isOfflineMode } = get();
    if (!taskId) return;

    // オフラインモードの場合はローカルストレージから読み込む
    if (isOfflineMode) {
      get().loadFromLocalStorage();
      return;
    }

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
      
      // 成功したらローカルストレージにも保存
      get().saveToLocalStorage();
    } catch (error) {
      console.error('承認状態の取得に失敗しました:', error);
      
      // ネットワークエラーの場合はローカルストレージから読み込む
      get().loadFromLocalStorage();
      
      const errorMessage = error instanceof Error ? error.message : '承認状態の取得に失敗しました';
      const isNetworkError = 
        errorMessage.includes('network') || 
        errorMessage.includes('Failed to fetch') || 
        errorMessage.includes('getaddrinfo failed') ||
        errorMessage.includes('ECONNREFUSED');
      
      set({ 
        error: errorMessage,
        networkError: isNetworkError ? errorMessage : null,
        // ネットワークエラーの場合は自動的にオフラインモードに切り替え
        isOfflineMode: isNetworkError
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

  // 新しいローカル承認メソッド（APIリクエストなし）
  localApproveDetail: (detailNo: string, userId: string) => {
    set(state => {
      const now = new Date().toISOString();
      
      // 承認状態を更新
      const newApprovedDetails = new Map(state.approvedDetails).set(detailNo, {
        approved_at: now,
        approved_by: userId,
      });
      
      // 未同期リストに追加
      const newPendingApprovals = new Map(state.pendingApprovals);
      const editedDetail = state.editedDetails.get(detailNo);
      newPendingApprovals.set(detailNo, { 
        action: 'approve', 
        userId, 
        detail: editedDetail 
      });
      
      // 編集値をクリア
      const newEditedDetails = new Map(state.editedDetails);
      newEditedDetails.delete(detailNo);
      
      return { 
        approvedDetails: newApprovedDetails,
        pendingApprovals: newPendingApprovals,
        editedDetails: newEditedDetails,
      };
    });
  },

  localApproveMultipleDetails: (detailNos: string[], userId: string) => {
    set(state => {
      const now = new Date().toISOString();
      const newApprovedDetails = new Map(state.approvedDetails);
      const newPendingApprovals = new Map(state.pendingApprovals);
      
      // 各明細を処理
      for (const detailNo of detailNos) {
        newApprovedDetails.set(detailNo, {
          approved_at: now,
          approved_by: userId,
        });
        
        newPendingApprovals.set(detailNo, { 
          action: 'approve', 
          userId 
        });
      }
      
      return { 
        approvedDetails: newApprovedDetails,
        pendingApprovals: newPendingApprovals,
      };
    });
  },

  localApproveAllDetails: (userId: string) => {
    const { document } = get();
    if (!document) return;

    // すべての明細番号を取得
    const allDetailNos = document.customers.flatMap(customer =>
      customer.entries.map(entry => entry.no)
    );

    // 一括承認を実行
    get().localApproveMultipleDetails(allDetailNos, userId);
  },

  localCancelApproval: (detailNo: string, userId: string) => {
    set(state => {
      // 承認状態を更新
      const newApprovedDetails = new Map(state.approvedDetails);
      newApprovedDetails.delete(detailNo);
      
      // 未同期リストに追加
      const newPendingApprovals = new Map(state.pendingApprovals);
      newPendingApprovals.set(detailNo, { 
        action: 'cancel', 
        userId 
      });
      
      return { 
        approvedDetails: newApprovedDetails,
        pendingApprovals: newPendingApprovals,
      };
    });
  },

  localCancelMultipleApprovals: (detailNos: string[], userId: string) => {
    set(state => {
      const newApprovedDetails = new Map(state.approvedDetails);
      const newPendingApprovals = new Map(state.pendingApprovals);
      
      // 各明細を処理
      for (const detailNo of detailNos) {
        newApprovedDetails.delete(detailNo);
        newPendingApprovals.set(detailNo, { 
          action: 'cancel', 
          userId 
        });
      }
      
      return { 
        approvedDetails: newApprovedDetails,
        pendingApprovals: newPendingApprovals,
      };
    });
  },

  // 未同期の承認状態をサーバーに送信
  syncPendingApprovals: async (progressCallback?: (current: number, total: number) => void) => {
    const { taskId, pendingApprovals, isOfflineMode } = get();
    if (!taskId || pendingApprovals.size === 0) return true;
    
    // オフラインモードの場合は同期をスキップして成功を返す
    if (isOfflineMode) {
      console.log('オフラインモード: 同期をスキップします');
      return true;
    }

    try {
      set({ isSyncing: true, error: null, networkError: null });
      
      // 未同期リストを配列に変換
      const pendingList = Array.from(pendingApprovals.entries());
      
      // 順次処理
      for (let i = 0; i < pendingList.length; i++) {
        const [detailNo, { action, userId, detail }] = pendingList[i];
        try {
          if (action === 'approve') {
            await documentApi.approveDetail(taskId, detailNo, userId, detail);
          } else {
            await documentApi.cancelApproval(taskId, detailNo, userId);
          }
          
          // 処理済みの項目を未同期リストから削除
          set(state => {
            const newPendingApprovals = new Map(state.pendingApprovals);
            newPendingApprovals.delete(detailNo);
            return { pendingApprovals: newPendingApprovals };
          });
          
          // 進捗コールバックを呼び出す
          if (progressCallback) {
            progressCallback(i + 1, pendingList.length);
          }
        } catch (error) {
          console.error(`明細 ${detailNo} の同期に失敗しました:`, error);
          // 個別のエラーは記録するが、処理は続行
          // 失敗した項目は pendingApprovals に残るので、次回の同期で再試行される
        }
      }
      
      // 同期が完了したらローカルストレージに保存
      get().saveToLocalStorage();
      
      set({ isSyncing: false });
      return true;
    } catch (error) {
      console.error('同期処理全体が失敗しました:', error);
      
      // ネットワークエラーの場合はオフラインモードを提案
      const errorMessage = error instanceof Error ? error.message : '同期に失敗しました';
      const isNetworkError = 
        errorMessage.includes('network') || 
        errorMessage.includes('Failed to fetch') || 
        errorMessage.includes('getaddrinfo failed') ||
        errorMessage.includes('ECONNREFUSED');
      
      set({ 
        isSyncing: false,
        error: errorMessage,
        networkError: isNetworkError ? errorMessage : null
      });
      
      return false;
    }
  },

  // オフラインモードの設定
  setOfflineMode: (enabled: boolean) => {
    set({ isOfflineMode: enabled });
    
    // オフラインモードを有効にした場合は、現在の状態をローカルストレージに保存
    if (enabled) {
      get().saveToLocalStorage();
    }
  },
  
  // 現在の状態をローカルストレージに保存
  saveToLocalStorage: () => {
    const { 
      taskId, 
      document, 
      approvedDetails, 
      editedDetails, 
      pendingApprovals 
    } = get();
    
    if (!taskId) return;
    
    try {
      // Map型はJSONに直接シリアライズできないので、配列に変換
      const data = {
        taskId,
        document,
        approvedDetails: Array.from(approvedDetails.entries()),
        editedDetails: Array.from(editedDetails.entries()),
        pendingApprovals: Array.from(pendingApprovals.entries()),
        timestamp: new Date().toISOString()
      };
      
      localStorage.setItem(`document_state_${taskId}`, JSON.stringify(data));
      console.log('状態をローカルストレージに保存しました');
    } catch (error) {
      console.error('ローカルストレージへの保存に失敗しました:', error);
    }
  },
  
  // ローカルストレージから状態を読み込み
  loadFromLocalStorage: () => {
    const { taskId } = get();
    if (!taskId) return;
    
    try {
      const storedData = localStorage.getItem(`document_state_${taskId}`);
      if (!storedData) return;
      
      const data = JSON.parse(storedData);
      
      // 保存されたデータが現在のタスクIDと一致するか確認
      if (data.taskId !== taskId) return;
      
      set({
        document: data.document,
        approvedDetails: new Map(data.approvedDetails),
        editedDetails: new Map(data.editedDetails),
        pendingApprovals: new Map(data.pendingApprovals)
      });
      
      console.log('ローカルストレージから状態を読み込みました');
    } catch (error) {
      console.error('ローカルストレージからの読み込みに失敗しました:', error);
    }
  },
}));
