import type { Config } from "@react-router/dev/config";

// NOTE: No buildEnd unpack — the server serves directly from build/client/.
// This avoids EPERM rename failures on Windows where the target directory
// may be locked by VSCode, Defender, or other processes.

export default {
  appDirectory: "src",
  ssr: false,
} satisfies Config;
