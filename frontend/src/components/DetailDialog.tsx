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
  TextField,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import { useDocumentStore } from '../store/documentStore';
import { documentApi, DetailWithCustomer, StockInfo, QuantityInfo } from '../services/api';

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

const EditableCell = styled(TableCell)(({ theme }) => ({
  '&:hover': {
    backgroundColor: alpha(theme.palette.primary.main, 0.04),
    cursor: 'pointer',
  },
  '&.editable': {
    backgroundColor: alpha(theme.palette.primary.main, 0.08),
    borderLeft: `2px solid ${theme.palette.primary.main}`,
  },
  padding: '4px',  // セルのパディングを調整
}));

const StyledTextField = styled(TextField)({
  '& .MuiInputBase-root': {
    height: '28px',  // 高さを小さく
    minHeight: '28px',
  },
  '& .MuiOutlinedInput-input': {
    padding: '4px 8px',  // パディングを調整
    fontSize: '0.875rem',  // フォントサイズを調整
  },
  '& .MuiOutlinedInput-notchedOutline': {
    borderRadius: '2px',  // 角を小さく
  },
  margin: 0,  // マージンを削除
});

const FixedImageSection = styled('div')({
  position: 'sticky',
  top: 0,
  backgroundColor: '#fff',
  zIndex: 1,
  paddingBottom: '16px',
  borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
});

const ScrollableContent = styled('div')({
  overflowY: 'auto',
  flex: 1,  // 利用可能な空間全体を使用
  minHeight: 0, // これが重要：flexboxでスクロールを正しく機能させるため
  '& > div': {  // Box要素のスタイル
    minHeight: '100%',  // 最小の高さを100%に設定
    paddingBottom: '400px',  // 下部に余白を大きく追加してスクロールを可能にする
  }
});


// 仮のユーザーID（実際の認証システムから取得する）
const CURRENT_USER = "user123";

interface DetailDialogProps {
  open: boolean;
  onClose: () => void;
}

type NestedKeyOf<T> = {
  [K in keyof T & (string | number)]: T[K] extends object
    ? `${K}.${NestedKeyOf<T[K]>}`
    : K;
}[keyof T & (string | number)];

export const DetailDialog: React.FC<DetailDialogProps> = ({ open, onClose }) => {
  const { 
    selectedDetail, 
    taskId,
    approveDetail, 
    approvedDetails, 
    getNextUnapprovedDetail,
    cancelApproval,
    selectDetail,
    updateDetail,
    editedDetails,
    resetEditedDetail,
  } = useDocumentStore();
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [editMode, setEditMode] = useState(false);

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
  const editedDetail = editedDetails.get(selectedDetail.no);
  const displayDetail = editedDetail || selectedDetail;

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

  const handleFieldChange = (path: string, value: string | number) => {
    const pathParts = path.split('.');
    const updatedDetail = { ...displayDetail };
    let current: any = updatedDetail;
    
    for (let i = 0; i < pathParts.length - 1; i++) {
      current = current[pathParts[i]];
    }
    current[pathParts[pathParts.length - 1]] = value;
    
    updateDetail(selectedDetail.no, updatedDetail);
  };

  const renderEditableCell = (path: string, value: string | number, type: 'text' | 'number' = 'text') => {
    if (!editMode) {
      return type === 'number' ? formatCurrency(value) : value;
    }

    return (
      <StyledTextField
        fullWidth
        type={type}
        value={value}
        onChange={(e) => handleFieldChange(path, e.target.value)}
      />
    );
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: {
          maxHeight: '90vh',
          height: '90vh',
          display: 'flex',
          flexDirection: 'column',
          ...(approvalInfo && {
            backgroundColor: alpha('#4caf50', 0.05),
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
          flex: '0 0 auto', // 固定サイズ
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
          {editedDetails.has(selectedDetail.no) && (
            <Chip
              label="編集済み"
              color="warning"
              size="small"
            />
          )}
          {!isApproved && (
            <Button
              variant="outlined"
              color={editMode ? "primary" : "inherit"}
              startIcon={editMode ? <SaveIcon /> : <EditIcon />}
              onClick={() => setEditMode(!editMode)}
              sx={{ ml: 2 }}
            >
              {editMode ? "編集を完了" : "編集する"}
            </Button>
          )}
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden', height: '100%', flex: 1 }}>
        <FixedImageSection>
          <Box p={3}>
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
          </Box>
        </FixedImageSection>

        <ScrollableContent>
          <Box p={1}>
            <Grid container spacing={0} direction="column">
              {/* 基本情報 */}
              <Grid item xs={12} sx={{ mt: 0.5 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ mb: 0.5 }}>
                  基本情報
                </Typography>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell component="th" sx={{ width: '15%' }}>取引先コード</TableCell>
                        <TableCell>{displayDetail.customer_code}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell component="th">取引先名</TableCell>
                        <TableCell>{displayDetail.customer_name}</TableCell>
                      </TableRow>
                      <TableRow>
                        <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                          <EditableCell component="th" className={editMode ? 'editable' : ''}>商品名</EditableCell>
                        </Tooltip>
                        <EditableCell className={editMode ? 'editable' : ''}>
                          {renderEditableCell('description', displayDetail.description)}
                        </EditableCell>
                      </TableRow>
                      <TableRow>
                        <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                          <EditableCell component="th" className={editMode ? 'editable' : ''}>金額</EditableCell>
                        </Tooltip>
                        <EditableCell className={editMode ? 'editable' : ''}>
                          {renderEditableCell('amount', displayDetail.amount, 'number')}
                        </EditableCell>
                      </TableRow>
                      <TableRow>
                        <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                          <EditableCell component="th" className={editMode ? 'editable' : ''}>税率</EditableCell>
                        </Tooltip>
                        <EditableCell className={editMode ? 'editable' : ''}>
                          {renderEditableCell('tax_rate', displayDetail.tax_rate)}
                        </EditableCell>
                      </TableRow>
                      {displayDetail.date_range && (
                        <TableRow>
                          <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                            <EditableCell component="th" className={editMode ? 'editable' : ''}>期間</EditableCell>
                          </Tooltip>
                          <EditableCell className={editMode ? 'editable' : ''}>
                            {renderEditableCell('date_range', displayDetail.date_range)}
                          </EditableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>

              {displayDetail.stock_info && (
                <Grid item xs={12} sx={{ mt: 0.5 }}>
                  <Typography variant="subtitle1" gutterBottom sx={{ mb: 0.5 }}>
                    在庫情報
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                            <EditableCell component="th" sx={{ width: '15%' }} className={editMode ? 'editable' : ''}>繰越</EditableCell>
                          </Tooltip>
                          <EditableCell className={editMode ? 'editable' : ''}>
                            {renderEditableCell('stock_info.carryover', displayDetail.stock_info.carryover, 'number')}
                          </EditableCell>
                        </TableRow>
                        <TableRow>
                          <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                            <EditableCell component="th" sx={{ width: '15%' }} className={editMode ? 'editable' : ''}>入庫</EditableCell>
                          </Tooltip>
                          <EditableCell className={editMode ? 'editable' : ''}>
                            {renderEditableCell('stock_info.incoming', displayDetail.stock_info.incoming, 'number')}
                          </EditableCell>
                        </TableRow>
                        <TableRow>
                          <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                            <EditableCell component="th" sx={{ width: '15%' }} className={editMode ? 'editable' : ''}>出庫</EditableCell>
                          </Tooltip>
                          <EditableCell className={editMode ? 'editable' : ''}>
                            {renderEditableCell('stock_info.outgoing', displayDetail.stock_info.outgoing, 'number')}
                          </EditableCell>
                        </TableRow>
                        <TableRow>
                          <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                            <EditableCell component="th" sx={{ width: '15%' }} className={editMode ? 'editable' : ''}>残高</EditableCell>
                          </Tooltip>
                          <EditableCell className={editMode ? 'editable' : ''}>
                            {renderEditableCell('stock_info.remaining', displayDetail.stock_info.remaining, 'number')}
                          </EditableCell>
                        </TableRow>
                        <TableRow>
                          <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                            <EditableCell component="th" sx={{ width: '15%' }} className={editMode ? 'editable' : ''}>単価</EditableCell>
                          </Tooltip>
                          <EditableCell className={editMode ? 'editable' : ''}>
                            {renderEditableCell('stock_info.unit_price', displayDetail.stock_info.unit_price, 'number')}
                          </EditableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              )}

              {displayDetail.quantity_info && (
                <Grid item xs={12} sx={{ mt: 0.5 }}>
                  <Typography variant="subtitle1" gutterBottom sx={{ mb: 0.5 }}>
                    数量情報
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                            <EditableCell component="th" sx={{ width: '15%' }} className={editMode ? 'editable' : ''}>数量</EditableCell>
                          </Tooltip>
                          <EditableCell className={editMode ? 'editable' : ''}>
                            {renderEditableCell('quantity_info.quantity', displayDetail.quantity_info.quantity, 'number')}
                          </EditableCell>
                        </TableRow>
                        {displayDetail.quantity_info.unit_price && (
                          <TableRow>
                            <Tooltip title={editMode ? "クリックして編集" : ""} arrow>
                              <EditableCell component="th" sx={{ width: '15%' }} className={editMode ? 'editable' : ''}>単価</EditableCell>
                            </Tooltip>
                            <EditableCell className={editMode ? 'editable' : ''}>
                              {renderEditableCell('quantity_info.unit_price', displayDetail.quantity_info.unit_price, 'number')}
                            </EditableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              )}
            </Grid>
          </Box>
        </ScrollableContent>
      </DialogContent>

      <DialogActions 
        sx={{ 
          gap: 1, 
          borderTop: 1, 
          borderColor: 'divider', 
          p: 2,
          flex: '0 0 auto', // 固定サイズ
        }}
      >
        <Box sx={{ display: 'flex', gap: 1, flex: 1 }}>
          {/* 編集モードのボタン */}
          {editMode && (
            <Button
              variant="outlined"
              color="inherit"
              onClick={() => {
                setEditMode(false);
                resetEditedDetail(selectedDetail.no);
              }}
              startIcon={<CancelIcon />}
            >
              キャンセル
            </Button>
          )}
          {/* 承認ボタン */}
          {!isApproved && !editMode && (
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
