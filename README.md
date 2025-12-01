# kvsankar's Blog

A Hugo-powered blog hosted on GitHub Pages.

## Setup

1. Install Hugo: https://gohugo.io/installation/

2. Clone this repo and add the theme:
   ```bash
   git clone https://github.com/kvsankar/blog.git
   cd blog
   git submodule add https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod
   ```

3. Run locally:
   ```bash
   hugo server -D
   ```
   Open http://localhost:1313/blog/

## Writing Posts

Create a new post:
```bash
hugo new posts/my-new-post.md
```

Edit `content/posts/my-new-post.md`, set `draft: false` when ready.

## Images

Store images in `static/images/` and reference them:
```markdown
![Alt text](/blog/images/my-image.jpg)
```

For Medium cross-posting, use full GitHub raw URLs:
```markdown
![Alt text](https://raw.githubusercontent.com/kvsankar/blog/main/static/images/my-image.jpg)
```

## Deployment

Push to `main` branch. GitHub Actions will build and deploy automatically.

## Cross-posting to Medium

```bash
cd scripts
pip install -r requirements.txt
export MEDIUM_TOKEN="your-token"
python publish_to_medium.py ../content/posts/my-post.md
```

Get your Medium token at: https://medium.com/me/settings/security
