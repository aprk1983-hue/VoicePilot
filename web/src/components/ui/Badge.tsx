interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "accent";
}

export function Badge({ children, variant = "default" }: BadgeProps) {
  const className =
    variant === "default" ? "badge" : `badge badge-${variant}`;
  return <span className={className}>{children}</span>;
}
