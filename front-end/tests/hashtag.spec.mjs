import {test, expect} from "@playwright/test";
import {loginAsSample} from "./test-utils.mjs";

// Regression tests for issue #3: "Hashtag slowing down my browser"
// Root cause: hashtagView fired getBloomsByHashtag() without awaiting it.
// When the API resolved it triggered state-change → handleRouteChange →
// hashtagView again → another fetch → infinite loop. destroy() on every
// iteration caused the blank flash.

test.describe("Hashtag view (issue #3)", () => {
  test("navigating to a hashtag fetches data exactly once", async ({page}) => {
    await loginAsSample(page);
    // Wait for all login-related API calls to settle before we start counting
    // hashtag fetches. getBlooms must have resolved (timeline visible) so no
    // pending state-change events can fire while the hashtag fetch is in-flight.
    await expect(
      page.locator("#timeline-container [data-bloom]").first()
    ).toBeVisible();

    let hashtagFetchCount = 0;
    await page.route("http://localhost:3000/hashtag/**", (route) => {
      hashtagFetchCount++;
      route.continue();
    });

    await page.evaluate(() => {
      window.location.hash = "#/hashtag/SwizBiz";
    });

    await expect(page.locator("[data-heading]")).toHaveText("#SwizBiz");
    // Allow extra time for any re-render loop to manifest
    await page.waitForTimeout(300);

    expect(hashtagFetchCount).toBe(1);
  });

  test("hashtag heading and blooms are visible and stable after navigation", async ({page}) => {
    await loginAsSample(page);
    await page.evaluate(() => {
      window.location.hash = "#/hashtag/SwizBiz";
    });

    await expect(page.locator("[data-heading]")).toHaveText("#SwizBiz");
    await expect(
      page.locator("#timeline-container [data-bloom]").first()
    ).toBeVisible();

    // Heading must still be present after settling — a flashing loop would
    // destroy it repeatedly, leaving it blank or absent.
    await page.waitForTimeout(300);
    await expect(page.locator("[data-heading]")).toHaveText("#SwizBiz");
  });
});
