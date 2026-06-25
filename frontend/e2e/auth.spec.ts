import { test, expect } from '@playwright/test';

test.describe('Smoke Test', () => {
  test('should load the home page successfully', async ({ page }) => {
    // Navigate to the base URL (http://localhost:5173/)
    await page.goto('/');

    // Assert that the page title is correct
    await expect(page).toHaveTitle(/Prompt Arena/i);

    // Assert that the heading containing "Prompt Arena" is visible
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toHaveText('Prompt Arena');

    // Assert that the welcome message is visible
    const welcome = page.locator('#welcome-message');
    await expect(welcome).toBeVisible();
    await expect(welcome).toHaveText('Welcome to Prompt Arena');
  });
});
