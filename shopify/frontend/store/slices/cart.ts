import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type Item = { id: string; title: string; priceCents: number; quantity: number };

const slice = createSlice({
  name: 'cart',
  initialState: { items: [] as Item[], storeId: '' },
  reducers: {
    setStore(state, action: PayloadAction<string>){ state.storeId = action.payload; },
    setItems(state, action: PayloadAction<Item[]>) { state.items = action.payload; },
    addItem(state, action: PayloadAction<Item>) {
      const e = state.items.find(i => i.id === action.payload.id);
      if (e) e.quantity += action.payload.quantity; else state.items.push(action.payload);
    },
    updateQty(state, action: PayloadAction<{ id: string; quantity: number }>) {
      const e = state.items.find(i => i.id === action.payload.id);
      if (e) e.quantity = action.payload.quantity;
    },
    removeItem(state, action: PayloadAction<string>) {
      state.items = state.items.filter(i => i.id !== action.payload);
    },
    clear(state){ state.items = []; }
  }
});

export const { setStore, setItems, addItem, updateQty, removeItem, clear } = slice.actions;
export default slice.reducer;
