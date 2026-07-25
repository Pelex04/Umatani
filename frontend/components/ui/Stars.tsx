export function Stars({ rating, count, size = 13 }: { rating: number; count?: number; size?: number }) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
      <span style={{ display: "inline-flex", gap: 1 }}>
        {[1,2,3,4,5].map(i => (
          <svg key={i} width={size} height={size} viewBox="0 0 16 16" fill={i <= Math.round(rating) ? "#C9A84C" : "#E8DDD0"}>
            <path d="M8 1l1.85 3.75L14 5.5l-3 2.92.7 4.08L8 10.35 4.3 12.5l.7-4.08L2 5.5l4.15-.75z"/>
          </svg>
        ))}
      </span>
      {rating > 0 && (
        <span style={{ fontSize: size - 2, fontWeight: 500, color: "var(--forest)", fontFamily: "var(--font-mono)" }}>
          {rating.toFixed(1)}
        </span>
      )}
      {count !== undefined && (
        <span style={{ fontSize: size - 2, color: "var(--ink-faint)", fontFamily: "var(--font-mono)" }}>({count})</span>
      )}
    </span>
  );
}
