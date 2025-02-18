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
  CircularProgress
} from '@mui/material';
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

  useEffect(() => {
    const loadImage = async () => {
      if (!taskId || !selectedDetail) return;

      try {
        setLoading(true);
        const blob = await documentApi.getDetailImage(taskId, selectedDetail.no);
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

    return () => {
      // クリーンアップ時に画像URLを解放
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
      setImageUrl(null);
    };
  }, [open, selectedDetail, taskId, imageUrl]);

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
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        明細詳細：{selectedDetail.no}
      </DialogTitle>
      <DialogContent>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
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

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle1" gutterBottom>
              明細画像
            </Typography>
            <Paper
              variant="outlined"
              sx={{
                p: 1,
                height: '100%',
                minHeight: 200,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              {loading ? (
                <CircularProgress />
              ) : imageUrl ? (
                <img
                  src={imageUrl}
                  alt="明細画像"
                  style={{ maxWidth: '100%', maxHeight: '400px' }}
                />
              ) : (
                <Typography color="text.secondary">
                  画像を読み込めませんでした
                </Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>閉じる</Button>
      </DialogActions>
    </Dialog>
  );
};
