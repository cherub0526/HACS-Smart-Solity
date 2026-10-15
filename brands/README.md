# Brand icon for the Smart Solity integration

Home Assistant does **not** load an integration's logo from inside
`custom_components/`. Brand images are served from the central
[home-assistant/brands](https://github.com/home-assistant/brands) repository.
Until they are published there, the integration shows a generic placeholder
icon — this is expected and does not affect functionality.

The app icon (extracted from the official app, `icon.png`, 512×512) has been
prepared here at the required sizes:

```
brands/custom_integrations/smart_solity/
├── icon.png       256×256
├── icon@2x.png    512×512
├── logo.png       256×256
└── logo@2x.png    512×512
```

## To make the icon appear in Home Assistant

1. Fork `home-assistant/brands`.
2. Copy `custom_integrations/smart_solity/` into the fork's
   `custom_integrations/` directory (same path).
3. Open a pull request. Once merged, HA fetches it automatically; the icon
   appears after the next brands CDN refresh (no integration update needed).

Note: the brands repo expects icons trimmed of transparent padding and square.
This source icon is a full-bleed square (blue background), which is accepted.
If the PR check requests a trimmed/transparent icon, regenerate from a
transparent-background source.
