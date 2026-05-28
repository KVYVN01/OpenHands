import {
  type RouteConfig,
  layout,
  index,
  route,
} from "@react-router/dev/routes";

export default [
  // The dedicated /login page has been removed.  OpenHands now relies on the
  // OSS auth flow (where `useIsAuthed` always returns true) and any SaaS
  // deployment is expected to terminate authentication at the gateway/IDP
  // (Keycloak, OAuth proxy, etc.) before traffic reaches the React app.
  route("onboarding", "routes/onboarding-form.tsx"),
  route("information-request", "routes/information-request.tsx"),
  layout("routes/root-layout.tsx", [
    index("routes/home.tsx"),
    route("accept-tos", "routes/accept-tos.tsx"),
    route("launch", "routes/launch.tsx"),
    route("settings", "routes/settings.tsx", [
      index("routes/llm-settings.tsx"),
      route("agent", "routes/agent-settings.tsx"),
      route("condenser", "routes/condenser-settings.tsx"),
      route("verification", "routes/verification-settings.tsx"),
      route("org-defaults", "routes/org-default-llm-settings.tsx"),
      route(
        "org-defaults/condenser",
        "routes/org-default-condenser-settings.tsx",
      ),
      route(
        "org-defaults/verification",
        "routes/org-default-verification-settings.tsx",
      ),
      route("mcp", "routes/mcp-settings.tsx"),
      route("skills", "routes/skills-settings.tsx"),
      route("user", "routes/user-settings.tsx"),
      route("integrations", "routes/git-settings.tsx"),
      route("app", "routes/app-settings.tsx"),
      route("billing", "routes/billing.tsx"),
      route("secrets", "routes/secrets-settings.tsx"),
      route("api-keys", "routes/api-keys.tsx"),
      route("org-members", "routes/manage-organization-members.tsx"),
      route("org", "routes/manage-org.tsx"),
    ]),
    route("conversations/:conversationId", "routes/conversation.tsx"),
    route("oauth/device/verify", "routes/device-verify.tsx"),
  ]),
  // Shared routes that don't require authentication
  route(
    "shared/conversations/:conversationId",
    "routes/shared-conversation.tsx",
  ),
] satisfies RouteConfig;
