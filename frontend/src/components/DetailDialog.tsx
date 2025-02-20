import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  Typography,
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  CircularProgress,
  IconButton,
  styled,
  Chip,
  Tooltip,
  alpha,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import { useDocumentStore } from '../store/documentStore';
import { documentApi } from '../services/api';

// スタイル付きコンポーネント
const ImageContainer = styled('div')({
  width: '100%',
  height: '200px',  // 画像表示エリアの高さを調整
  overflow: 'auto',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: '#f5f5f5',
  position: 'relative',
});

const ZoomControls = styled('div')({
  position: 'absolute',
  top: '10px',
  right: '10px',
  display: 'flex',
  gap: '8px',
  backgroundColor: 'rgba(255, 255, 255, 0.8)',
  padding: '4px',
  borderRadius: '4px',
  zIndex: 1,
});

const StyledImage = styled('img')({
  width: '100%',  // 常に親要素の幅いっぱいに表示
  height: 'auto',
  objectFit: 'contain',
  transition: 'transform 0.2s ease',
  transformOrigin: 'center center',  // 中心を基準にズーム
});

// 仮のユーザーID（実際の認証システムから取得する）
const CURRENT_USER = "user123";

interface DetailDialogProps {
  open: boolean;
  onClose: () => void;
}

export const DetailDialog: React.FC<DetailDialogProps> = ({ open, onClose }) => {
  const { 
    selectedDetail, 
    taskId,
    approveDetail, 
    approvedDetails, 
    getNextUnapprovedDetail,
    cancelApproval,
    selectDetail,
  } = useDocumentStore();
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [zoom, setZoom] = useState(1);

  // 画像の読み込み
  useEffect(() => {
    const loadImage = async () => {
      if (!taskId || !selectedDetail) return;

      try {
        setLoading(true);
        const blob = await documentApi.getDetailImage(taskId, selectedDetail.no);
        // 古いURLを解放してから新しいURLを設定
        if (imageUrl) {
          URL.revokeObjectURL(imageUrl);
        }
        const url = URL.createObjectURL(blob);
        setImageUrl(url);
      } catch (error) {
        console.error('画像の読み込みに失敗しました:', error);
      } finally {
        setLoading(false);
      }
    };

    if (open && selectedDetail) {
      loadImage();
    }

    // コンポーネントのアンマウント時のみクリーンアップを実行
    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
        setImageUrl(null);
      }
    };
  }, [open, selectedDetail, taskId]); // imageUrlを依存配列から削除

  if (!selectedDetail) {
    return null;
  }

  const isApproved = approvedDetails.has(selectedDetail.no);
  const approvalInfo = isApproved ? approvedDetails.get(selectedDetail.no)! : null;

  // ズーム操作
  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev * 1.2, 3));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev * 0.8, 0.5));
  };

  const handleResetZoom = () => {
    setZoom(1);
  };

  // ホイールイベントでのズーム
  const handleWheel = (e: React.WheelEvent) => {
    if (e.ctrlKey) {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.8 : 1.2;
      setZoom(prev => Math.min(Math.max(prev * delta, 0.5), 3));
    }
  };

  const handleApprove = async () => {
    if (!selectedDetail) return;

    try {
      await approveDetail(selectedDetail.no, CURRENT_USER);
      const nextDetail = getNextUnapprovedDetail();
      if (nextDetail) {
        // 次の未承認明細に移動
        selectDetail(nextDetail);
      } else {
        // 最後の明細の場合は閉じる
        onClose();
      }
    } catch (error) {
      console.error('承認処理に失敗しました:', error);
    }
  };

  const handleCancelApproval = async () => {
    try {
      await cancelApproval(selectedDetail.no, CURRENT_USER);
      onClose();  // 承認取り消し後に自動でダイアログを閉じる
    } catch (error) {
      console.error('承認取り消しに失敗しました:', error);
    }
  };

  const handleNext = () => {
    const nextDetail = getNextUnapprovedDetail();
    if (nextDetail) {
      selectDetail(nextDetail);
    }
  };

  // キーボードショートカット
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.ctrlKey && event.key === 'Enter' && !isApproved) {
      handleApprove();
    }
  };

  const formatCurrency = (amount: string | number) => {
    const value = typeof amount === 'string' ? parseInt(amount.replace(/[^\d]/g, '')) : amount;
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY'
    }).format(value);
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: {
          maxHeight: '90vh',  // ビューポートの90%の高さまで許可
          height: '90vh',     // 固定の高さを設定
          ...(approvalInfo && {
            backgroundColor: alpha('#4caf50', 0.05),  // 承認済みの場合、背景色を変更
          })
        }
      }}
      onKeyDown={handleKeyDown}
    >
      <DialogTitle 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: 1,
          borderBottom: 1,
          borderColor: approvalInfo ? 'success.main' : 'divider',
          bgcolor: approvalInfo ? 'success.lighter' : 'inherit',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
          <Typography component="span">明細詳細：{selectedDetail.no}</Typography>
          {isApproved ? (
            <Tooltip 
              title={approvalInfo ? 
                `承認日時: ${new Date(approvalInfo.approved_at).toLocaleString()}\n承認者: ${approvalInfo.approved_by}` :
                "承認情報が見つかりません"
              }
            >
              <Chip
                icon={<CheckCircleIcon />}
                label="承認済"
                color="success"
                size="small"
              />
            </Tooltip>
          ) : (
            <Chip
              label="未承認"
              size="small"
              color="default"
            />
          )}
        </Box>
      </DialogTitle>

      <DialogContent>
        <Grid container spacing={3} direction="column">
          {/* 画像表示エリア */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              明細画像
            </Typography>
            <ImageContainer onWheel={handleWheel}>
              <ZoomControls>
                <IconButton onClick={handleZoomIn} size="small">
                  <ZoomInIcon />
                </IconButton>
                <IconButton onClick={handleZoomOut} size="small">
                  <ZoomOutIcon />
                </IconButton>
                <IconButton onClick={handleResetZoom} size="small">
                  <RestartAltIcon />
                </IconButton>
              </ZoomControls>
              {loading ? (
                <CircularProgress />
              ) : imageUrl ? (
                <StyledImage
                  src={imageUrl}
                  alt="明細画像"
                  style={{
                    transform: `scale(${zoom})`,
                    cursor: zoom !== 1 ? 'move' : 'default',
                  }}
                />
              ) : (
                <Typography color="text.secondary">
                  画像を読み込めませんでした
                </Typography>
              )}
            </ImageContainer>
          </Grid>

          {/* 基本情報 */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              基本情報
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell component="th" sx={{ width: '15%' }}>取引先コード</TableCell>
                    <TableCell>{selectedDetail.customer_code}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">取引先名</TableCell>
                    <TableCell>{selectedDetail.customer_name}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">商品名</TableCell>
                    <TableCell>{selectedDetail.description}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">金額</TableCell>
                    <TableCell>{formatCurrency(selectedDetail.amount)}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell component="th">税率</TableCell>
                    <TableCell>{selectedDetail.tax_rate}</TableCell>
                  </TableRow>
                  {selectedDetail.date_range && (
                    <TableRow>
                      <TableCell component="th">期間</TableCell>
                      <TableCell>{selectedDetail.date_range}</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            {selectedDetail.stock_info && (
              <Box mt={3}>
                <Typography variant="subtitle1" gutterBottom>
                  在庫情報
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell component="th" sx={{ width: '15%' }}>繰越</TableCell>
                        <TableCell>{selectedDetail.stock_info.carryover}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th" sx={{ width: '15%' }}>入庫</TableCell>
                        <TableCell>{selectedDetail.stock_info.incoming}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th" sx={{ width: '15%' }}>出庫</TableCell>
                        <TableCell>{selectedDetail.stock_info.outgoing}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th" sx={{ width: '15%' }}>残高</TableCell>
                        <TableCell>{selectedDetail.stock_info.remaining}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th" sx={{ width: '15%' }}>単価</TableCell>
                        <TableCell>{formatCurrency(selectedDetail.stock_info.unit_price)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}

            {selectedDetail.quantity_info && (
              <Box mt={3}>
                <Typography variant="subtitle1" gutterBottom>
                  数量情報
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell component="th" sx={{ width: '15%' }}>数量</TableCell>
                        <TableCell>{selectedDetail.quantity_info.quantity}</TableCell>
                      </TableRow>
                      {selectedDetail.quantity_info.unit_price && (
                        <TableRow>
                          <TableCell component="th" sx={{ width: '15%' }}>単価</TableCell>
                          <TableCell>{formatCurrency(selectedDetail.quantity_info.unit_price)}</TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
          </Grid>
        </Grid>
      </DialogContent>

      <DialogActions sx={{ gap: 1, borderTop: 1, borderColor: 'divider', p: 2 }}>
        <Box sx={{ display: 'flex', gap: 1, flex: 1 }}>
          {/* 承認ボタン */}
          {!isApproved && (
            <Button
              startIcon={<CheckCircleIcon />}
              onClick={handleApprove}
              variant="contained"
              color="success"
            >
              承認（Ctrl+Enter）
            </Button>
          )}
          {/* 承認取り消しボタン */}
          {isApproved && (
            <Button
              variant="outlined"
              color="error"
              onClick={handleCancelApproval}
            >
              承認を取り消し
            </Button>
          )}
        </Box>
        <Button 
          onClick={onClose}
          variant={isApproved ? "contained" : "outlined"}
          color={isApproved ? "primary" : "inherit"}
        >
          閉じる
        </Button>
      </DialogActions>
    </Dialog>
  );
};
