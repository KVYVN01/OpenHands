import { I18nKey } from "#/i18n/declaration";

export interface Tip {
  key: I18nKey;
  link?: string;
}

export const TIPS: Tip[] = [
  {
    key: I18nKey.TIPS$CUSTOMIZE_MICROAGENT,
    link: "#",
  },
  {
    key: I18nKey.TIPS$SETUP_SCRIPT,
    link: "#",
  },
  { key: I18nKey.TIPS$VSCODE_INSTANCE },
  { key: I18nKey.TIPS$SAVE_WORK },
  {
    key: I18nKey.TIPS$SPECIFY_FILES,
    link: "#",
  },
  {
    key: I18nKey.TIPS$HEADLESS_MODE,
    link: "#",
  },
  {
    key: I18nKey.TIPS$CLI_MODE,
    link: "#",
  },
  {
    key: I18nKey.TIPS$GITHUB_HOOK,
    link: "#",
  },
  {
    key: I18nKey.TIPS$BLOG_SIGNUP,
    link: "#",
  },
  {
    key: I18nKey.TIPS$API_USAGE,
    link: "#",
  },
];

export function getRandomTip(): Tip {
  const randomIndex = Math.floor(Math.random() * TIPS.length);
  return TIPS[randomIndex];
}
