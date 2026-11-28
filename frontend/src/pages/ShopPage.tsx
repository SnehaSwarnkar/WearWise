import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Heart, Search } from 'lucide-react';
import Header from './Header';
import { fetchProducts } from '../api/products';
import { addToWishlist, getWishlist } from '../api/saved';

const CATEGORIES = ['All', 'Tops', 'Shirts', 'Trousers', 'Jeans', 'Skirts', 'Dresses', 'Jackets'];

export default function ShopPage({ sectionGender = 'all' }: { sectionGender?: 'all' | 'men' | 'women' | 'kids' }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [category, setCategory] = useState(searchParams.get('category') || 'All');
  const [search, setSearch] = useState(searchParams.get('q') || '');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [sort, setSort] = useState(searchParams.get('sort') || 'featured');
  const [products, setProducts] = useState<any[]>([]);
  const [wishlistIds, setWishlistIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    Promise.all([
      fetchProducts(category, false, {
        gender: sectionGender,
        search: search.trim() || undefined,
        min_price: minPrice || undefined,
        max_price: maxPrice || undefined,
        sort,
      }).catch(() => []),
      getWishlist().catch(() => []),
    ]).then(([items, wish]) => {
      if (!alive) return;
      setProducts(Array.isArray(items) ? items : []);
      setWishlistIds(new Set((Array.isArray(wish) ? wish : []).map((w: any) => w.product_id)));
      setLoading(false);
    });
    return () => {
      alive = false;
    };
  }, [sectionGender, category, search, minPrice, maxPrice, sort]);

  const handleSave = async (p: any) => {
    try {
      await addToWishlist(p);
      setWishlistIds((prev) => new Set([...prev, p.id]));
      setToast(`Added "${p.name}" to your Wishlist.`);
      setTimeout(() => setToast(null), 2500);
    } catch {
      setToast('Unable to update wishlist right now.');
    }
  };

  const titles: Record<string, { title: string; subtitle: string }> = {
    all: {
      title: 'ALL CLOTHING',
      subtitle: 'Complete catalog across Men, Women, and Kids collections.',
    },
    men: {
      title: "MEN'S SHOP",
      subtitle: 'Structured shirts, relaxed tees, knit layers, trousers, and outerwear.',
    },
    women: {
      title: "WOMEN'S SHOP",
      subtitle: 'Everyday tops, tailored silhouettes, skirts, dresses, and denim.',
    },
    kids: {
      title: "KIDS' SHOP",
      subtitle: 'Comfortable everyday cotton clothing, coordinated sets, and jackets.',
    },
  };
  const headerInfo = titles[sectionGender] || titles.all;

  return (
    <div style={{ minHeight: '100vh', background: '#fff8f1', color: '#151515' }}>
      <Header />

      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '30px 24px 64px' }}>
        {/* Section Department Switcher */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
          {[
            { id: 'all', label: 'All Shop', to: '/shop' },
            { id: 'men', label: 'Men', to: '/shop/men' },
            { id: 'women', label: 'Women', to: '/shop/women' },
            { id: 'kids', label: 'Kids', to: '/shop/kids' },
          ].map((d) => {
            const active = sectionGender === d.id;
            return (
              <Link
                key={d.id}
                to={d.to}
                style={{
                  padding: '8px 16px',
                  border: '2px solid #151515',
                  background: active ? '#d8ff3f' : '#ffffff',
                  color: '#151515',
                  fontWeight: 900,
                  fontSize: '12px',
                  textDecoration: 'none',
                }}
              >
                {d.label}
              </Link>
            );
          })}
        </div>

        <h1 style={{ fontFamily: '"Archivo Black", sans-serif', fontSize: 'clamp(30px, 4vw, 46px)', margin: '0 0 6px', letterSpacing: '-1.5px' }}>
          {headerInfo.title}
        </h1>
        <p style={{ margin: '0 0 22px', fontSize: '14px', color: '#454854' }}>{headerInfo.subtitle}</p>

        {/* Search, Price Filter & Sort Bar */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
            gap: '10px',
            padding: '14px',
            background: '#ffffff',
            border: '2.5px solid #151515',
            marginBottom: '18px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', border: '1.5px solid #151515', padding: '6px 10px' }}>
            <Search size={15} />
            <input
              type="search"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setSearchParams((p) => {
                  const n = new URLSearchParams(p);
                  if (e.target.value) n.set('q', e.target.value);
                  else n.delete('q');
                  return n;
                });
              }}
              placeholder="Search items…"
              style={{ border: 'none', outline: 'none', width: '100%', fontSize: '13px' }}
            />
          </div>

          <input
            type="number"
            min="0"
            value={minPrice}
            onChange={(e) => setMinPrice(e.target.value)}
            placeholder="Min price (₹)"
            style={{ border: '1.5px solid #151515', padding: '8px 10px', fontSize: '13px' }}
          />
          <input
            type="number"
            min="0"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            placeholder="Max price (₹)"
            style={{ border: '1.5px solid #151515', padding: '8px 10px', fontSize: '13px' }}
          />
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            aria-label="Sort products"
            style={{ border: '1.5px solid #151515', padding: '8px 10px', fontSize: '13px', fontWeight: 700, background: '#fff' }}
          >
            <option value="featured">Sort: Featured</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="newest">Newest Arrivals</option>
            <option value="popular">Popular</option>
          </select>
        </div>

        {/* Category Pills */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '22px' }}>
          {CATEGORIES.map((c) => {
            const active = category === c;
            return (
              <button
                key={c}
                type="button"
                onClick={() => setCategory(c)}
                style={{
                  padding: '6px 14px',
                  border: '2px solid #151515',
                  background: active ? '#151515' : '#ffffff',
                  color: active ? '#d8ff3f' : '#151515',
                  fontWeight: 800,
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                {c}
              </button>
            );
          })}
        </div>

        {toast && (
          <div style={{ marginBottom: '16px', padding: '10px 14px', background: '#d8ff3f', border: '2px solid #151515', fontWeight: 800, fontSize: '13px' }}>
            {toast}
          </div>
        )}

        {loading ? (
          <p style={{ fontSize: '14px', color: '#6b7280' }}>Loading products…</p>
        ) : products.length === 0 ? (
          <div style={{ padding: '28px', background: '#ffffff', border: '2px solid #151515' }}>
            <strong>No products matched your filters.</strong>
            <p style={{ margin: '6px 0 12px', fontSize: '13px', color: '#454854' }}>
              Try clearing your search or widening your price range.
            </p>
            <button
              type="button"
              onClick={() => {
                setCategory('All');
                setSearch('');
                setMinPrice('');
                setMaxPrice('');
              }}
              style={{ border: '2px solid #151515', background: '#d8ff3f', padding: '8px 14px', fontWeight: 900, cursor: 'pointer' }}
            >
              Show All Products
            </button>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '20px' }}>
            {products.map((p) => {
              const detailUrl = p.sku ? `/product/${encodeURIComponent(p.sku)}` : `/shop`;
              const sizes: string[] = Array.isArray(p.available_sizes) && p.available_sizes.length ? p.available_sizes : ['S', 'M', 'L'];
              const colors: string[] = Array.isArray(p.colors) ? p.colors : [];
              const inStock = (p.stock ?? 10) > 0;
              const isWished = wishlistIds.has(p.id);

              return (
                <article
                  key={p.id}
                  data-testid={`shop-card-${p.sku || p.id}`}
                  style={{
                    background: '#ffffff',
                    border: '2.5px solid #151515',
                    boxShadow: '5px 5px 0 #151515',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                  }}
                >
                  <div style={{ position: 'relative', aspectRatio: '4 / 5', background: '#f3ece4' }}>
                    <Link to={detailUrl} style={{ display: 'block', width: '100%', height: '100%' }}>
                      {p.image ? (
                        <img src={p.image} alt={p.name} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
                      ) : (
                        <div style={{ padding: '24px', fontSize: '13px', color: '#6b7280' }}>No image</div>
                      )}
                    </Link>
                    <button
                      type="button"
                      aria-label={`Save ${p.name} to wishlist`}
                      onClick={() => handleSave(p)}
                      style={{
                        position: 'absolute',
                        top: '10px',
                        right: '10px',
                        width: '34px',
                        height: '34px',
                        borderRadius: '50%',
                        border: '2px solid #151515',
                        background: isWished ? '#ff3d9a' : '#ffffff',
                        color: isWished ? '#ffffff' : '#151515',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        cursor: 'pointer',
                      }}
                    >
                      <Heart size={16} fill={isWished ? '#ffffff' : 'none'} />
                    </button>
                  </div>

                  <div style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', fontWeight: 800, color: '#6b7280' }}>
                      <span>{p.seller_name || p.brand || 'WEARWISE EDIT'}</span>
                      <span style={{ color: inStock ? '#15803d' : '#991b1b' }}>
                        {inStock ? 'In Stock' : 'Out of Stock'}
                      </span>
                    </div>

                    <Link to={detailUrl} style={{ textDecoration: 'none', color: '#151515', fontWeight: 900, fontSize: '15px', lineHeight: 1.25 }}>
                      {p.name}
                    </Link>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                      {sizes.slice(0, 5).map((sz) => (
                        <span
                          key={sz}
                          style={{
                            border: '1px solid #151515',
                            padding: '2px 6px',
                            fontSize: '10px',
                            fontWeight: 800,
                          }}
                        >
                          {sz}
                        </span>
                      ))}
                      {colors.slice(0, 4).map((c, idx) => (
                        <span
                          key={`${c}-${idx}`}
                          title={c}
                          style={{
                            width: '12px',
                            height: '12px',
                            borderRadius: '50%',
                            background: c.startsWith('#') ? c : '#d1d5db',
                            border: '1px solid #151515',
                            marginLeft: idx === 0 ? 'auto' : 0,
                          }}
                        />
                      ))}
                    </div>

                    <div style={{ marginTop: 'auto', paddingTop: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ fontSize: '16px' }}>₹{Number(p.price || 0).toLocaleString()}</strong>
                      <Link
                        to={detailUrl}
                        style={{
                          padding: '6px 11px',
                          background: '#151515',
                          color: '#d8ff3f',
                          fontWeight: 900,
                          fontSize: '11px',
                          textDecoration: 'none',
                        }}
                      >
                        Details &amp; Fit →
                      </Link>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
