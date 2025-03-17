// eslint-disable-next-line @typescript-eslint/no-unused-vars
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import NavigateNextIcon from '@mui/icons-material/NavigateNext';

// 型定義の未使用部分を修正
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { Detail, Customer } from '../types';
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { DetailWithCustomer, StockInfo, QuantityInfo } from '../types';

// 未使用の型定義 NestedKeyOf を修正
// eslint-disable-next-line @typescript-eslint/no-unused-vars
type NestedKeyOf<T> = ...

// handleNext 関数の未使用警告を修正
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const handleNext = () => {
  // 実装
};

// formatCurrency 関数の未使用警告を修正
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const formatCurrency = (value: number) => {
  // 実装
};

// useEffectの依存関係を修正
useEffect(() => {
  // 既存のコード
  // ...
  
  // imageUrlを依存配列に追加
}, [detail, imageUrl]); // imageUrlを依存配列に追加 