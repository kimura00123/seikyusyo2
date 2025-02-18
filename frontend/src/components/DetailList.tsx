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
  Chip
} from '@mui/material';
import { useDocumentStore, DetailWithCustomer } from '../store/documentStore';
import { DetailDialog } from './DetailDialog';

export const DetailList: React.FC = () => {
  const { document, status, selectDetail } = useDocumentStore();
  const [dialogOpen, setDialogOpen] = useState(false);

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

  const handleDetailClick = (detail: DetailWithCustomer) => {
    selectDetail(detail);
    setDialogOpen(true);
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h6" gutterBottom>
        明細一覧
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>明細番号</TableCell>
              <TableCell>取引先</TableCell>
              <TableCell>商品名</TableCell>
              <TableCell align="right">金額</TableCell>
              <TableCell>税率</TableCell>
              <TableCell>ステータス</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {allDetails.map((detail) => (
              <TableRow
                key={`${detail.customer_code}-${detail.no}`}
                sx={{ '&:hover': { bgcolor: 'action.hover', cursor: 'pointer' } }}
                onClick={() => handleDetailClick(detail)}
              >
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
                  <Chip
                    label="未確認"
                    size="small"
                    color="default"
                  />
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
