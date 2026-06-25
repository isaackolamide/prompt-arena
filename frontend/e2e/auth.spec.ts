import { test, expect } from '@playwright/test';

test.describe('Auth Flow', () => {
  test('should load the home page successfully', async ({ page }) => {
    await page.goto('/');

    // Assert that the heading containing "Prompt Arena" is visible
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toHaveText('Prompt Arena');

    // Assert that the welcome message is visible
    const welcome = page.locator('#welcome-message');
    await expect(welcome).toBeVisible();
    await expect(welcome).toHaveText('Welcome to Prompt Arena');
  });

  test('should register a new user successfully', async ({ page }) => {
    await page.goto('/');

    const uniqueId = Date.now();
    const username = `user_${uniqueId}`;
    const email = `user_${uniqueId}@example.com`;
    const password = 'password123';

    // Fill in registration form
    await page.fill('#register-username', username);
    await page.fill('#register-email', email);
    await page.fill('#register-password', password);

    // Submit registration form
    await page.click('#register-submit');

    // Verify success status
    const status = page.locator('#auth-status');
    await expect(status).toBeVisible();
    await expect(status).toHaveText('Registration successful');
  });

  test('should log in successfully with registered credentials', async ({ page }) => {
    await page.goto('/');

    const uniqueId = Date.now() + 1;
    const username = `user_${uniqueId}`;
    const email = `user_${uniqueId}@example.com`;
    const password = 'password123';

    // Register this user first so they exist
    await page.fill('#register-username', username);
    await page.fill('#register-email', email);
    await page.fill('#register-password', password);
    await page.click('#register-submit');

    // Wait for registration success status
    const status = page.locator('#auth-status');
    await expect(status).toHaveText('Registration successful');

    // Now attempt to log in
    await page.fill('#login-email', email);
    await page.fill('#login-password', password);
    await page.click('#login-submit');

    // Verify successful login status
    await expect(status).toHaveText(`Logged in as ${email}`);
  });
});
