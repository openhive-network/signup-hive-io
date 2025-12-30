# CLAUDE.md - signup-hive-io

## Project Overview

Static landing page for Hive blockchain account signup at `signup.hive.io`. Aggregates multiple community-run account creation services, educates users about Hive accounts, and guides them to appropriate signup providers based on their needs (free vs paid, instant vs delayed, verification requirements).

## Tech Stack

- **HTML5** - Single-page static site (no framework)
- **Bootstrap 4.0.0** - CSS framework (via CDN + local override)
- **jQuery 3.3.1** - DOM manipulation (via CDN)
- **Vanilla JavaScript** - UTM parameter propagation, dynamic pricing
- **Google Tag Manager** - Analytics (GTM-5CCQXK9)
- **AWS S3 + CloudFront** - Hosting and CDN

No build tools, package managers, or transpilers - pure static site.

## Directory Structure

```
signup-hive-io/
├── index.html           # Main landing page (complete SPA)
├── bootstrap.min.css    # Bootstrap CSS customization
├── favicon.ico          # Browser icon
├── images/
│   ├── members.svg      # Hero section image
│   └── star.svg         # Decorative element
├── .gitlab-ci.yml       # CI/CD pipeline
└── README.md            # Brief description
```

## Development Commands

No build process required. For local development:

```bash
# Serve locally
python3 -m http.server 8000

# Or use any static file server
npx serve .
```

Direct edit `index.html` for changes.

## Key Files

| File | Purpose |
|------|---------|
| `index.html` | Main page - all content, styles, and JS inline |
| `bootstrap.min.css` | Bootstrap framework CSS |
| `.gitlab-ci.yml` | S3 deployment pipeline |

## Coding Conventions

**HTML/CSS:**
- Bootstrap grid system (12-column)
- Card-based UI for signup providers
- Inline `<style>` tag for custom CSS
- Mobile-first responsive design

**JavaScript:**
- Vanilla JS only, no framework
- IIFE pattern for scope isolation
- Fetch API with try-catch for API calls
- DOM manipulation via getElementById/querySelectorAll

**Color scheme:**
- Primary: `#e31337` (Hive red)
- Dark: `#212529` (nav, footer)

## CI/CD Notes

**Branches:**
- `develop` → deploys to staging (`signup-staging.hive.io`)
- `master` → deploys to production (`signup.hive.io`)

**Pipeline stages:**
1. `deploy_staging` - S3 sync to staging bucket
2. `deploy_master` - S3 sync to production + CloudFront invalidation

**Required CI variables:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `S3_BUCKET_NAME_STAGING`
- `S3_BUCKET_NAME_PRODUCTION`
- `DISTRIBUTION_ID` (CloudFront)

**Excluded from deployment:** `.git/`, `.gitlab-ci.yml`, `README.md`

## External APIs

- **Hivedex API** (`https://api2.hivedex.io/price`) - Dynamic pricing display
- **Google Tag Manager** - Analytics tracking

## Adding/Removing Signup Providers

Edit `index.html` and find the signup provider cards section. Each provider is a Bootstrap card with:
- Logo/icon
- Name and description
- Features list
- Signup button link

Update UTM domain list in the script section if adding new provider domains.
