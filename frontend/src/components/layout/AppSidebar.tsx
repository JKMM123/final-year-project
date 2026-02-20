import * as React from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../context/AuthContext";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
} from "../ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import {
  Home,
  Users,
  Package,
  Gauge,
  FileText,
  Mail,
  Banknote,
  Wrench,
  MapPin,
  Globe,
  ChevronUp,
} from "lucide-react";

// Define menu items
const NAV_ITEMS = [
  {
    to: "/dashboard",
    labelKey: "sidebar.dashboard",
    icon: Home,
    roles: ["system", "admin"],
  },
  {
    to: "/users",
    labelKey: "sidebar.users",
    icon: Users,
    roles: ["system", "admin"],
  },
  {
    to: "/packages",
    labelKey: "sidebar.packages",
    icon: Package,
    roles: ["system", "admin"],
  },
  {
    to: "/meters",
    labelKey: "sidebar.meters",
    icon: Gauge,
    roles: ["system", "admin", "user"],
  },
  {
    to: "/readings",
    labelKey: "sidebar.readings",
    icon: FileText,
    roles: ["system", "admin", "user"],
  },
  {
    to: "/messages",
    labelKey: "sidebar.messages",
    icon: Mail,
    roles: ["system", "admin"],
  },
  {
    to: "/bills",
    labelKey: "sidebar.bills",
    icon: Banknote,
    roles: ["system", "admin", "user"],
  },
  {
    to: "/fixes",
    labelKey: "sidebar.fixes",
    icon: Wrench,
    roles: ["system", "admin", "user"],
  },
  {
    to: "/areas",
    labelKey: "sidebar.areas",
    icon: MapPin,
    roles: ["system", "admin"],
  },
];

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { user } = useAuth();
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const role = user?.role;
  const isRtl = i18n.dir() === "rtl";
  // Filter links based on role
  const allowedLinks = NAV_ITEMS.filter(
    (link) => role && link.roles.includes(role),
  );

  const handleLanguageChange = (lang: string) => {
    i18n.changeLanguage(lang);
    // The Layout component handles the 'dir' attribute update
  };

  return (
    <Sidebar collapsible="icon" side={isRtl ? "right" : "left"} {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-2">
          <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Gauge className="size-4" />
          </div>
          <div className="grid flex-1 text-left text-sm leading-tight">
            <span className="truncate font-semibold">Skyline</span>
            <span className="truncate text-xs">{user?.role || "Guest"}</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>{t("sidebar.menu")}</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {allowedLinks.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <SidebarMenuButton
                    asChild
                    tooltip={t(item.labelKey)}
                    isActive={location.pathname === item.to}
                  >
                    <NavLink to={item.to}>
                      <item.icon />
                      <span>{t(item.labelKey)}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                >
                  <Globe className="size-4" />
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-semibold">
                      {t("common.language")}
                    </span>
                    <span className="truncate text-xs">
                      {i18n.language === "en"
                        ? t("common.english")
                        : t("common.arabic")}
                    </span>
                  </div>
                  <ChevronUp className="ml-auto" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side="top"
                className="w-[--radix-popper-anchor-width]"
              >
                <DropdownMenuItem onClick={() => handleLanguageChange("en")}>
                  {t("common.english")}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleLanguageChange("ar")}>
                  {t("common.arabic")}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
