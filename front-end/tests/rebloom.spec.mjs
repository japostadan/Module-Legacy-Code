import {test, expect} from "@playwright/test";
import {loginAsSample} from "./test-utils.mjs";

// Tests for issue #9: Rebloom feature.
// JustSomeGuy posts a bloom; sample navigates to JustSomeGuy's profile to rebloom it.

test.describe.configure({mode: "serial"});
test.describe("Rebloom (issue #9)", () => {
  let originalBloomId;

  test.beforeAll(async ({request}) => {
    const loginResp = await request.post("http://localhost:3000/login", {
      data: {username: "JustSomeGuy", password: "mysterious"},
    });
    const {token} = await loginResp.json();
    await request.post("http://localhost:3000/bloom", {
      data: {content: "Rebloom this bloom!"},
      headers: {Authorization: `Bearer ${token}`},
    });
    const bloomsResp = await request.get("http://localhost:3000/blooms/JustSomeGuy");
    const blooms = await bloomsResp.json();
    originalBloomId = blooms[0].id;
  });

  test("rebloom button is visible on each bloom", async ({page}) => {
    await loginAsSample(page);
    await expect(
      page.locator("[data-bloom] [data-action='rebloom']").first()
    ).toBeVisible();
  });

  test("rebloomed bloom appears in rebloomer's profile", async ({page}) => {
    await loginAsSample(page);
    await page.goto("/#/profile/JustSomeGuy");

    const rebloomButton = page.locator(`[data-bloom-id='${originalBloomId}'] [data-action='rebloom']`);
    await expect(rebloomButton).toBeVisible();
    await rebloomButton.click();

    // After rebloom, go to sample's profile to see the rebloomed entry
    await page.goto("/#/profile/sample");
    await expect(
      page.locator("#timeline-container [data-rebloom-attribution]").filter({hasText: "JustSomeGuy"}).first()
    ).toBeVisible();
  });

  test("rebloom attribution shows original sender", async ({page}) => {
    await loginAsSample(page);
    await page.goto("/#/profile/sample");

    const attribution = page.locator("[data-rebloom-attribution]").filter({hasText: "JustSomeGuy"}).first();
    await expect(attribution).toBeVisible();
    await expect(attribution.locator("[data-original-sender]")).toHaveText("JustSomeGuy");
  });
});
