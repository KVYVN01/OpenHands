import { useParams } from "react-router";
import { useConfig } from "#/hooks/query/use-config";
import { useUserConversation } from "#/hooks/query/use-user-conversation";

const APP_TITLE_OSS = "DOSTUP_CRS";
const APP_TITLE_SAAS = "DOSTUP_CRS Cloud";
const APP_TITLE_DOSTUP = "DOSTUP_CRS";

/**
 * Hook that returns the appropriate document title based on app_mode and current route.
 * - For conversation pages: "Conversation Title | DOSTUP_CRS" or "Conversation Title | DOSTUP_CRS Cloud"
 * - For other pages: "DOSTUP_CRS" or "DOSTUP_CRS Cloud"
 */
export const useAppTitle = () => {
  const { data: config } = useConfig();
  const { conversationId } = useParams<{ conversationId: string }>();
  const { data: conversation } = useUserConversation(conversationId ?? null);

  let appTitle: string;
  if (config?.app_mode === "oss") {
    appTitle = APP_TITLE_OSS;
  } else if (config?.app_mode === "dostup") {
    appTitle = APP_TITLE_DOSTUP;
  } else {
    appTitle = APP_TITLE_SAAS;
  }
  const conversationTitle = conversation?.title;

  if (conversationId && conversationTitle) {
    return `${conversationTitle} | ${appTitle}`;
  }

  return appTitle;
};
