import { openHands } from "../open-hands-axios";
import DostupAuthService from "./dostup-auth-service.api";
import { AuthenticateResponse, GitHubAccessTokenResponse } from "./auth.types";
import { WebClientConfig } from "../option-service/option.types";

/**
 * Authentication service for handling all authentication-related API calls.
 *
 * Supports three deployment modes:
 *   - ``oss``    — single-tenant, no login required.
 *   - ``saas``   — Keycloak/GitHub OAuth flow.
 *   - ``dostup`` — DOSTUP_CRS local email/password + JWT cookie.
 */
class AuthService {
  /**
   * Probe whether the current session is authenticated.
   *
   * In ``oss`` mode this is always ``true``. In ``saas`` mode we hit the
   * legacy ``/api/authenticate`` endpoint. In ``dostup`` mode we hit the V1
   * ``/api/v1/auth/me`` endpoint.
   */
  static async authenticate(
    appMode: WebClientConfig["app_mode"],
  ): Promise<boolean> {
    if (appMode === "oss") return true;
    if (appMode === "dostup") {
      await DostupAuthService.me();
      return true;
    }

    // Just make the request, if it succeeds (no exception thrown), return true
    await openHands.post<AuthenticateResponse>("/api/authenticate");
    return true;
  }

  /**
   * Get GitHub access token from Keycloak callback
   * @param code Code provided by GitHub
   * @returns GitHub access token
   */
  static async getGitHubAccessToken(
    code: string,
  ): Promise<GitHubAccessTokenResponse> {
    const { data } = await openHands.post<GitHubAccessTokenResponse>(
      "/api/keycloak/callback",
      {
        code,
      },
    );
    return data;
  }

  /**
   * Logout user from the application
   * @param appMode The application mode (saas, oss or dostup)
   */
  static async logout(appMode: WebClientConfig["app_mode"]): Promise<void> {
    if (appMode === "dostup") {
      await DostupAuthService.logout();
      return;
    }
    const endpoint =
      appMode === "saas" ? "/api/logout" : "/api/unset-provider-tokens";
    await openHands.post(endpoint);
  }
}

export default AuthService;
