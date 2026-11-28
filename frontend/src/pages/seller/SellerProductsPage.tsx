import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import SellerLayout from '../../components/seller/SellerLayout';
import { createSellerProduct, fetchSellerProducts, updateSellerProduct } from '../../api/seller';

export default function SellerProductsPage({
  openCreateDefault = false,
  inventoryMode = false,
}: {
  openCreateDefault?: boolean;
  inventoryMode?: boolean;
}) {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [showCreate, setShowCreate] = useState(openCreateDefault);
  const [form, setForm] = useState({
    name: '',
    sku: '',
    category: 'Shirts',
    gender: 'unisex',
    description: '',
    color_variant: '#151515',
    price: '1499',
    inventory_count: '20',
    try_on_mode: 'IMAGE_ONLY',
  });

  const loadProducts = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetchSellerProducts();
      setProducts(res.products || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load store products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setShowCreate(openCreateDefault);
    loadProducts();
  }, [openCreateDefault]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setNotice('');
    try {
      await createSellerProduct({
        ...form,
        price: Number(form.price),
        inventory_count: Number(form.inventory_count),
      });
      setNotice(`Created draft listing for SKU ${form.sku.toUpperCase()}.`);
      setForm({
        name: '',
        sku: '',
        category: 'Shirts',
        gender: 'unisex',
        description: '',
        color_variant: '#151515',
        price: '1499',
        inventory_count: '20',
        try_on_mode: 'IMAGE_ONLY',
      });
      setShowCreate(false);
      await loadProducts();
    } catch (err: any) {
      setError(err.message || 'Failed to create listing');
    }
  };

  const handleQuickUpdate = async (prod: any, updates: Record<string, any>) => {
    setError('');
    setNotice('');
    try {
      await updateSellerProduct(prod.id, updates);
      setNotice(`Updated ${prod.sku}.`);
      await loadProducts();
    } catch (err: any) {
      setError(err.message || 'Failed to update product');
    }
  };

  return (
    <SellerLayout
      title={inventoryMode ? 'Inventory & Availability' : openCreateDefault ? 'Add Product Listing' : 'Store Products'}
      subtitle={
        inventoryMode
          ? 'Manage available sizes, stock counts, and listing visibility for your catalog.'
          : 'Create and update product listings, pricing, stock, and virtual try-on modes.'
      }
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', marginBottom: '18px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={() => setShowCreate((s) => !s)}
            data-testid="toggle-create-product-btn"
            style={{
              background: '#d8ff3f',
              color: '#151515',
              border: '2px solid #151515',
              boxShadow: '4px 4px 0 #151515',
              padding: '10px 16px',
              fontWeight: 900,
              cursor: 'pointer',
            }}
          >
            {showCreate ? 'Close Form' : '+ New Product Listing'}
          </button>
          <Link
            to="/seller/studio"
            style={{
              background: '#8d6bff',
              color: '#ffffff',
              border: '2px solid #151515',
              boxShadow: '4px 4px 0 #151515',
              padding: '10px 16px',
              fontWeight: 900,
              textDecoration: 'none',
            }}
          >
            Open 3D Garment Studio →
          </Link>
        </div>
      </div>

      {notice && (
        <div style={{ padding: '10px 14px', border: '2px solid #151515', background: '#d8ff3f', marginBottom: '14px', fontWeight: 700 }}>
          {notice}
        </div>
      )}
      {error && <p className="auth-error">{error}</p>}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          data-testid="seller-create-product-form"
          style={{
            background: '#ffffff',
            border: '2.5px solid #151515',
            boxShadow: '6px 6px 0 #151515',
            padding: '20px',
            marginBottom: '24px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '14px',
          }}
        >
          <label className="auth-field">
            <span>PRODUCT NAME</span>
            <input
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Relaxed Poplin Shirt"
            />
          </label>
          <label className="auth-field">
            <span>SKU</span>
            <input
              required
              value={form.sku}
              onChange={(e) => setForm({ ...form, sku: e.target.value })}
              placeholder="SHR-WW-010"
            />
          </label>
          <label className="auth-field">
            <span>CATEGORY</span>
            <select
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              style={{ padding: '10px', border: '2px solid #151515', background: '#fff' }}
            >
              {['Tops', 'Shirts', 'Trousers', 'Jeans', 'Skirts', 'Dresses', 'Jackets'].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </label>
          <label className="auth-field">
            <span>SECTION</span>
            <select
              value={form.gender}
              onChange={(e) => setForm({ ...form, gender: e.target.value })}
              style={{ padding: '10px', border: '2px solid #151515', background: '#fff' }}
            >
              <option value="men">Men</option>
              <option value="women">Women</option>
              <option value="kids">Kids</option>
              <option value="unisex">Unisex</option>
            </select>
          </label>
          <label className="auth-field">
            <span>PRICE (INR)</span>
            <input
              type="number"
              min="1"
              required
              value={form.price}
              onChange={(e) => setForm({ ...form, price: e.target.value })}
            />
          </label>
          <label className="auth-field">
            <span>STOCK COUNT</span>
            <input
              type="number"
              min="0"
              required
              value={form.inventory_count}
              onChange={(e) => setForm({ ...form, inventory_count: e.target.value })}
            />
          </label>
          <label className="auth-field">
            <span>TRY-ON CAPABILITY</span>
            <select
              value={form.try_on_mode}
              onChange={(e) => setForm({ ...form, try_on_mode: e.target.value })}
              style={{ padding: '10px', border: '2px solid #151515', background: '#fff' }}
            >
              <option value="IMAGE_ONLY">Image Try-On Only</option>
              <option value="THREE_D_ONLY">Interactive 3D Only</option>
              <option value="IMAGE_AND_THREE_D">Image + Interactive 3D</option>
            </select>
          </label>
          <label className="auth-field" style={{ gridColumn: '1 / -1' }}>
            <span>DESCRIPTION</span>
            <input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Fabric composition, fit cut, and construction details"
            />
          </label>
          <div>
            <button type="submit" className="auth-submit" data-testid="seller-submit-create-product">
              SAVE DRAFT LISTING
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p>Loading store products…</p>
      ) : (
        <div
          data-testid="seller-products-table"
          style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
        >
          {products.length === 0 ? (
            <div style={{ padding: '24px', background: '#ffffff', border: '2px solid #151515' }}>
              No products in this store yet. Create a new listing or open the 3D Garment Studio.
            </div>
          ) : (
            products.map((prod) => (
              <div
                key={prod.id}
                data-testid={`seller-product-row-${prod.sku}`}
                style={{
                  background: '#ffffff',
                  border: '2px solid #151515',
                  boxShadow: '4px 4px 0 #151515',
                  padding: '16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '16px',
                  flexWrap: 'wrap',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <strong style={{ fontSize: '16px' }}>{prod.name}</strong>
                    <span style={{ fontSize: '12px', fontWeight: 800, padding: '2px 7px', border: '1.5px solid #151515', background: '#fff8f1' }}>
                      {prod.sku}
                    </span>
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 900,
                        padding: '2px 8px',
                        border: '1.5px solid #151515',
                        background: prod.status === 'published' ? '#d8ff3f' : '#ffad7d',
                      }}
                    >
                      {String(prod.status).toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: '13px', color: '#454854', marginTop: '6px' }}>
                    ₹{prod.price} · Category: {prod.category} · Sizes: {(prod.available_sizes || []).join(', ')} · Mode: {prod.try_on_mode}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <label style={{ fontSize: '12px', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                    Stock:
                    <input
                      type="number"
                      min="0"
                      defaultValue={prod.inventory_count}
                      onBlur={(e) => {
                        const val = Number(e.target.value);
                        if (!Number.isNaN(val) && val !== prod.inventory_count) {
                          handleQuickUpdate(prod, { inventory_count: val });
                        }
                      }}
                      style={{ width: '70px', padding: '5px', border: '1.5px solid #151515' }}
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() => handleQuickUpdate(prod, { available: !prod.available })}
                    style={{
                      padding: '6px 10px',
                      border: '1.5px solid #151515',
                      background: prod.available ? '#ffffff' : '#ff3d9a',
                      color: prod.available ? '#151515' : '#ffffff',
                      fontWeight: 800,
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    {prod.available ? 'In Stock (Pause)' : 'Paused (Resume)'}
                  </button>
                  <select
                    value={prod.try_on_mode}
                    onChange={(e) => handleQuickUpdate(prod, { try_on_mode: e.target.value })}
                    style={{ padding: '6px', border: '1.5px solid #151515', fontSize: '12px', fontWeight: 700 }}
                  >
                    <option value="IMAGE_ONLY">IMAGE_ONLY</option>
                    <option value="THREE_D_ONLY">THREE_D_ONLY</option>
                    <option value="IMAGE_AND_THREE_D">IMAGE_AND_THREE_D</option>
                  </select>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </SellerLayout>
  );
}
