export function ErrorBanner({ message }: { message: string }) {
  if (!message) return null;
  return <div className="error-banner" role="alert">{message}</div>;
}
