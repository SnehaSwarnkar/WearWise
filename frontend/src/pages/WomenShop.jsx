import ShopLayout from "./ShopLayout";

export default function WomenShop() {
  return (
    <ShopLayout
      gender="women"
      eyebrow="✦ WOMEN'S COLLECTION"
      heroTitle={<>DRESS<br /><span>BEAUTIFULLY.</span></>}
      heroSub="Western, sarees, lehengas, indo-western and occasion wear — made for every woman."
      accentColor="var(--pink)"
    />
  );
}
