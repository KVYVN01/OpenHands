import { openHands } from "../open-hands-axios";

export interface DostupPublicUser {
  id: string;
  email: string;
  display_name: string;
  is_admin: boolean;
}

export interface DostupLoginPayload {
  email: string;
  password: string;
}

export interface DostupRegisterPayload extends DostupLoginPayload {
  display_name?: string;
}

/**
 * Client for the DOSTUP_CRS multi-user auth endpoints exposed by the
 * application server. All endpoints rely on the ``dostup_session`` httpOnly
 * cookie set by the backend on a successful login or registration.
 */
class DostupAuthService {
  static async login(payload: DostupLoginPayload): Promise<DostupPublicUser> {
    const { data } = await openHands.post<DostupPublicUser>(
      "/api/v1/auth/login",
      payload,
      { withCredentials: true },
    );
    return data;
  }

  static async register(
    payload: DostupRegisterPayload,
  ): Promise<DostupPublicUser> {
    const { data } = await openHands.post<DostupPublicUser>(
      "/api/v1/auth/register",
      payload,
      { withCredentials: true },
    );
    return data;
  }

  static async logout(): Promise<void> {
    await openHands.post("/api/v1/auth/logout", undefined, {
      withCredentials: true,
    });
  }

  static async me(): Promise<DostupPublicUser> {
    const { data } = await openHands.get<DostupPublicUser>("/api/v1/auth/me", {
      withCredentials: true,
    });
    return data;
  }
}

export default DostupAuthService;
