# Ship It — digital product launch page

A fast, framework-free landing page that sells a downloadable ebook and
captures emails before the download. Pure HTML/CSS/JS — deploys anywhere
static, no build step.

```
index.html        the page + all copy (edit the EDIT ME blocks)
styles.css         theme + layout (change --brand to recolor everything)
script.js          form validation, email capture, download reveal
downloads/ebook.pdf  PLACEHOLDER — replace with your real ebook (keep the name)
netlify.toml       optional Netlify config
```

## Go live in 3 steps

1. **Drop in your real ebook.** Replace `downloads/ebook.pdf` with your file,
   keeping the same name (or change `CONFIG.downloadPath` in `script.js`).
2. **Turn on email capture.** Create a free form at https://formspree.io,
   copy your endpoint, and paste it into `CONFIG.formEndpoint` in `script.js`.
   (Leave it blank and the download still works — you just won't collect emails.)
3. **Deploy.** Any static host works:
   - **Netlify / Vercel:** import the repo, no settings needed.
   - **GitHub Pages:** repo Settings → Pages → deploy from branch root.

## Edit the copy

Open `index.html` and look for `EDIT ME` comments and the headline,
chapters, testimonials, and FAQ — swap in your product's real words.

## Preview locally

```
python3 -m http.server 8000
# open http://localhost:8000
```

## Next steps when you're ready to charge

The page is payment-ready by design. When you want to sell instead of give
it away, swap the email form for a Stripe Checkout / Gumroad / Lemon Squeezy
button and gate the download behind a successful payment.
