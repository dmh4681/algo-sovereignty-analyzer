# Favicon Installation Instructions

## Files Generated

All favicon files have been created and are ready to use:

- `favicon.ico` - Multi-resolution ICO file (16x16, 32x32, 48x48)
- `favicon-16x16.png` - Tiny browser tab icon
- `favicon-32x32.png` - Standard browser tab icon
- `favicon-96x96.png` - High-DPI browser tab icon
- `apple-touch-icon.png` - iOS home screen icon (180x180)
- `android-chrome-192x192.png` - Android home screen icon
- `android-chrome-512x512.png` - High-res Android icon
- `manifest.json` - PWA manifest for installable web app

## Installation Steps

### 1. Copy Files to Next.js Public Directory

```bash
# From your project root
cp favicon_output/* web/public/
```

This places all favicon files in the `web/public/` directory where Next.js can serve them.

### 2. Update Your Layout File

Add the favicon meta tags to `web/app/layout.tsx`:

```tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Algorand Sovereignty Analyzer',
  description: 'Measure your financial sovereignty. Analyze any Algorand wallet and calculate your freedom.',
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
      { url: '/favicon-96x96.png', sizes: '96x96', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
  },
  manifest: '/manifest.json',
  themeColor: '#f97316',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <meta name="theme-color" content="#f97316" />
        <meta name="msapplication-TileColor" content="#0f172a" />
      </head>
      <body>{children}</body>
    </html>
  )
}
```

### 3. Verify Installation

After running `npm run dev`:

1. **Browser tab:** Should show the orange "A" logo
2. **Mobile add to home screen:** Should use proper icon
3. **PWA install:** Should offer installable app experience

## What Each File Does

| File | Purpose | Used By |
|------|---------|---------|
| `favicon.ico` | Legacy browser support | Old browsers, Windows |
| `favicon-16x16.png` | Browser tabs | Chrome, Firefox, Edge |
| `favicon-32x32.png` | Browser tabs (retina) | High-DPI displays |
| `favicon-96x96.png` | Desktop shortcuts | Windows, Linux |
| `apple-touch-icon.png` | iOS home screen | iPhone, iPad |
| `android-chrome-192x192.png` | Android home screen | Android devices |
| `android-chrome-512x512.png` | Android splash screen | PWA install |
| `manifest.json` | PWA configuration | Installable web app |

## Testing Checklist

- [ ] Favicon appears in browser tab
- [ ] Favicon appears in bookmarks
- [ ] iOS "Add to Home Screen" shows correct icon
- [ ] Android "Add to Home Screen" shows correct icon
- [ ] Theme color matches app (orange #f97316)
- [ ] No 404 errors in browser console for favicon files

## Notes

- The orange "A" with upward arrow symbolizes Algorand + sovereignty/growth
- Color scheme matches your app: Orange (#f97316) primary, Emerald (#10b981) accent, Dark slate (#0f172a) background
- All files optimized for web (file sizes kept minimal)
- PWA-ready with manifest.json for installable app experience

---

**All files are ready to use!** Just copy them to `web/public/` when your Next.js app is set up.
