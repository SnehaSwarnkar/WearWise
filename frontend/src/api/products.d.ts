export function fetchProducts(
  category?: string | null,
  sortPrice?: boolean,
  extra?: {
    gender?: string;
    occasion?: string;
    search?: string;
    min_price?: string | number;
    max_price?: string | number;
    sort?: string;
  }
): Promise<any[]>;

export function fetchRecommendations(gender?: string | null, limit?: number): Promise<{ items: any[] }>;
export function fetchProduct(id: string | number): Promise<any>;
export function fetchProductBySku(sku: string): Promise<any>;
export function fetchProductReviews(sku: string): Promise<any>;
export function submitProductReview(sku: string, payload: Record<string, any>): Promise<any>;
