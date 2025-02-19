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
  styled
} from '@mui/material';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import { useDocumentStore } from '../store/documentStore';
import { documentApi } from '../services/api';

interface DetailDialogProps {
  open: boolean;
  onClose: () => void;
}

export const DetailDialog: React.FC<DetailDialogProps> = ({ open, onClose }) => {
  const { selectedDetail, taskId } = useDocumentStore();
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [zoom, setZoom] = useState(1);

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

  if (!selectedDetail) return null;

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
        }
      }}
    >
      <DialogTitle>
        明細詳細：{selectedDetail.no}
      </DialogTitle>
      <DialogContent>
        <Grid container spacing={3} direction="column">
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

          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              基本情報
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell component="th">取引先コード</TableCell>
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
                        <TableCell component="th">繰越</TableCell>
                        <TableCell align="right">{selectedDetail.stock_info.carryover}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th">入庫</TableCell>
                        <TableCell align="right">{selectedDetail.stock_info.incoming}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th">出庫</TableCell>
                        <TableCell align="right">{selectedDetail.stock_info.outgoing}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th">残高</TableCell>
                        <TableCell align="right">{selectedDetail.stock_info.remaining}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th">単価</TableCell>
                        <TableCell align="right">
                          {formatCurrency(selectedDetail.stock_info.unit_price)}
                        </TableCell>
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
                        <TableCell component="th">数量</TableCell>
                        <TableCell align="right">{selectedDetail.quantity_info.quantity}</TableCell>
                      </TableRow>
                      {selectedDetail.quantity_info.unit_price && (
                        <TableRow>
                          <TableCell component="th">単価</TableCell>
                          <TableCell align="right">
                            {formatCurrency(selectedDetail.quantity_info.unit_price)}
                          </TableCell>
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
      <DialogActions>
        <Button onClick={onClose}>閉じる</Button>
      </DialogActions>
    </Dialog>
  );
};
