declare global {
  interface Window {
    grecaptcha: {
      ready: (cb: () => void) => void;
      execute: (siteKey: string, options: { action: string }) => Promise<string>;
    };
  }
}

const SITE_KEY = process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || "";

export async function getRecaptchaToken(action: string): Promise<string> {
  if (!SITE_KEY) return "";

  return new Promise((resolve) => {
    if (typeof window === "undefined" || !window.grecaptcha) {
      resolve("");
      return;
    }
    window.grecaptcha.ready(() => {
      window.grecaptcha
        .execute(SITE_KEY, { action })
        .then(resolve)
        .catch(() => resolve(""));
    });
  });
}
