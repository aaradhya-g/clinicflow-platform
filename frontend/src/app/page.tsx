"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";

export default function HomePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (user) {
        if (user.role === "doctor") router.push("/doctor");
        else if (user.role === "admin") router.push("/admin");
        else router.push("/receptionist");
      } else {
        router.push("/login");
      }
    }
  }, [user, isLoading, router]);

  return (
    <div className="flex h-screen items-center justify-center bg-clinic-canvas">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-clinic-primary border-t-transparent" />
        <span className="text-sm font-medium text-clinic-text-secondary">
          Initializing ClinicFlow Platform...
        </span>
      </div>
    </div>
  );
}
