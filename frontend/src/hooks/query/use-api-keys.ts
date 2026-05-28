import { useQuery } from "@tanstack/react-query";
import ApiKeysClient from "#/api/api-keys";
import { useConfig } from "./use-config";
import { useSelectedOrganizationId } from "#/context/use-selected-organization";
import { useIsAuthed } from "./use-is-authed";

export const API_KEYS_QUERY_KEY = "api-keys";

export function useApiKeys() {
  const { data: config } = useConfig();
  const { organizationId } = useSelectedOrganizationId();
  const { data: isAuthed } = useIsAuthed();

  const isSaas = config?.app_mode === "saas";
  const isDostup = config?.app_mode === "dostup";

  return useQuery({
    queryKey: [API_KEYS_QUERY_KEY, organizationId, isDostup],
    enabled: (isSaas && !!organizationId) || (isDostup && !!isAuthed),
    queryFn: async () => {
      ApiKeysClient.setBasePath(isDostup ? "/api/v1/bot/keys" : "/api/keys");
      const keys = await ApiKeysClient.getApiKeys();
      return Array.isArray(keys) ? keys : [];
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 15, // 15 minutes
  });
}
