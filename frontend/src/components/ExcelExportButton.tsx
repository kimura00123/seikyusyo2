import React, { useState, useMemo, useEffect } from 'react';
import { 
  Button, 
  CircularProgress, 
  Snackbar, 
  Alert, 
  Backdrop, 
  Typography, 
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Chip
} from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import CloudOffIcon from '@mui/icons-material/CloudOff';
import SyncIcon from '@mui/icons-material/Sync';
import { useDocumentStore } from '../store/documentStore';
import { documentApi } from '../services/api';

export const ExcelExportButton: React.FC = () => {
  const { 
    taskId, 
    document: documentData, 
    approvedDetails, 
    editedDetails, 
    pendingApprovals, 
    syncPendingApprovals,
    isSyncing,
    isOfflineMode,
    networkError,
    setOfflineMode,
    saveToLocalStorage
  } = useDocumentStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [showNetworkErrorDialog, setShowNetworkErrorDialog] = useState(false);
  const [pendingDownload, setPendingDownload] = useState<{
    blob: Blob;
    filename: string;
  } | null>(null);

  // ネットワークエラーが発生したらダイアログを表示
  useEffect(() => {
    if (networkError) {
      setShowNetworkErrorDialog(true);
    }
  }, [networkError]);

  // 定期的に状態をローカルストレージに保存
  useEffect(() => {
    if (taskId) {
      const saveInterval = setInterval(() => {
        saveToLocalStorage();
      }, 60000); // 1分ごとに保存
      
      return () => clearInterval(saveInterval);
    }
  }, [taskId, saveToLocalStorage]);

  // すべての明細が承認済みかチェック
  const isAllApproved = useMemo(() => {
    if (!documentData) return false;
    
    const totalDetails = documentData.customers.reduce(
      (total, customer) => total + customer.entries.length,
      0
    );
    
    return approvedDetails.size === totalDetails;
  }, [documentData, approvedDetails]);

  // 未同期の承認状態があるかチェック
  const hasPendingApprovals = useMemo(() => {
    return pendingApprovals.size > 0;
  }, [pendingApprovals]);

  const handleExport = async () => {
    if (!taskId) return;

    try {
      setLoading(true);
      setError(null);
      
      console.log('===== handleExport開始 =====');
      console.log('taskId:', taskId);
      console.log('isOfflineMode:', isOfflineMode);
      console.log('hasPendingApprovals:', hasPendingApprovals);
      console.log('pendingApprovals数:', pendingApprovals.size);

      // オフラインモードでない場合のみ同期を試みる
      if (!isOfflineMode && hasPendingApprovals) {
        console.log('承認状態の同期を開始します');
        setSyncMessage(`承認状態を同期中です (0/${pendingApprovals.size})...`);
        
        // 同期処理を実行
        const syncSuccess = await syncPendingApprovals((current, total) => {
          console.log(`承認状態の同期進捗: ${current}/${total}`);
          setSyncMessage(`承認状態を同期中です (${current}/${total})...`);
        });
        
        console.log('承認状態の同期結果:', syncSuccess);
        
        if (!syncSuccess) {
          // 同期に失敗した場合はオフラインモードを提案するダイアログを表示
          console.log('承認状態の同期に失敗しました');
          setShowNetworkErrorDialog(true);
          throw new Error('承認状態の同期に失敗しました。再試行するか、オフラインモードで続行してください。');
        }
        
        console.log('承認状態の同期が完了しました');
        setSyncMessage(null);
      } else {
        console.log('承認状態の同期をスキップします', 
          isOfflineMode ? '(オフラインモード)' : '(未同期の承認状態なし)');
      }

      // オフラインモードの場合はローカルでの処理のみ
      if (isOfflineMode) {
        console.log('オフラインモード: ローカルストレージに保存します');
        // ローカルストレージに保存
        saveToLocalStorage();
        
        // オフラインモードではExcel出力はできないことを通知
        setError('オフラインモードではExcel出力ができません。ネットワーク接続を確認してオンラインモードに切り替えてください。');
        setLoading(false);
        return;
      }

      console.log('エクセル出力を開始します');
      // 編集された値がある場合は、それを含めてエクセル出力
      const blob = await documentApi.downloadExcel(taskId, editedDetails);
      console.log('エクセル出力が完了しました');
      
      // レスポンスの検証
      if (!blob || blob.size === 0) {
        console.error('サーバーから空のファイルが返されました');
        throw new Error('サーバーから空のファイルが返されました');
      }
      
      // Content-Typeの確認
      const contentType = blob.type;
      console.log('Content-Type:', contentType);
      
      if (!contentType.includes('spreadsheetml') && !contentType.includes('excel') && !contentType.includes('octet-stream')) {
        console.error('予期しないContent-Type:', contentType);
        // エラーレスポンスの場合はJSONとして読み取り
        if (contentType.includes('json')) {
          const text = await blob.text();
          try {
            const errorData = JSON.parse(text);
            throw new Error(errorData.detail || 'サーバーエラーが発生しました');
          } catch (parseError) {
            throw new Error(`サーバーエラー: ${text}`);
          }
        }
        throw new Error(`不正なファイル形式: ${contentType}`);
      }
      
      // ファイル名の決定（優先順位: サーバー提供のファイル名 > PDFファイル名 > デフォルト名）
      let filename = '';
      
      // 1. サーバーから提供されたファイル名があれば使用
      if ((blob as any).filename) {
        filename = (blob as any).filename;
        console.log('サーバーから提供されたファイル名を使用:', filename);
      } 
      // 2. PDFファイル名から生成
      else if (documentData && documentData.pdf_filename) {
        // 拡張子を.xlsxに変更
        const baseFilename = documentData.pdf_filename.replace(/\.[^/.]+$/, '');
        filename = `${baseFilename}.xlsx`;
        console.log('オリジナルPDFファイル名からExcelファイル名を生成:', filename);
      } 
      // 3. デフォルト名
      else {
        const date = new Date().toISOString().split('T')[0];
        filename = `invoice_data_${date}.xlsx`;
        console.log('デフォルトのExcelファイル名を使用:', filename);
      }

      let downloadSucceeded = false;

      // File System Access APIが利用可能な場合
      if (typeof window !== 'undefined' && 'showSaveFilePicker' in window) {
        console.log('File System Access APIを使用してファイル保存ダイアログを表示します');
        // ダウンロード情報を状態に保存し、ダイアログを表示
        setPendingDownload({ blob, filename });
        downloadSucceeded = true; // 後続のフォールバック処理をスキップ
      }

      // showSaveFilePickerが失敗または利用不可の場合はフォールバック方式を使用
      if (!downloadSucceeded) {
        console.log('従来のダウンロード方法を使用します');
        // フォールバック: 従来のダウンロード方法
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        
        // クリックイベントを確実に発火させる
        try {
          console.log('ダウンロードリンクをクリックします');
          const clickEvent = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true
          });
          const clickResult = link.dispatchEvent(clickEvent);
          console.log('クリックイベントの結果:', clickResult);
        } catch (e) {
          // 古いブラウザ向けのフォールバック
          console.warn('MouseEventの作成に失敗、直接clickメソッドを使用します:', e);
          link.click();
        }

        // クリーンアップ（少し遅延させる）
        setTimeout(() => {
          console.log('ダウンロードリンクをクリーンアップします');
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }, 500); // 遅延時間を増やす
      }
      
      console.log('===== handleExport終了 =====');
    } catch (err) {
      const error = err as Error;
      console.error('エクセルファイルのダウンロードに失敗しました:', error);
      setError('エクセルファイルのダウンロードに失敗しました。');
    } finally {
      setLoading(false);
      setSyncMessage(null);
    }
  };

  // ファイル保存ダイアログでの保存処理
  const handleSaveFile = async () => {
    if (!pendingDownload) return;
    
    const { blob, filename } = pendingDownload;
    
    console.log('===== handleSaveFile開始 =====');
    console.log('filename:', filename);
    console.log('blob size:', blob.size);
    console.log('pendingApprovals数:', pendingApprovals.size);
    
    try {
      // ユーザージェスチャーのコンテキスト内で実行
      console.log('showSaveFilePickerを呼び出します');
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
      console.log('ファイルの書き込みを開始します');
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
      console.log('ファイルの保存に成功しました:', filename);
      
      // 承認処理の状態を確認
      console.log('承認処理の状態確認:');
      console.log('- pendingApprovals数:', pendingApprovals.size);
      console.log('- isOfflineMode:', isOfflineMode);
      
      // 未同期の承認状態があり、オフラインモードでない場合は同期を実行
      if (pendingApprovals.size > 0 && !isOfflineMode) {
        console.log('ファイル保存後に承認状態の同期を開始します');
        setSyncMessage(`承認状態を同期中です (0/${pendingApprovals.size})...`);
        
        try {
          // 同期処理を実行
          const syncSuccess = await syncPendingApprovals((current, total) => {
            console.log(`承認状態の同期進捗: ${current}/${total}`);
            setSyncMessage(`承認状態を同期中です (${current}/${total})...`);
          });
          
          console.log('ファイル保存後の承認状態の同期結果:', syncSuccess);
          
          if (!syncSuccess) {
            console.log('ファイル保存後の承認状態の同期に失敗しました');
            setShowNetworkErrorDialog(true);
          } else {
            console.log('ファイル保存後の承認状態の同期が完了しました');
          }
        } catch (syncError) {
          console.error('ファイル保存後の承認状態の同期でエラーが発生しました:', syncError);
          setShowNetworkErrorDialog(true);
        } finally {
          setSyncMessage(null);
        }
      } else {
        console.log('ファイル保存後の承認状態の同期をスキップします', 
          isOfflineMode ? '(オフラインモード)' : '(未同期の承認状態なし)');
      }
      
      // 処理完了後に状態をクリア
      setPendingDownload(null);
      console.log('===== handleSaveFile終了 =====');
    } catch (err) {
      const error = err as Error;
      console.log('ファイル保存中にエラーが発生しました:', error);
      
      if (error.name !== 'AbortError') {
        // SecurityErrorの場合はフォールバック処理を実行
        console.warn('File System Access APIでの保存に失敗、フォールバック方式を使用します:', error);
        // フォールバック処理を実行
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        
        try {
          console.log('ダウンロードリンクをクリックします');
          const clickEvent = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true
          });
          const clickResult = link.dispatchEvent(clickEvent);
          console.log('クリックイベントの結果:', clickResult);
        } catch (e) {
          console.warn('MouseEventの作成に失敗、直接clickメソッドを使用します:', e);
          link.click();
        }
        
        // 未同期の承認状態があり、オフラインモードでない場合は同期を実行
        if (pendingApprovals.size > 0 && !isOfflineMode) {
          console.log('フォールバック後に承認状態の同期を開始します');
          setTimeout(async () => {
            setSyncMessage(`承認状態を同期中です (0/${pendingApprovals.size})...`);
            
            try {
              // 同期処理を実行
              const syncSuccess = await syncPendingApprovals((current, total) => {
                console.log(`承認状態の同期進捗: ${current}/${total}`);
                setSyncMessage(`承認状態を同期中です (${current}/${total})...`);
              });
              
              console.log('フォールバック後の承認状態の同期結果:', syncSuccess);
              
              if (!syncSuccess) {
                console.log('フォールバック後の承認状態の同期に失敗しました');
                setShowNetworkErrorDialog(true);
              } else {
                console.log('フォールバック後の承認状態の同期が完了しました');
              }
            } catch (syncError) {
              console.error('フォールバック後の承認状態の同期でエラーが発生しました:', syncError);
              setShowNetworkErrorDialog(true);
            } finally {
              setSyncMessage(null);
            }
          }, 1000); // ダウンロード完了後に実行
        }
        
        setTimeout(() => {
          console.log('ダウンロードリンクをクリーンアップします');
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }, 500);
      } else {
        console.log('ユーザーがファイル保存をキャンセルしました');
      }
      
      // 処理完了後に状態をクリア
      setPendingDownload(null);
      console.log('===== handleSaveFile終了（エラーまたはキャンセル） =====');
    }
  };

  // 同期を試みる
  const handleTrySync = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // オフラインモードを解除
      setOfflineMode(false);
      
      // 同期処理を実行
      const syncSuccess = await syncPendingApprovals();
      
      if (syncSuccess) {
        setShowNetworkErrorDialog(false);
      } else {
        // 同期に失敗した場合はエラーメッセージを表示
        setError('同期に失敗しました。ネットワーク接続を確認してください。');
      }
    } catch (error) {
      console.error('同期に失敗しました:', error);
      setError('同期に失敗しました。ネットワーク接続を確認してください。');
    } finally {
      setLoading(false);
    }
  };

  // オフラインモードに切り替え
  const handleEnableOfflineMode = () => {
    setOfflineMode(true);
    setShowNetworkErrorDialog(false);
  };

  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleExport}
          disabled={loading || !taskId || !isAllApproved || isSyncing}
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <FileDownloadIcon />}
        >
          エクセル出力
        </Button>
        
        {isOfflineMode && (
          <Chip
            icon={<CloudOffIcon />}
            label="オフラインモード"
            color="warning"
            variant="outlined"
            onClick={handleTrySync}
          />
        )}
        
        {hasPendingApprovals && !isOfflineMode && (
          <Chip
            icon={<SyncIcon />}
            label={`未同期の承認: ${pendingApprovals.size}件`}
            color="info"
            variant="outlined"
            onClick={() => syncPendingApprovals()}
          />
        )}
      </Box>

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

      {/* 同期中のバックドロップ */}
      <Backdrop
        sx={{ color: '#fff', zIndex: (theme) => theme.zIndex.drawer + 1 }}
        open={!!syncMessage || isSyncing}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress color="inherit" />
          <Typography sx={{ mt: 2 }}>
            {syncMessage || '処理中...'}
          </Typography>
        </Box>
      </Backdrop>

      {/* ネットワークエラーダイアログ */}
      <Dialog
        open={showNetworkErrorDialog}
        onClose={() => setShowNetworkErrorDialog(false)}
      >
        <DialogTitle>ネットワーク接続エラー</DialogTitle>
        <DialogContent>
          <DialogContentText>
            サーバーに接続できません。ネットワーク接続を確認してください。
            <br /><br />
            {networkError && <strong>{networkError}</strong>}
            <br /><br />
            オフラインモードに切り替えると、ローカルでの作業を続行できます。
            ただし、サーバーとの同期は行われず、Excel出力はできなくなります。
            ネットワーク接続が回復したら、同期を試みることができます。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleTrySync} color="primary" startIcon={<SyncIcon />}>
            同期を試みる
          </Button>
          <Button onClick={handleEnableOfflineMode} color="warning" startIcon={<CloudOffIcon />}>
            オフラインモードに切り替え
          </Button>
          <Button onClick={() => setShowNetworkErrorDialog(false)} color="inherit">
            閉じる
          </Button>
        </DialogActions>
      </Dialog>

      {/* ファイル保存ダイアログ */}
      <Dialog
        open={!!pendingDownload}
        onClose={() => setPendingDownload(null)}
      >
        <DialogTitle>ファイルの保存</DialogTitle>
        <DialogContent>
          <DialogContentText>
            「ファイルを保存」ボタンをクリックして、Excelファイルを保存してください。
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleSaveFile} color="primary">
            ファイルを保存
          </Button>
          <Button onClick={() => setPendingDownload(null)} color="inherit">
            キャンセル
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};
