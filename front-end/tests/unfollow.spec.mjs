import {test, expect} from "@playwright/test";
import {loginAsJustSomeGuy} from "./test-utils.mjs";

// Tests for issue #8: Unfollow feature.

test.describe("Unfollow (issue #8)", () => {
  test.beforeEach(async ({request}) => {
    // Reset: ensure JustSomeGuy is not following sample before each test.
    const loginResp = await request.post("http://localhost:3000/login", {
      data: {username: "JustSomeGuy", password: "mysterious"},
    });
    const {token} = await loginResp.json();
    await request.post("http://localhost:3000/unfollow/sample", {
      headers: {Authorization: `Bearer ${token}`},
    });
  });
  test("follow button is visible on a profile you do not follow", async ({
    page,
  }) => {
    await loginAsJustSomeGuy(page);
    await page.goto("/#/profile/sample");
    await expect(
      page.locator("#profile-container .profile > .profile__actions [data-action='follow']")
    ).toBeVisible();
  });

  test("unfollow button appears after following a user", async ({page}) => {
    await loginAsJustSomeGuy(page);
    await page.goto("/#/profile/sample");

    await page.click("#profile-container .profile > .profile__actions [data-action='follow']");

    await expect(
      page.locator("#profile-container .profile > .profile__actions [data-action='unfollow']")
    ).toBeVisible();
    await expect(
      page.locator("#profile-container .profile > .profile__actions [data-action='follow']")
    ).toBeHidden();
  });

  test("follow button reappears after unfollowing", async ({page}) => {
    await loginAsJustSomeGuy(page);
    await page.goto("/#/profile/sample");

    // Follow then unfollow
    await page.click("#profile-container .profile > .profile__actions [data-action='follow']");
    await expect(
      page.locator("#profile-container .profile > .profile__actions [data-action='unfollow']")
    ).toBeVisible();

    await page.click("#profile-container .profile > .profile__actions [data-action='unfollow']");

    await expect(
      page.locator("#profile-container .profile > .profile__actions [data-action='follow']")
    ).toBeVisible();
    await expect(
      page.locator("#profile-container .profile > .profile__actions [data-action='unfollow']")
    ).toBeHidden();
  });
});
