import { createMarkdownWorker } from "@adhenawer-pkg/markdown-edge-for-agents";

export default createMarkdownWorker({
  preset: "custom",
  selector: "article",
  strip: [
    ".theme-bar",
    ".back-home",
    ".progress",
    ".reading-pct",
    ".resume-banner",
    ".back-top",
    "script",
    "style",
    "nav",
    "button",
    "header",
  ],
  frontmatter: ["title", "author", "description", "lang"],
  autoDetectAiCrawlers: true,
  redirects: {
    "/leituras/*": "/posts/pt_br/$1",
  },
});
