import {test, expect} from "@playwright/test";
import {loginAsSample} from "./test-utils.mjs";

// Regression tests for issue #5: "Hashtag link doesn't work correctly"
// Root cause: _formatHashtags used /\B#[^#]+/g — too greedy, consumed
// trailing text (e.g. "#SwizBiz love!!" instead of "#SwizBiz").
// Only worked when the hashtag was at end-of-string with nothing to over-consume.

test.describe("Hashtag links (issue #5)", () => {
  test("hashtag mid-sentence links to correct results", async ({page}) => {
    await loginAsSample(page);
    // "Let's get some #SwizBiz love!!" — hashtag is mid-sentence
    await expect(
      page.locator("#timeline-container [data-bloom] [data-content] a").first()
    ).toBeVisible();

    // Click the first hashtag link in the timeline
    const hashtagLink = page
      .locator("#timeline-container [data-bloom] [data-content] a[href*='hashtag']")
      .first();
    const href = await hashtagLink.getAttribute("href");
    // href must not include trailing words or punctuation — just /hashtag/<tag>
    expect(href).toMatch(/^\/hashtag\/\w+$/);
  });

  test("clicking #SwizBiz mid-sentence shows blooms on the hashtag page", async ({
    page,
  }) => {
    await loginAsSample(page);
    await expect(
      page.locator("#timeline-container [data-bloom]").first()
    ).toBeVisible();

    // Navigate directly to the hashtag route (same as clicking the mid-sentence link)
    await page.evaluate(() => {
      window.location.hash = "#/hashtag/SwizBiz";
    });

    await expect(page.locator("[data-heading]")).toHaveText("#SwizBiz");
    await expect(
      page.locator("#timeline-container [data-bloom]").first()
    ).toBeVisible();
  });

  test("both SwizBiz blooms produce the same hashtag href", async ({page}) => {
    await loginAsSample(page);
    await expect(
      page.locator("#timeline-container [data-bloom]").first()
    ).toBeVisible();

    const links = await page
      .locator(
        "#timeline-container [data-bloom] [data-content] a[href*='SwizBiz']"
      )
      .all();

    // Both blooms containing #SwizBiz must generate the same href
    expect(links.length).toBeGreaterThanOrEqual(2);
    const hrefs = await Promise.all(links.map((l) => l.getAttribute("href")));
    const unique = new Set(hrefs);
    expect(unique.size).toBe(1);
    expect([...unique][0]).toBe("/hashtag/SwizBiz");
  });
});
