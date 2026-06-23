interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
  actions?: React.ReactNode;
}

export function Card({ title, children, className = "", actions }: CardProps) {
  return (
    <div className={`card ${className}`.trim()}>
      {(title || actions) && (
        <div className="card-header">
          {title ? <h2 className="card-title">{title}</h2> : <span />}
          {actions}
        </div>
      )}
      {children}
    </div>
  );
}
