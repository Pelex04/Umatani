export function Skeleton({ w, h = 16, r = 8 }: { w?: string; h?: number; r?: number }) {
  return <div className="sk" style={{ width: w ?? "100%", height: h, borderRadius: r }} />;
}

export function BusinessCardSkeleton() {
  return (
    <div className="card" style={{ padding: 18 }}>
      <div style={{ display: "flex", gap: 12, marginBottom: 14 }}>
        <Skeleton w="46px" h={46} r={11} />
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 7 }}>
          <Skeleton h={14} r={5} />
          <Skeleton w="55%" h={11} r={5} />
        </div>
      </div>
      <Skeleton h={12} r={5} />
      <div style={{ marginTop: 6 }}><Skeleton w="75%" h={12} r={5} /></div>
      <div style={{ marginTop: 18, paddingTop: 14, borderTop: "1px solid var(--border)", display: "flex", justifyContent: "space-between" }}>
        <Skeleton w="90px" h={12} r={5} />
        <Skeleton w="70px" h={12} r={5} />
      </div>
    </div>
  );
}
