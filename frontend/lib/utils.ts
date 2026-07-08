export function timeAgo(dateStr: string): string {
  const diff   = Date.now() - new Date(dateStr).getTime();
  const mins   = Math.floor(diff / 60000);
  const hours  = Math.floor(diff / 3600000);
  const days   = Math.floor(diff / 86400000);
  const months = Math.floor(days / 30);
  if (mins  < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days  < 30) return `${days}d ago`;
  return `${months}mo ago`;
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-GB", {
    day: "numeric", month: "long", year: "numeric",
  });
}

export function truncate(str: string, n: number): string {
  return str.length > n ? str.slice(0, n) + "…" : str;
}

export function getInitials(name: string): string {
  return name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
}
