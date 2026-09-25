"use client";

import { SystemBanner } from "@/components/SystemBanner";

export function BannerWrapper({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SystemBanner />
      {children}
    </>
  );
}