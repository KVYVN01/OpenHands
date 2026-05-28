import React from "react";
import {
  useRouteError,
  isRouteErrorResponse,
  Outlet,
  useLocation,
} from "react-router";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import i18n from "#/i18n";
import { useIsAuthed } from "#/hooks/query/use-is-authed";
import { useConfig } from "#/hooks/query/use-config";
import { Sidebar } from "#/components/features/sidebar/sidebar";
import { ReauthModal } from "#/components/features/waitlist/reauth-modal";
import { AnalyticsConsentFormModal } from "#/components/features/analytics/analytics-consent-form-modal";
import { useSettings } from "#/hooks/query/use-settings";
import { useMigrateUserConsent } from "#/hooks/use-migrate-user-consent";
import { displaySuccessToast } from "#/utils/custom-toast-handlers";
import { useIsOnIntermediatePage } from "#/hooks/use-is-on-intermediate-page";
import { useReoTracking } from "#/hooks/use-reo-tracking";
import { useSyncPostHogConsent } from "#/hooks/use-sync-posthog-consent";
import { useAutoSelectOrganization } from "#/hooks/use-auto-select-organization";
import { EmailVerificationGuard } from "#/components/features/guards/email-verification-guard";
import { OnboardingGuard } from "#/components/features/guards/onboarding-guard";
import { AlertBanner } from "#/components/features/alerts/alert-banner";
import { cn } from "#/utils/utils";
import { LoadingSpinner } from "#/components/shared/loading-spinner";
import { useAppTitle } from "#/hooks/use-app-title";
import { useInvitation } from "#/hooks/use-invitation";
import { InvitationAcceptModal } from "#/components/features/invitations/invitation-accept-modal";
import { useSwitchOrganization } from "#/hooks/mutation/use-switch-organization";

export function ErrorBoundary() {
  const error = useRouteError();
  const { t } = useTranslation();

  if (isRouteErrorResponse(error)) {
    return (
      <div>
        <h1>{error.status}</h1>
        <p>{error.statusText}</p>
        <pre>
          {error.data instanceof Object
            ? JSON.stringify(error.data)
            : error.data}
        </pre>
      </div>
    );
  }
  if (error instanceof Error) {
    return (
      <div>
        <h1>{t(I18nKey.ERROR$GENERIC)}</h1>
        <pre>{error.message}</pre>
      </div>
    );
  }

  return (
    <div>
      <h1>{t(I18nKey.ERROR$UNKNOWN)}</h1>
    </div>
  );
}

export default function MainApp() {
  const appTitle = useAppTitle();
  const { pathname } = useLocation();
  const isOnIntermediatePage = useIsOnIntermediatePage();
  const { data: settings } = useSettings();
  const { migrateUserConsent } = useMigrateUserConsent();
  const { t } = useTranslation();

  const config = useConfig();
  const {
    data: isAuthed,
    isFetching: isFetchingAuth,
    isError: isAuthError,
    isLoading: isAuthLoading,
  } = useIsAuthed();

  const [consentFormIsOpen, setConsentFormIsOpen] = React.useState(false);

  // Invitation acceptance modal state
  const { invitationToken, clearInvitation } = useInvitation();
  const { mutate: switchOrganization } = useSwitchOrganization();
  const [showInvitationModal, setShowInvitationModal] = React.useState(false);

  // Initialize Reo.dev tracking in SaaS mode
  useReoTracking();

  // Sync PostHog opt-in/out state with backend setting on mount
  useSyncPostHogConsent();

  // Auto-select the first organization when none is selected
  useAutoSelectOrganization();

  React.useEffect(() => {
    // Don't change language when on intermediate pages (TOS, profile questions)
    if (!isOnIntermediatePage && settings?.language) {
      i18n.changeLanguage(settings.language);
    }
  }, [settings?.language, isOnIntermediatePage]);

  React.useEffect(() => {
    // Don't show consent form when on intermediate pages
    if (!isOnIntermediatePage) {
      const consentFormModalIsOpen =
        settings?.user_consents_to_analytics === null;

      setConsentFormIsOpen(consentFormModalIsOpen);
    }
  }, [settings, isOnIntermediatePage]);

  React.useEffect(() => {
    // Don't migrate user consent when on intermediate pages
    if (!isOnIntermediatePage) {
      // Migrate user consent to the server if it was previously stored in localStorage
      migrateUserConsent({
        handleAnalyticsWasPresentInLocalStorage: () => {
          setConsentFormIsOpen(false);
        },
      });
    }
  }, [isOnIntermediatePage]);

  React.useEffect(() => {
    if (settings?.is_new_user && config.data?.app_mode === "saas") {
      displaySuccessToast(t(I18nKey.BILLING$YOURE_IN));
    }
  }, [settings?.is_new_user, config.data?.app_mode]);

  // Show invitation modal when authenticated and has invitation token
  React.useEffect(() => {
    if (isAuthed && invitationToken && !isOnIntermediatePage) {
      setShowInvitationModal(true);
    }
  }, [isAuthed, invitationToken, isOnIntermediatePage]);

  const handleInvitationClose = React.useCallback(() => {
    setShowInvitationModal(false);
    clearInvitation();
  }, [clearInvitation]);

  const handleInvitationSuccess = React.useCallback(
    (payload: { orgId: string; orgName: string; isPersonal: boolean }) => {
      setShowInvitationModal(false);
      clearInvitation();
      // Switch to the newly joined organization
      switchOrganization(payload);
    },
    [clearInvitation, switchOrganization],
  );

  // The dedicated /login page has been removed. We no longer redirect
  // unauthenticated users to a login screen — SaaS deployments are expected
  // to terminate authentication at the gateway/IDP before traffic reaches
  // the React app, and OSS mode never required login in the first place.
  // We still surface a reauth modal in SaaS mode if the cookie expires.
  const isLoading = config.isLoading || isAuthLoading;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-base">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  const renderReAuthModal =
    !isAuthed &&
    !isAuthError &&
    !isFetchingAuth &&
    !isOnIntermediatePage &&
    config.data?.app_mode === "saas";

  return (
    <div
      data-testid="root-layout"
      className={cn(
        "h-screen lg:min-w-5xl flex flex-col md:flex-row bg-base overflow-hidden",
        pathname === "/" ? "p-0" : "p-0 md:p-3 md:pl-0",
      )}
    >
      <title>{appTitle}</title>
      <Sidebar />

      <div className="flex flex-col w-full min-w-0 h-[calc(100%-50px)] md:h-full gap-3">
        {config.data &&
          (config.data.maintenance_start_time ||
            (config.data.faulty_models &&
              config.data.faulty_models.length > 0) ||
            config.data.error_message) && (
            <AlertBanner
              maintenanceStartTime={config.data.maintenance_start_time}
              faultyModels={config.data.faulty_models}
              errorMessage={config.data.error_message}
              updatedAt={config.data.updated_at}
            />
          )}
        <div
          id="root-outlet"
          className="flex-1 relative overflow-auto custom-scrollbar"
        >
          <OnboardingGuard>
            <EmailVerificationGuard>
              <Outlet />
            </EmailVerificationGuard>
          </OnboardingGuard>
        </div>
      </div>

      {renderReAuthModal && <ReauthModal />}
      {config.data?.app_mode === "oss" && consentFormIsOpen && (
        <AnalyticsConsentFormModal
          onClose={() => {
            setConsentFormIsOpen(false);
          }}
        />
      )}
      {showInvitationModal && invitationToken && (
        <InvitationAcceptModal
          token={invitationToken}
          onClose={handleInvitationClose}
          onSuccess={handleInvitationSuccess}
        />
      )}
    </div>
  );
}
