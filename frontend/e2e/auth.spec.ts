import { test, expect } from '@playwright/test';

interface MailpitMessageSummary {
  ID: string;
  To: Array<{
    Name: string;
    Address: string;
  }> | null;
}

interface MailpitMessagesResponse {
  messages: MailpitMessageSummary[];
}

interface MailpitMessageDetail {
  ID: string;
  Text: string;
}

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

  test('should sign in successfully with magic link and OTP', async ({ page }) => {
    const uniqueId = Date.now();
    const email = `test_${uniqueId}@example.com`;

    await page.goto('/');

    // Fill in the email input
    await page.fill('#email-input', email);

    // Click the "Send Magic Link" button
    await page.click('#submit-email-button');

    // Verify status message changes to indicate success
    const statusMsg = page.locator('#auth-status');
    await expect(statusMsg).toContainText('Magic link sent successfully');

    // Poll Mailpit API to retrieve the OTP token
    let messageId: string | undefined;
    const startTime = Date.now();
    const timeout = 15000; // 15 seconds

    while (Date.now() - startTime < timeout) {
      try {
        const mailpitResponse = await page.request.get('http://localhost:54324/api/v1/messages');
        if (mailpitResponse.ok()) {
          const mailpitData = (await mailpitResponse.json()) as MailpitMessagesResponse;
          const msg = mailpitData.messages?.find((m) =>
            m.To?.some((to) => to.Address === email)
          );
          if (msg) {
            messageId = msg.ID;
            break;
          }
        }
      } catch (err) {
        // Ignore network errors during polling
      }
      await page.waitForTimeout(500);
    }

    if (!messageId) {
      throw new Error(`Email not received in Mailpit for ${email} within ${timeout}ms`);
    }

    // Retrieve message details
    const detailResponse = await page.request.get(
      `http://localhost:54324/api/v1/message/${messageId}`
    );
    if (!detailResponse.ok()) {
      throw new Error(`Failed to retrieve message details for ID ${messageId}`);
    }

    const detailData = (await detailResponse.json()) as MailpitMessageDetail;
    const emailText = detailData.Text;

    // Parse the token parameter from the URL
    const tokenMatch = emailText.match(/token=([a-f0-9]+)/);
    if (!tokenMatch) {
      throw new Error(`OTP/Magic link token not found in email body:\n${emailText}`);
    }
    const token = tokenMatch[1];

    // Input the extracted token into the OTP input field
    await page.fill('#otp-input', token);

    // Click the "Verify OTP" button
    await page.click('#submit-otp-button');

    // Verify dashboard welcome message appears and logout button is visible
    const welcomeTitle = page.locator('.welcome-title');
    await expect(welcomeTitle).toBeVisible();
    await expect(welcomeTitle).toContainText(`Welcome, ${email}!`);

    const logoutButton = page.locator('#logout-button');
    await expect(logoutButton).toBeVisible();
  });
});
