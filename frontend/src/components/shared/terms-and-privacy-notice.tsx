/* eslint-disable jsx-a11y/anchor-is-valid -- placeholder anchors after URL scrub for DOSTUP_CRS */
import React from "react";
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";
import { cn } from "#/utils/utils";

interface TermsAndPrivacyNoticeProps {
  className?: string;
}

export function TermsAndPrivacyNotice({
  className,
}: TermsAndPrivacyNoticeProps) {
  const { t } = useTranslation();

  return (
    <p
      className={cn("text-xs text-center text-muted-foreground", className)}
      data-testid="terms-and-privacy-notice"
    >
      {t(I18nKey.AUTH$BY_SIGNING_UP_YOU_AGREE_TO_OUR)}{" "}
      <a
        href="#"
        target="_blank"
        className="underline hover:text-primary"
        rel="noopener noreferrer"
      >
        {t(I18nKey.COMMON$TERMS_OF_SERVICE)}
      </a>{" "}
      {t(I18nKey.COMMON$AND)}{" "}
      <a
        href="#"
        target="_blank"
        className="underline hover:text-primary"
        rel="noopener noreferrer"
      >
        {t(I18nKey.COMMON$PRIVACY_POLICY)}
      </a>
      .
    </p>
  );
}
