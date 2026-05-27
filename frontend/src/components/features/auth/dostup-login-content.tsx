import React from "react";
import { useNavigate } from "react-router";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import DostupAuthService, {
  DostupPublicUser,
} from "#/api/auth-service/dostup-auth-service.api";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";

type Mode = "login" | "register";

type AxiosErrorLike = {
  response?: {
    data?:
      | string
      | {
          detail?:
            | string
            | Array<{ loc?: unknown[]; msg?: string; type?: string }>;
          message?: string;
        };
  };
  message?: string;
};

function extractErrorMessage(caught: unknown): string {
  const err = caught as AxiosErrorLike;
  const data = err?.response?.data;
  if (typeof data === "string") return data;
  if (data && typeof data === "object") {
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      // FastAPI / pydantic validation errors are an array of objects.
      // Surface the human-readable `msg` field.
      const first = data.detail[0];
      if (first?.msg) return first.msg;
    }
    if (typeof data.message === "string") return data.message;
  }
  if (caught instanceof Error) return caught.message;
  return "Unknown error";
}

function submitButtonLabel(
  isSubmitting: boolean,
  mode: Mode,
  t: (key: I18nKey) => string,
) {
  if (isSubmitting) return t(I18nKey.LANDING$BUSY);
  if (mode === "login") return t(I18nKey.LANDING$ACTION_SIGN_IN);
  return t(I18nKey.LANDING$ACTION_CREATE_ACCOUNT);
}

interface DostupLoginContentProps {
  returnTo: string;
}

const inputClasses = cn(
  "w-full rounded-md bg-neutral-900/60 border border-neutral-700",
  "px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500",
  "outline-none focus:border-emerald-500/70 focus:ring-2 focus:ring-emerald-500/20",
  "transition-colors",
);

const buttonClasses = cn(
  "w-full inline-flex items-center justify-center rounded-md",
  "bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-medium",
  "px-3 py-2 text-sm transition-colors",
  "disabled:opacity-50 disabled:cursor-not-allowed",
);

const ghostButtonClasses = cn(
  "inline-flex items-center justify-center rounded-md",
  "border border-neutral-700 hover:border-neutral-500 text-neutral-200",
  "px-3 py-1.5 text-xs transition-colors",
);

const fieldLabelClasses = "text-xs font-medium text-neutral-400";

export function DostupLoginContent({ returnTo }: DostupLoginContentProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [mode, setMode] = React.useState<Mode>("login");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [displayName, setDisplayName] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  const onSubmit: React.FormEventHandler<HTMLFormElement> = async (event) => {
    event.preventDefault();
    if (isSubmitting) return;
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      let user: DostupPublicUser;
      if (mode === "login") {
        user = await DostupAuthService.login({ email, password });
      } else {
        user = await DostupAuthService.register({
          email,
          password,
          display_name: displayName.trim() || undefined,
        });
      }

      // Refresh the auth caches so the rest of the app sees the new session.
      await queryClient.invalidateQueries({ queryKey: ["user"] });
      // Stash a tiny hint so the post-login experience can greet the user
      // even before /me round-trips. This is purely cosmetic.
      try {
        window.sessionStorage?.setItem(
          "dostup:last-user",
          JSON.stringify({
            email: user.email,
            display_name: user.display_name,
          }),
        );
      } catch {
        // ignore storage errors (e.g. private mode)
      }
      navigate(returnTo, { replace: true });
    } catch (caught) {
      setErrorMessage(extractErrorMessage(caught));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      data-testid="dostup-login-card"
      className={cn(
        "relative w-full max-w-md rounded-2xl border border-neutral-800",
        "bg-neutral-950/80 shadow-2xl shadow-black/40 backdrop-blur",
        "p-8 space-y-6",
      )}
    >
      <header className="space-y-2 text-center">
        <div className="flex items-center justify-center gap-2 text-emerald-400">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.7)]" />
          <span className="text-[11px] uppercase tracking-[0.4em] text-neutral-400">
            {t(I18nKey.LANDING$INTERNAL_AGENT_PLATFORM)}
          </span>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-50">
          DOSTUP_CRS
        </h1>
        <p className="text-sm text-neutral-400">
          {mode === "login"
            ? t(I18nKey.LANDING$SIGN_IN_SUBTITLE)
            : t(I18nKey.LANDING$CREATE_ACCOUNT_SUBTITLE)}
        </p>
      </header>

      <div className="flex rounded-md border border-neutral-800 bg-neutral-900/60 p-1">
        {(["login", "register"] as Mode[]).map((value) => (
          <button
            key={value}
            type="button"
            onClick={() => {
              setMode(value);
              setErrorMessage(null);
            }}
            className={cn(
              "flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
              mode === value
                ? "bg-neutral-800 text-neutral-50"
                : "text-neutral-400 hover:text-neutral-200",
            )}
          >
            {value === "login"
              ? t(I18nKey.LANDING$TAB_SIGN_IN)
              : t(I18nKey.LANDING$TAB_CREATE_ACCOUNT)}
          </button>
        ))}
      </div>

      <form className="space-y-4" onSubmit={onSubmit}>
        {mode === "register" && (
          <label className="block space-y-1">
            <span className={fieldLabelClasses}>
              {t(I18nKey.LANDING$FIELD_DISPLAY_NAME)}
            </span>
            <input
              type="text"
              autoComplete="name"
              className={inputClasses}
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              maxLength={160}
              placeholder=""
            />
          </label>
        )}

        <label className="block space-y-1">
          <span className={fieldLabelClasses}>
            {t(I18nKey.LANDING$FIELD_EMAIL)}
          </span>
          <input
            type="email"
            required
            autoComplete="email"
            className={inputClasses}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            maxLength={320}
          />
        </label>

        <label className="block space-y-1">
          <span className={fieldLabelClasses}>
            {t(I18nKey.LANDING$FIELD_PASSWORD)}
          </span>
          <input
            type="password"
            required
            minLength={8}
            autoComplete={
              mode === "login" ? "current-password" : "new-password"
            }
            className={inputClasses}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {mode === "register" && (
            <span className="text-[11px] text-neutral-500">
              {t(I18nKey.LANDING$PASSWORD_HINT)}
            </span>
          )}
        </label>

        {errorMessage && (
          <div
            role="alert"
            data-testid="dostup-login-error"
            className="rounded-md border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-xs text-rose-300"
          >
            {errorMessage}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className={buttonClasses}
          data-testid="dostup-login-submit"
        >
          {submitButtonLabel(isSubmitting, mode, t)}
        </button>
      </form>

      <footer className="flex items-center justify-between text-[11px] text-neutral-500">
        <span>{t(I18nKey.LANDING$LOCAL_DEPLOYMENT_NOTICE)}</span>
        <button
          type="button"
          className={ghostButtonClasses}
          onClick={() => {
            setMode(mode === "login" ? "register" : "login");
            setErrorMessage(null);
          }}
        >
          {mode === "login"
            ? t(I18nKey.LANDING$TAB_CREATE_ACCOUNT)
            : t(I18nKey.LANDING$TAB_SIGN_IN)}
        </button>
      </footer>
    </div>
  );
}
