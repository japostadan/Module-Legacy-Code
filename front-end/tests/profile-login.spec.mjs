import {test, expect} from "@playwright/test";
import {loginAsSample, logout} from "./test-utils.mjs";

// Regression test for issue #6: "Can't log in from profile page".
// After viewing another user's profile and logging out, the login form is
// re-rendered on the profile route. Submitting it must log the user back in,
// not trigger a native form POST to the static server (which 501s / 405s).
test.describe("Login from the profile page (issue #6)", () => {
  test("logs back in after viewing a profile and logging out", async ({
    page,
  }) => {
    await page.goto("/");
    await loginAsSample(page);
    await expect(
      page.locator("#logout-container [data-logout-button]")
    ).toBeVisible();

    // View another user's profile via the hash router.
    await page.evaluate(() => {
      window.location.hash = "#/profile/AS";
    });
    await expect(page.locator("#profile-container .profile")).toBeVisible();

    // Log out while still on the profile route — this re-renders the login form
    // on the profile page.
    await logout(page);
    // Wait for the logged-out profile to finish re-rendering (the async profile
    // fetch re-renders the login form, so settle before interacting with it).
    await expect(page.locator("#profile-container .profile")).toBeVisible();
    await expect(page.locator('[data-form="login"]')).toBeVisible();

    // Submit the login form from the profile page.
    await page.fill('[data-form="login"] input[name="username"]', "sample");
    await page.fill('[data-form="login"] input[name="password"]', "sosecret");
    await page.click('[data-form="login"] [data-submit]');

    // We should be logged back in, still inside the SPA — not on a server
    // error page from a native POST.
    await expect(
      page.locator("#logout-container [data-logout-button]")
    ).toBeVisible();
  });
});
