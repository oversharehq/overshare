import type { Metadata } from "next";
import { MockBanner } from "@/components/MockBanner";
import { ScanPoller } from "@/components/ScanPoller";

// Reports can describe apps the submitter may not own, so they must never be
// indexed. See build brief §12 on retention and privacy.
export const metadata: Metadata = {
  title: "Scan report",
  robots: { index: false, follow: false },
};

export default async function ScanPage(props: PageProps<"/scan/[id]">) {
  const { id } = await props.params;

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <MockBanner />
      <ScanPoller id={id} />
    </div>
  );
}
