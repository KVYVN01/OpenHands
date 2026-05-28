/* eslint-disable jsx-a11y/anchor-is-valid -- placeholder anchors after URL scrub for DOSTUP_CRS */
import { Trans, useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

export function GitLabTokenHelpAnchor() {
  const { t } = useTranslation();

  return (
    <p data-testid="gitlab-token-help-anchor" className="text-xs">
      <Trans
        i18nKey={I18nKey.GITLAB$TOKEN_HELP_TEXT}
        components={[
          <a
            key="gitlab-token-help-anchor-link"
            aria-label={t(I18nKey.GIT$GITLAB_TOKEN_HELP_LINK)}
            href="#"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
          <a
            key="gitlab-token-help-anchor-link-2"
            aria-label={t(I18nKey.GIT$GITLAB_TOKEN_SEE_MORE_LINK)}
            href="#"
            target="_blank"
            className="underline underline-offset-2"
            rel="noopener noreferrer"
          />,
        ]}
      />
    </p>
  );
}
