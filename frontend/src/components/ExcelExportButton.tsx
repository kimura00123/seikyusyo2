import React, { useState, useMemo } from 'react';
import { Button, CircularProgress, Snackbar, Alert } from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { useDocumentStore } from '../store/documentStore';
import { documentApi } from '../services/api';

export const ExcelExportButton: React.FC = () => {
  const { taskId, document: documentData, approvedDetails, editedDetails } = useDocumentStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // すべての明細が承認済みかチェック
  const isAllApproved = useMemo(() => {
    if (!documentData) return false;
    
    const totalDetails = documentData.customers.reduce(
      (total, customer) => total + customer.entries.length,
      0
    );
    
    return approvedDetails.size === totalDetails;
  }, [documentData, approvedDetails]);

  const handleExport = async () => {
    if (!taskId) return;

    try {
      setLoading(true);
      setError(null);

      // 編集された値がある場合は、それを含めてエクセル出力
      const blob = await documentApi.downloadExcel(taskId, editedDetails);
      
      // ファイル名を生成（現在の日時を含める）
      const date = new Date().toISOString().split('T')[0];
      const filename = `invoice_data_${date}.xlsx`;

      // ファイル保存ダイアログを表示（showSaveFilePickerが利用可能な場合）
      if (typeof window !== 'undefined' && 'showSaveFilePicker' in window) {
        try {
          const handle = await window.showSaveFilePicker({
            suggestedName: filename,
            types: [{
              description: 'Excel ファイル',
              accept: {
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
              }
            }]
          });

          // ファイルを保存
          const writable = await handle.createWritable();
          await writable.write(blob);
          await writable.close();
        } catch (err) {
          const error = err as Error;
          if (error.name !== 'AbortError') {
            // ユーザーがキャンセルした場合以外はフォールバック処理を実行
            throw error;
          }
        }
      } else {
        // フォールバック: 従来のダウンロード方法
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();

        // クリーンアップ
        link.parentNode?.removeChild(link);
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      const error = err as Error;
      console.error('エクセルファイルのダウンロードに失敗しました:', error);
      setError('エクセルファイルのダウンロードに失敗しました。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        variant="contained"
        color="primary"
        onClick={handleExport}
        disabled={loading || !taskId || !isAllApproved}
        startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <FileDownloadIcon />}
      >
        エクセル出力
      </Button>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setError(null)} severity="error">
          {error}
        </Alert>
      </Snackbar>
    </>
  );
};
