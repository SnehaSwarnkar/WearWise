import ShopLayout from "./ShopLayout";

export default function MenShop() {
  return (
    <ShopLayout
      gender="men"
      eyebrow="✦ MEN'S COLLECTION"
      heroTitle={<>DRESS<br /><span>SHARP.</span></>}
      heroSub="Western, traditional, indo-western and occasion wear — curated for every man."
      accentColor="var(--purple)"
    />
  );
}
