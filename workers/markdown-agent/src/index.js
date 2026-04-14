/**
 * Markdown for Agents — Cloudflare Worker
 *
 * Converts article HTML to Markdown when agents request Accept: text/markdown.
 * Uses regex-based conversion optimized for this project's HTML structure.
 */

function wantsMarkdown(request) {
  const accept = request.headers.get("Accept") || "";
  return accept.includes("text/markdown");
}

function estimateTokens(text) {
  return Math.ceil(text.length / 4);
}

function extractMeta(html) {
  const title = html.match(/<title>([^<]+)<\/title>/i)?.[1] || "";
  const description =
    html.match(/<meta\s+name="description"\s+content="([^"]*)"/i)?.[1] || "";
  const author =
    html.match(/<meta\s+name="author"\s+content="([^"]*)"/i)?.[1] || "";
  const lang =
    html.match(/<html[^>]*\slang="([^"]+)"/i)?.[1] || "pt-BR";
  return { title, description, author, lang };
}

function extractArticleHtml(html) {
  const match = html.match(/<article[^>]*>([\s\S]*?)<\/article>/i);
  return match ? match[1] : null;
}

function htmlToMarkdown(articleHtml) {
  let md = articleHtml;

  // Remove elements we don't want
  md = md.replace(/<div class="theme-bar">[\s\S]*?<\/div>/gi, "");
  md = md.replace(/<a[^>]*class="back-home"[^>]*>[\s\S]*?<\/a>/gi, "");
  md = md.replace(/<div[^>]*class="progress[^"]*"[^>]*>[\s\S]*?<\/div>/gi, "");
  md = md.replace(/<div[^>]*class="reading-pct[^"]*"[^>]*>[\s\S]*?<\/div>/gi, "");
  md = md.replace(/<div[^>]*class="resume-banner[^"]*"[^>]*>[\s\S]*?<\/div>/gi, "");
  md = md.replace(/<a[^>]*class="back-top"[^>]*>[\s\S]*?<\/a>/gi, "");
  md = md.replace(/<script[\s\S]*?<\/script>/gi, "");
  md = md.replace(/<style[\s\S]*?<\/style>/gi, "");
  md = md.replace(/<nav[\s\S]*?<\/nav>/gi, "");
  md = md.replace(/<button[\s\S]*?<\/button>/gi, "");

  // Remove header block (title + meta already in frontmatter)
  md = md.replace(/<header[\s\S]*?<\/header>/gi, "");

  // Convert headings
  md = md.replace(/<h1[^>]*>([\s\S]*?)<\/h1>/gi, "# $1\n\n");
  md = md.replace(/<h2[^>]*>([\s\S]*?)<\/h2>/gi, "## $1\n\n");
  md = md.replace(/<h3[^>]*>([\s\S]*?)<\/h3>/gi, "### $1\n\n");

  // Convert figures/slides
  md = md.replace(
    /<figure[^>]*class="slide-figure"[^>]*>[\s\S]*?<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>[\s\S]*?<\/figure>/gi,
    "\n\n![$2]($1)\n\n"
  );

  // Convert links
  md = md.replace(/<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)<\/a>/gi, "[$2]($1)");

  // Convert cite
  md = md.replace(/<cite>([\s\S]*?)<\/cite>/gi, "*$1*");

  // Convert paragraphs
  md = md.replace(/<p[^>]*>([\s\S]*?)<\/p>/gi, "$1\n\n");

  // Convert emphasis
  md = md.replace(/<strong>([\s\S]*?)<\/strong>/gi, "**$1**");
  md = md.replace(/<em>([\s\S]*?)<\/em>/gi, "*$1*");
  md = md.replace(/<b>([\s\S]*?)<\/b>/gi, "**$1**");
  md = md.replace(/<i>([\s\S]*?)<\/i>/gi, "*$1*");

  // Convert lists
  md = md.replace(/<li[^>]*>([\s\S]*?)<\/li>/gi, "- $1\n");
  md = md.replace(/<\/?[ou]l[^>]*>/gi, "\n");

  // Convert blockquotes
  md = md.replace(/<blockquote[^>]*>([\s\S]*?)<\/blockquote>/gi, (_, content) => {
    return content.trim().split("\n").map((l) => `> ${l.trim()}`).join("\n") + "\n\n";
  });

  // Convert <br>
  md = md.replace(/<br\s*\/?>/gi, "\n");

  // Strip remaining HTML tags
  md = md.replace(/<[^>]+>/g, "");

  // Decode common HTML entities
  md = md.replace(/&ldquo;/g, "\u201c");
  md = md.replace(/&rdquo;/g, "\u201d");
  md = md.replace(/&amp;/g, "&");
  md = md.replace(/&lt;/g, "<");
  md = md.replace(/&gt;/g, ">");
  md = md.replace(/&nbsp;/g, " ");
  md = md.replace(/&#(\d+);/g, (_, code) => String.fromCharCode(parseInt(code)));

  // Clean up whitespace
  md = md.replace(/\n{3,}/g, "\n\n");
  md = md.trim();

  return md;
}

export default {
  async fetch(request, env, ctx) {
    // 301 redirect for legacy /leituras/ URLs
    const url = new URL(request.url);
    if (url.pathname.startsWith("/leituras/")) {
      const newPath = url.pathname.replace("/leituras/", "/posts/pt_br/");
      return Response.redirect(`${url.origin}${newPath}`, 301);
    }

    // 301 redirects for renamed canonical URLs
    const RENAMED = {
      "/posts/pt_br/akita-ia-prompt-fim-programador-bracal.html": "/posts/pt_br/fabio-akita-flow-588.html",
      "/posts/original/akita-ai-prompts-end-of-grunt-work-programming.html": "/posts/original/fabio-akita-flow-588.html",
    };
    if (RENAMED[url.pathname]) {
      return Response.redirect(`${url.origin}${RENAMED[url.pathname]}`, 301);
    }

    if (!wantsMarkdown(request)) {
      return fetch(request);
    }

    const originRequest = new Request(request.url, {
      headers: { Accept: "text/html" },
    });
    const response = await fetch(originRequest);

    if (!response.ok) {
      return response;
    }

    const contentType = response.headers.get("Content-Type") || "";
    if (!contentType.includes("text/html")) {
      return response;
    }

    const html = await response.text();
    const meta = extractMeta(html);
    const articleHtml = extractArticleHtml(html);

    if (!articleHtml) {
      return new Response("No article content found", { status: 404 });
    }

    const markdown = htmlToMarkdown(articleHtml);

    const lines = [];
    lines.push("---");
    if (meta.title) lines.push(`title: "${meta.title}"`);
    if (meta.author) lines.push(`author: "${meta.author}"`);
    if (meta.description) lines.push(`description: "${meta.description}"`);
    lines.push(`source: "${request.url}"`);
    lines.push(`lang: ${meta.lang}`);
    lines.push("---");
    lines.push("");
    lines.push(markdown);

    const finalMarkdown = lines.join("\n");
    const tokens = estimateTokens(finalMarkdown);

    return new Response(finalMarkdown, {
      status: 200,
      headers: {
        "Content-Type": "text/markdown; charset=utf-8",
        "x-markdown-tokens": String(tokens),
        "Vary": "Accept",
        "Cache-Control": "public, max-age=3600",
        "Access-Control-Allow-Origin": "*",
      },
    });
  },
};
