export default function LoadingSpinner({ className = "" }) {
  return (
    <div className={`flex items-center justify-center py-6 ${className}`}>
      <div
        className="h-8 w-8 animate-spin rounded-full border-2 border-white/15 border-t-white"
        aria-hidden
      />
    </div>
  );
}
