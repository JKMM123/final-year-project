import { useEffect } from "react"; // 1. Import useEffect
import { Trans, useTranslation } from "react-i18next";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/button";
import { SidebarTrigger } from "../../components/ui/sidebar";
import { Separator } from "../../components/ui/separator";
import { LogOut } from "lucide-react";

const Header = () => {
  const { user, logout } = useAuth();
  const { t, i18n } = useTranslation(); // 2. Destructure i18n

  // 3. Effect to handle Language Direction (LTR/RTL)
  useEffect(() => {
    const dir = i18n.dir(i18n.language);
    document.documentElement.dir = dir;
    document.documentElement.lang = i18n.language;
  }, [i18n, i18n.language]);

  return (
    // 4. Use padding-start/end (px) is fine, but gap handles spacing well
    <header className="flex h-16 shrink-0 items-center gap-2 border-b bg-background px-4 transition-all">
      <div className="flex items-center gap-2">
        <SidebarTrigger />
        {/* 5. Use 'h-4' is fine, usually Separator handles orientation, 
             but we don't need margin classes if using gap in parent */}
        <Separator orientation="vertical" className="h-4" />
      </div>

      <div className="flex flex-1 items-center justify-end gap-4">
        {/* Welcome Message */}
        <span className="text-sm text-muted-foreground hidden sm:inline-block">
          <Trans
            i18nKey="header.welcome"
            values={{
              username: user?.username,
              role: t(`usersPage.roles.${user?.role}`),
            }}
            components={{
              1: <strong className="font-semibold text-foreground" />,
            }}
          />
        </span>

        {/* Logout Button */}
        <Button
          variant="destructive"
          size="sm"
          // 6. Ensure logout exists before calling it
          onClick={() => {
            console.log("Logout clicked"); // Debugging check
            if (logout) logout();
          }}
          className="gap-2"
        >
          <LogOut className="h-4 w-4" />
          {/* 7. I removed 'hidden sm:inline' so you can see if the text appears. 
               Add it back if you want it hidden on mobile. */}
          <span>{t("header.logout")}</span>
        </Button>
      </div>
    </header>
  );
};

export default Header;
