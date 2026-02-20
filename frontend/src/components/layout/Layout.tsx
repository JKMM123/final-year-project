import { useEffect } from "react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { SidebarProvider, SidebarInset } from "../../components/ui/sidebar";
import { AppSidebar } from "./AppSidebar";
import Header from "./Header";

interface LayoutProps {
  children: ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  const { i18n } = useTranslation();

  // Handle RTL/LTR direction
  useEffect(() => {
    const dir = i18n.dir(i18n.language);
    document.documentElement.dir = dir;
    document.documentElement.lang = i18n.language;

    // Optional: Add specific class for Arabic fonts if needed
    if (dir === "rtl") {
      document.body.classList.add("rtl");
    } else {
      document.body.classList.remove("rtl");
    }
  }, [i18n, i18n.language]);

  return (
    <SidebarProvider>
      {/* The actual Sidebar Component */}
      <AppSidebar />

      {/* The Main Content Area */}
      <SidebarInset>
        <Header />
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
          <main className="min-h-screen flex-1 rounded-xl bg-muted/50 md:min-h-min mt-4">
            <div className="p-4">{children}</div>
          </main>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
};

export default Layout;
