# Email deliverability (MicroDegree Weekly)

If mail lands in **Spam** (especially for `@microdegree.work` Google Workspace), fix **DNS + reputation** first. Code changes help, but they cannot replace authentication.

## 1. AWS SES (required)

In **AWS SES → Verified identities → `mdegree.in`**:

- [ ] Domain **verified**
- [ ] **DKIM** enabled (3 CNAME records in DNS)
- [ ] **MAIL FROM** domain configured (recommended: `mail.mdegree.in`)
- [ ] **Custom MAIL FROM** SPF record published
- [ ] Account out of **sandbox** (production access)
- [ ] No **Configuration Set** with open/click tracking enabled (tracking pixels trigger Gmail “tracking signatures”)

## 2. DNS records for `mdegree.in`

Add in your DNS provider (where `mdegree.in` is hosted):

| Type | Purpose |
|------|---------|
| TXT (SPF) | Authorize Amazon SES to send |
| CNAME ×3 | DKIM keys from SES console |
| TXT (DMARC) | `v=DMARC1; p=none; rua=mailto:tech@mdegree.in` (start with `p=none`, tighten later) |

Example SPF (adjust if you already send mail from this domain):

```txt
v=spf1 include:amazonses.com ~all
```

After DNS propagates, send a test and check headers in Gmail → **Show original**:

- `spf=pass`
- `dkim=pass`
- `dmarc=pass`

## 3. Google Workspace (`@microdegree.work`)

For internal recipients (e.g. founder):

1. Admin console → **Apps → Google Workspace → Gmail → Spam**
2. Add **approved sender**: `tech@mdegree.in` or `@mdegree.in`
3. Ask the user to mark one message **Not spam** (trains their mailbox)

## 4. Content practices (already in code)

- Plain text + HTML multipart
- `List-Unsubscribe` + one-click unsubscribe
- Minimal job layout (text links, no “Apply Now” buttons)
- No hidden preheader blocks
- No image scraping for weekly builds

## 5. Test send

```bash
python runners/run_mass_weekly_test.py someone@microdegree.work
```

Check **Show original** before asking users to look in Inbox.
