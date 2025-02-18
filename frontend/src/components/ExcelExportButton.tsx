import React, { useState } from 'react';
import { Button, CircularProgress } from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import { useDocumentStore } from '../store/documentStore';
import { documentApi } from '../services/api';

export const ExcelExportButton: React.FC = () => {
  const { taskId } = useDocumentStore();
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    if (!taskId) return;

    try {
      setLoading(true);
      const blob = await documentApi.downloadExcel(taskId);
      
      // ファイル名を生成（現在の日時を含める）
      const date = new Date().toISOString().split('T')[0];
      const filename = `invoice_data_${date}.xlsx`;

      // ダウンロードリンクを作成
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();

      // クリーンアップ
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('エクセルファイルのダウンロードに失敗しました:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant="contained"
      color="primary"
      onClick={handleExport}
      disabled={loading || !taskId}
      startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <FileDownloadIcon />}
    >
      エクセル出力
    </Button>
  );
};
