import React from 'react';
import SellerLayout from '../../components/seller/SellerLayout';
import MerchantGarmentStudio from '../MerchantGarmentStudio';

export default function SellerStudioPage() {
  return (
    <SellerLayout
      title="Digital Garment & 3D Try-On Studio"
      subtitle="Upload photos, configure S/M/L garment measurements, preview 3D fit, and publish to the marketplace."
    >
      <MerchantGarmentStudio embedded />
    </SellerLayout>
  );
}
