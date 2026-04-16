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
  redirects: {
    "/leituras/*": "/posts/pt_br/$1",
    "/posts/pt_br/akita-ia-prompt-fim-programador-bracal.html":
      "/posts/pt_br/fabio-akita-flow-588.html",
    "/posts/original/akita-ai-prompts-end-of-grunt-work-programming.html":
      "/posts/original/fabio-akita-flow-588.html",
  },
});
