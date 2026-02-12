#!/bin/bash
# Verify RSS feeds - output: OK/FAIL + status code + first tag found

verify() {
    local name="$1" url="$2"
    local resp=$(curl -sL -o /dev/null -w "%{http_code}" --max-time 10 -A "Mozilla/5.0 (compatible; Newsbot/1.0)" "$url" 2>/dev/null)
    local content=$(curl -sL --max-time 10 -A "Mozilla/5.0 (compatible; Newsbot/1.0)" "$url" 2>/dev/null | head -5)
    local has_rss=$(echo "$content" | grep -ciE '<rss|<feed|<atom|xml')
    if [ "$resp" = "200" ] && [ "$has_rss" -gt 0 ]; then
        echo "✅ $name ($resp)"
    elif [ "$resp" = "200" ]; then
        echo "⚠️  $name ($resp, no RSS tags)"
    else
        echo "❌ $name ($resp)"
    fi
}

echo "=== P0: AI Company Official Blogs ==="
verify "Anthropic Blog" "https://www.anthropic.com/rss.xml"
verify "Anthropic Blog /feed" "https://www.anthropic.com/feed"
verify "Anthropic Blog /blog/rss" "https://www.anthropic.com/blog/rss"
verify "OpenAI Blog" "https://openai.com/blog/rss.xml"
verify "OpenAI Blog /feed" "https://openai.com/blog/feed/"
verify "OpenAI Index" "https://openai.com/index/rss.xml"
verify "Google AI Blog" "https://blog.google/technology/ai/rss/"
verify "DeepMind Blog" "https://deepmind.google/blog/rss.xml"
verify "DeepMind /discover/blog" "https://www.deepmind.com/blog/feed/basic"
verify "Meta AI Blog" "https://ai.meta.com/blog/rss/"
verify "Meta AI /feed" "https://ai.meta.com/feed/"
verify "Microsoft Research" "https://www.microsoft.com/en-us/research/feed/"
verify "Cursor Blog" "https://www.cursor.com/blog/rss.xml"
verify "Cursor /feed" "https://cursor.com/feed"
verify "Cursor changelog" "https://changelog.cursor.com/feed.xml"
verify "HuggingFace Blog" "https://huggingface.co/blog/feed.xml"
verify "Mistral AI" "https://mistral.ai/feed.xml"
verify "Mistral News" "https://mistral.ai/news/feed.xml"
verify "NVIDIA AI Blog" "https://blogs.nvidia.com/feed/"
verify "NVIDIA AI /ai/feed" "https://blogs.nvidia.com/blog/category/deep-learning/feed/"
verify "Stability AI" "https://stability.ai/news/feed"
verify "Cohere Blog" "https://cohere.com/blog/rss.xml"
verify "Cohere /feed" "https://cohere.com/blog/feed"
verify "Vercel Blog" "https://vercel.com/atom"
verify "Vercel /feed" "https://vercel.com/blog/feed"

echo ""
echo "=== P1: Tech Media ==="
verify "Ars Technica" "https://feeds.arstechnica.com/arstechnica/index"
verify "Wired" "https://www.wired.com/feed/rss"
verify "Lobsters" "https://lobste.rs/rss"
verify "Dev.to AI" "https://dev.to/feed/tag/ai"
verify "InfoQ" "https://www.infoq.com/feed/"
verify "36kr" "https://36kr.com/feed"
verify "机器之心" "https://www.jiqizhixin.com/rss"
verify "量子位" "https://www.qbitai.com/feed"
verify "The Gradient" "https://thegradient.pub/rss/"
verify "Import AI" "https://importai.substack.com/feed"
verify "Simon Willison" "https://simonwillison.net/atom/everything/"
verify "Lil'Log (Lilian Weng)" "https://lilianweng.github.io/index.xml"
verify "Jack Clark / Import AI" "https://jack-clark.net/feed/"

echo ""
echo "=== P2: Crypto ==="
verify "The Block" "https://www.theblock.co/rss.xml"
verify "Bankless" "https://www.bankless.com/feed"
verify "Rekt News" "https://rekt.news/feed.xml"
verify "DeFi Llama" "https://defillama.com/feed"
verify "The Defiant" "https://thedefiant.io/feed"
verify "Unchained" "https://unchainedcrypto.com/feed/"
verify "Wu Blockchain" "https://wublock.substack.com/feed"

echo ""
echo "=== P3: Finance ==="
verify "Bloomberg" "https://www.bloomberg.com/feed/podcast/etf-iq.xml"
verify "FT" "https://www.ft.com/rss/home"
verify "WSJ" "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"
verify "Seeking Alpha" "https://seekingalpha.com/feed.xml"
verify "ZeroHedge" "https://feeds.feedburner.com/zerohedge/feed"
verify "Benzinga" "https://www.benzinga.com/feed"
verify "MarketWatch" "https://www.marketwatch.com/rss/"
