/* eslint-disable jsx-a11y/anchor-is-valid -- placeholder anchors after URL scrub for DOSTUP_CRS */
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function AzureDevOpsTokenHelpAnchor() {
  const { t } = useTranslation();

  return (
    <p data-testid="azure-devops-token-help-anchor" className="text-xs">
      <a
        href="#"
        target="_blank"
        className="underline underline-offset-2"
        rel="noopener noreferrer"
        aria-label={t(I18nKey.GIT$AZURE_DEVOPS_TOKEN_HELP)}
      >
        {t(I18nKey.GIT$AZURE_DEVOPS_TOKEN_HELP)}
      </a>
    </p>
  );
}
