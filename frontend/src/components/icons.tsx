import type { SVGProps } from "react";

/** Minimal stroke-based icon set (no icon library dependency) — 24x24 viewBox,
 * 1.75 stroke width, inherits `currentColor` so they follow text color/theme. */
function Icon({ children, ...props }: SVGProps<SVGSVGElement> & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {children}
    </svg>
  );
}

export const ReportIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M7 3.5h7l4 4V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z" />
    <path d="M14 3.5V8h4" />
    <path d="M9 12.5h6M9 15.5h6M9 9.5h2" />
  </Icon>
);

export const ExplorerIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M3.5 7a1 1 0 0 1 1-1h4l1.5 2h9a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-14a1 1 0 0 1-1-1V7Z" />
  </Icon>
);

export const DiagramIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <rect x="3.5" y="4" width="6" height="4.5" rx="1" />
    <rect x="14.5" y="4" width="6" height="4.5" rx="1" />
    <rect x="9" y="15.5" width="6" height="4.5" rx="1" />
    <path d="M6.5 8.5v3a2 2 0 0 0 2 2h1M17.5 8.5v3a2 2 0 0 1-2 2h-1" />
  </Icon>
);

export const DatabaseIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <ellipse cx="12" cy="6" rx="7" ry="2.5" />
    <path d="M5 6v12c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V6" />
    <path d="M5 12c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5" />
  </Icon>
);

export const ApiIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M8 8 4 12l4 4M16 8l4 4-4 4M14 5l-4 14" />
  </Icon>
);

export const FindingsIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="M15.8 15.8 20 20" />
    <path d="M11 8.5v3M11 14v.01" />
  </Icon>
);

export const ScoresIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M5 19V10M12 19V5M19 19v-6" />
  </Icon>
);

export const SearchIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <circle cx="10.5" cy="10.5" r="6.5" />
    <path d="M19 19l-4.3-4.3" />
  </Icon>
);

export const PlusIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M12 5v14M5 12h14" />
  </Icon>
);

export const SunIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2.5v2M12 19.5v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2.5 12h2M19.5 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4" />
  </Icon>
);

export const MoonIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z" />
  </Icon>
);

export const ChevronRightIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M9 6l6 6-6 6" />
  </Icon>
);

export const ChevronDownIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M6 9l6 6 6-6" />
  </Icon>
);

export const FileIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M7 3.5h6l4 4V20a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z" />
    <path d="M13 3.5V8h4" />
  </Icon>
);

export const DownloadIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M12 4v11M8 11l4 4 4-4" />
    <path d="M5 19.5h14" />
  </Icon>
);

export const GithubIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M9 19c-4.5 1.5-4.5-2.5-6-3m12 5v-3.4c0-1 .1-1.4-.5-2 2-.2 4.5-1 4.5-4.5 0-1-.4-1.9-1-2.6.1-.3.5-1.4-.1-2.9 0 0-.9-.3-2.9 1a10 10 0 0 0-5.3 0c-2-1.3-2.9-1-2.9-1-.6 1.5-.2 2.6-.1 2.9-.6.7-1 1.6-1 2.6 0 3.5 2.5 4.3 4.5 4.5-.3.3-.5.7-.6 1.3-.5.2-1.8.6-2.6-.7-.5-.8-1.4-.9-1.4-.9" />
  </Icon>
);

export const UploadIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M12 15V4M8 8l4-4 4 4" />
    <path d="M5 15v3.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V15" />
  </Icon>
);

export const FolderIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M3.5 7a1 1 0 0 1 1-1h4l1.5 2h9a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1h-14a1 1 0 0 1-1-1V7Z" />
  </Icon>
);

export const SendIcon = (props: SVGProps<SVGSVGElement>) => (
  <Icon {...props}>
    <path d="M4 12l16-7-6.5 16-2.5-6.5L4 12Z" />
  </Icon>
);
