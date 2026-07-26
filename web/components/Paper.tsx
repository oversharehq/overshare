/**
 * Layout primitives for the document treatment: numbered sections, notes set in
 * the right margin, and captioned figures.
 *
 * Margin notes are floated rather than placed in a grid track, which is what
 * lets a note sit beside the specific paragraph it annotates and collapse to an
 * inline aside on narrow screens without any coordination between the two.
 */

export function Shell({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`mx-auto max-w-5xl px-6 ${className}`}>{children}</div>
  );
}

export function Section({
  index,
  title,
  id,
  children,
}: {
  index: string;
  title: React.ReactNode;
  id?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-4 border-t border-rule py-14 sm:py-16">
      <Shell>
        <header className="flex gap-4 sm:gap-6">
          <span className="label shrink-0 pt-[0.55rem] text-flag tabular-nums sm:pt-[0.7rem]">
            {index}
          </span>
          <h2 className="max-w-3xl text-[1.65rem] leading-[1.15] font-medium tracking-tight text-balance sm:text-[2.1rem]">
            {title}
          </h2>
        </header>
        <div className="mt-7 sm:pl-10 lg:pr-[17rem]">{children}</div>
      </Shell>
    </section>
  );
}

/**
 * A titled part of the report. Headings here are mono rather than serif — a
 * report is a form to be read in order, not an essay.
 */
export function Block({
  index,
  title,
  children,
  className = "",
}: {
  index: string;
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`mt-10 ${className}`}>
      <div className="flex items-baseline gap-3 border-b border-ink pb-2">
        <span className="label text-flag tabular-nums">{index}</span>
        <h2 className="label text-ink">{title}</h2>
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

/** A note in the right margin on wide screens; a ruled aside below `lg`. */
export function Note({ children }: { children: React.ReactNode }) {
  return (
    <aside className="my-5 border-l-2 border-rule-firm pl-4 font-mono text-xs leading-[1.7] text-mute lg:clear-right lg:float-right lg:my-1 lg:-mr-[17rem] lg:ml-12 lg:w-[14rem] lg:border-l-0 lg:pl-0">
      <span className="hidden lg:mb-1.5 lg:block lg:h-px lg:w-8 lg:bg-flag" />
      {children}
    </aside>
  );
}

export function Figure({
  index,
  caption,
  children,
}: {
  index: string;
  caption: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <figure>
      {children}
      <figcaption className="mt-3 flex gap-3 font-mono text-xs leading-[1.7] text-mute">
        <span className="shrink-0 text-faint uppercase">Fig. {index}</span>
        <span className="max-w-[34rem]">{caption}</span>
      </figcaption>
    </figure>
  );
}

export function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="bg-inset px-1 py-0.5 font-mono text-[0.85em] text-ink">
      {children}
    </code>
  );
}

/** Body copy. Serif, measured, with the sizing decided in one place. */
export function Prose({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`max-w-[36rem] space-y-4 text-[1.0625rem] leading-[1.65] text-ink-soft ${className}`}
    >
      {children}
    </div>
  );
}
