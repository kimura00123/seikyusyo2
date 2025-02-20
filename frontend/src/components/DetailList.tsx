import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  Chip,
  Tooltip,
  LinearProgress,
  Button,
  Checkbox,
  ToggleButtonGroup,
  ToggleButton
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useDocumentStore, DetailWithCustomer } from '../store/documentStore';
import { DetailDialog } from './DetailDialog';

type FilterType = 'all' | 'pending' | 'approved';

// 仮のユーザーID（実際の認証システムから取得する）
const CURRENT_USER = "user123";

export const DetailList: React.FC = () => {
  const { 
    document, 
    status, 
    selectDetail, 
    approvedDetails, 
    approveMultipleDetails, 
    approveAllDetails,
    cancelMultipleApprovals
  } = useDocumentStore();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedDetails, setSelectedDetails] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<FilterType>('all');

  if (status !== 'completed' || !document) {
    return null;
  }

  // すべての明細を1つの配列にフラット化
  const allDetails = document.customers.flatMap(customer => 
    customer.entries.map(entry => ({
      ...entry,
      customer_code: customer.customer_code,
      customer_name: customer.customer_name,
    }))
  );

  // フィルター適用
  const filteredDetails = allDetails.filter(detail => {
    switch (filter) {
      case 'pending':
        return !approvedDetails.has(detail.no);
      case 'approved':
        return approvedDetails.has(detail.no);
      default:
        return true;
    }
  });

  const handleDetailClick = (detail: DetailWithCustomer, event: React.MouseEvent) => {
    // チェックボックスセル内のクリックは無視
    const target = event.target as HTMLElement;
    if (target.closest('.MuiTableCell-paddingCheckbox')) {
      return;
    }

    if (event.ctrlKey) {
      // Ctrl+クリックで選択状態を切り替え
      event.preventDefault();
      setSelectedDetails(prev => {
        const newSet = new Set(prev);
        if (newSet.has(detail.no)) {
          newSet.delete(detail.no);
        } else {
          newSet.add(detail.no);
        }
        return newSet;
      });
    } else {
      // 通常クリックでダイアログを開く
      selectDetail(detail);
      setDialogOpen(true);
    }
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      // フィルター適用後の明細のみを選択対象とする
      const filteredDetailNos = filteredDetails.map(detail => detail.no);
      setSelectedDetails(new Set(filteredDetailNos));
    } else {
      setSelectedDetails(new Set());
    }
  };

  const handleBulkApprove = async () => {
    if (selectedDetails.size === 0) return;
    await approveMultipleDetails(Array.from(selectedDetails), CURRENT_USER);
    setSelectedDetails(new Set());
  };

  const handleApproveAll = async () => {
    await approveAllDetails(CURRENT_USER);
    setSelectedDetails(new Set());
  };

  const handleCancelApprovals = async () => {
    if (selectedDetails.size === 0) return;
    await cancelMultipleApprovals(Array.from(selectedDetails), CURRENT_USER);
    setSelectedDetails(new Set());
  };

  // フィルター変更ハンドラー
  const handleFilterChange = (_: React.MouseEvent<HTMLElement>, newFilter: FilterType) => {
    if (newFilter !== null) {
      setFilter(newFilter);
      // フィルター変更時に選択をクリア
      setSelectedDetails(new Set());
    }
  };

  // 承認進捗率の計算
  const progressPercentage = (approvedDetails.size / allDetails.length) * 100;

  return (
    <Box sx={{ mt: 4 }}>
      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" gutterBottom>
              明細一覧
            </Typography>
            <ToggleButtonGroup
              value={filter}
              exclusive
              onChange={handleFilterChange}
              size="small"
            >
              <ToggleButton value="all">
                すべて
              </ToggleButton>
              <ToggleButton value="pending">
                未承認のみ
              </ToggleButton>
              <ToggleButton value="approved">
                承認済みのみ
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              承認済み: {approvedDetails.size} / {allDetails.length} 件
              {filter !== 'all' && ` （${filter === 'pending' ? '未承認のみ' : '承認済みのみ'}表示中）`}
            </Typography>
            <Box sx={{ width: 200 }}>
              <LinearProgress
                variant="determinate"
                value={progressPercentage}
                color="success"
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 2 }}>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              startIcon={<CheckCircleIcon />}
              variant="contained"
              color="success"
              onClick={handleBulkApprove}
              disabled={selectedDetails.size === 0}
            >
              選択した明細を承認 ({selectedDetails.size}件)
            </Button>
            <Button
              startIcon={<CheckCircleIcon />}
              variant="outlined"
              color="success"
              onClick={handleApproveAll}
            >
              全件承認
            </Button>
          </Box>
          {/* 承認取り消しボタン */}
          <Button
            variant="outlined"
            color="error"
            onClick={handleCancelApprovals}
            disabled={selectedDetails.size === 0 || 
              // 選択された明細のうち、承認済みのものがない場合は無効化
              !Array.from(selectedDetails).some(detailNo => approvedDetails.has(detailNo))}
          >
            選択した明細の承認を取り消し
          </Button>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selectedDetails.size > 0 && selectedDetails.size < filteredDetails.length}
                  checked={selectedDetails.size === filteredDetails.length && filteredDetails.length > 0}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>明細番号</TableCell>
              <TableCell>取引先</TableCell>
              <TableCell>商品名</TableCell>
              <TableCell align="right">金額</TableCell>
              <TableCell>税率</TableCell>
              <TableCell>ステータス</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredDetails.map((detail) => (
              <TableRow
                key={`${detail.customer_code}-${detail.no}`}
                sx={{
                  '&:hover': { bgcolor: 'action.hover', cursor: 'pointer' },
                  bgcolor: approvedDetails.has(detail.no) ? 'success.lighter' : 'inherit',
                }}
                onClick={(e) => handleDetailClick(detail, e)}
                selected={selectedDetails.has(detail.no)}
              >
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedDetails.has(detail.no)}
                    onChange={(e) => {
                      e.stopPropagation();
                      setSelectedDetails(prev => {
                        const newSet = new Set(prev);
                        if (e.target.checked) {
                          newSet.add(detail.no);
                        } else {
                          newSet.delete(detail.no);
                        }
                        return newSet;
                      });
                    }}
                  />
                </TableCell>
                <TableCell>{detail.no}</TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {detail.customer_code}
                  </Typography>
                  {detail.customer_name}
                </TableCell>
                <TableCell>{detail.description}</TableCell>
                <TableCell align="right">
                  {new Intl.NumberFormat('ja-JP', {
                    style: 'currency',
                    currency: 'JPY'
                  }).format(parseInt(detail.amount.replace(/[^\d]/g, '')))}
                </TableCell>
                <TableCell>{detail.tax_rate}</TableCell>
                <TableCell>
                  {approvedDetails.has(detail.no) ? (
                    <Tooltip
                      title={`承認日時: ${new Date(approvedDetails.get(detail.no)!.approved_at).toLocaleString()}\n承認者: ${approvedDetails.get(detail.no)!.approved_by}`}
                    >
                      <Chip
                        icon={<CheckCircleIcon />}
                        label="承認済"
                        size="small"
                        color="success"
                      />
                    </Tooltip>
                  ) : (
                    <Chip
                      label="未承認"
                      size="small"
                      color="default"
                    />
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <DetailDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
      />
    </Box>
  );
};
