/* eslint-disable jsx-a11y/anchor-is-valid -- placeholder anchors after URL scrub for DOSTUP_CRS */
import { useTranslation } from "react-i18next";
import { I18nKey } from "#/i18n/declaration";

interface TOSCheckboxProps {
  onChange: () => void;
}

export function TOSCheckbox({ onChange }: TOSCheckboxProps) {
  const { t } = useTranslation();
  return (
    <label className="flex items-center gap-2">
      <input type="checkbox" onChange={onChange} />
      <span>
        {t(I18nKey.TOS$ACCEPT)}{" "}
        <a
          href="#"
          target="_blank"
          rel="noopener noreferrer"
          className="underline underline-offset-2 text-blue-500 hover:text-blue-700"
        >
          {t(I18nKey.TOS$TERMS)}
        </a>
      </span>
    </label>
  );
}
