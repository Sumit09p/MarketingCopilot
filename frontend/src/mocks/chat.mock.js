import { ApiError } from "../services/apiClient";
import { delay } from "./delay";
import { conversations, messagesByConversation } from "./conversations.mock";

function ensureConversation(conversationId) {
  if (conversationId) return conversationId;

  const created = {
    id: `conversation_${Date.now()}`,
    title: "New Marketing Campaign",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  conversations.unshift(created);
  messagesByConversation[created.id] = [];

  return created.id;
}

function appendMessages(conversationId, userText, assistantText) {
  const now = new Date().toISOString();
  const thread = messagesByConversation[conversationId] ?? [];

  const userMessage = {
    id: `message_${Date.now()}`,
    role: "user",
    content: userText,
    created_at: now,
  };

  const assistantMessage = {
    id: `message_${Date.now() + 1}`,
    role: "assistant",
    content: assistantText,
    created_at: now,
  };

  thread.push(userMessage, assistantMessage);
  messagesByConversation[conversationId] = thread;

  const conversation = conversations.find(
    (item) => item.id === conversationId
  );

  if (conversation) {
    conversation.updated_at = now;
  }

  return assistantMessage;
}

function generateMarketingResponse(message) {
  const text = (message || "").toLowerCase();

  if (text.includes("seo")) {
    return `## SEO Strategy

### Target Keywords
- coffee shop Mumbai
- best coffee near me
- premium coffee Mumbai
- specialty coffee Mumbai
- cafes in Mumbai

### On-Page SEO
- Optimize title and meta description
- Create location-specific landing pages
- Add structured headings and internal links
- Optimize images with descriptive alt text

### Content Ideas
1. Best coffee drinks to try in Mumbai
2. Guide to specialty coffee
3. Coffee shop ambience and experience
4. Coffee brewing tips

### Recommendation
Focus on local SEO, Google Business visibility, reviews, and location-based keywords to attract nearby customers.`;
  }

  if (text.includes("competitor")) {
    return `## Competitor Analysis

### Key Competitor Types
1. Premium coffee chains
2. Independent specialty cafes
3. Local neighbourhood cafes
4. Delivery-first coffee brands

### Competitive Factors
- Pricing
- Location
- Product variety
- Customer experience
- Instagram presence
- Reviews and ratings

### Opportunity
Differentiate through a strong local identity, unique signature drinks, loyalty offers, user-generated content, and consistent social media branding.

### Recommended Action
Track competitor promotions, engagement, customer reviews, and content themes every week.`;
  }

  if (
    text.includes("instagram") ||
    text.includes("social media") ||
    text.includes("campaign")
  ) {
    return `## Social Media Marketing Campaign

### Campaign
**Mumbai Coffee Launch**

### Target Audience
- College students
- Young professionals
- Coffee enthusiasts
- Local residents aged 18–35

### Platforms
- Instagram
- Facebook
- WhatsApp
- Google Business Profile

### Content Plan
1. Launch announcement
2. Signature coffee reel
3. Behind-the-scenes content
4. Customer testimonial
5. Limited-time offer

### Sample Caption
"Your new coffee ritual has arrived in Mumbai ☕  
Freshly brewed. Carefully crafted. Made for your everyday moments."

### Hashtags
#MumbaiCoffee #CoffeeLovers #MumbaiCafe #CoffeeCulture #CafeLife

### Recommendation
Use short-form video, local hashtags, customer-generated content, and limited-time offers to drive awareness and visits.`;
  }

  if (text.includes("analytics") || text.includes("performance")) {
    return `## Marketing Analytics Report

### Key Metrics
- Reach
- Engagement rate
- Click-through rate
- Conversion rate
- Cost per acquisition
- Return on ad spend

### Analysis
Monitor which campaigns generate the highest engagement and conversions. Compare organic and paid channels to identify the most efficient sources of customers.

### Recommendations
1. Increase investment in high-converting channels.
2. Test multiple creative variations.
3. Retarget engaged users.
4. Track conversions rather than impressions alone.
5. Review campaign performance weekly.`;
  }

  return `## Marketing Strategy

### Business
New Coffee Shop in Mumbai

### Target Audience
- Young professionals
- College students
- Coffee enthusiasts
- Local residents

### Marketing Channels
- Instagram
- Google Search
- Google Business Profile
- WhatsApp
- Local influencer collaborations

### Content Strategy
1. Product photography and reels
2. Behind-the-scenes content
3. Customer testimonials
4. Educational coffee content
5. Promotional offers

### 30-Day Plan
**Week 1:** Brand awareness and launch content  
**Week 2:** Product-focused reels and stories  
**Week 3:** Influencer and customer-generated content  
**Week 4:** Promotional campaign and performance analysis

### Recommendation
Focus on local SEO, Instagram Reels, customer reviews, influencer collaborations, and targeted local advertising.

### Expected Outcome
Build local awareness, increase engagement, generate website/store visits, and convert nearby customers.`;
}

export async function sendMessage({ conversation_id, message }) {
  await delay();

  const conversationId = ensureConversation(conversation_id);
  const reply = generateMarketingResponse(message);

  const assistantMessage = appendMessages(
    conversationId,
    message,
    reply
  );

  return {
    conversation_id: conversationId,
    message_id: assistantMessage.id,
    response: reply,
    mode: "GENERAL",
    status: "COMPLETED",
  };
}

function looksLikeUrl(text) {
  return /https?:\/\/|www\./i.test(text);
}

function generateAgentResponse(agent, message) {
  switch (agent) {
    case "content":
      return `## Content Agent Result

### Content Strategy
Created a content plan based on your request.

### Content Types
- Social media posts
- Short-form video
- Promotional creatives
- Educational content
- Customer testimonials

### Suggested Workflow
Research → Content Generation → Review → Publish → Analyze`;

    case "seo":
      return `## SEO Agent Result

### SEO Recommendations
- Keyword research
- On-page optimization
- Local SEO
- Technical SEO
- Content optimization
- Performance tracking

### Priority
Start with local and high-intent keywords, then build supporting content around them.`;

    case "competitor":
      return `## Competitor Agent Result

### Competitive Analysis
Analyzed the major competitive factors relevant to the request.

### Factors
- Pricing
- Positioning
- Content strategy
- Customer reviews
- Social media engagement
- Promotional offers

### Recommendation
Identify competitor gaps and position the brand around a clear differentiator.`;

    case "research":
      return `## Research Agent Result

### Market Research
The target market can be segmented by demographics, interests, location, buying behaviour, and customer intent.

### Recommended Segments
- Young professionals
- Students
- Local residents
- Enthusiasts

### Next Step
Use these segments to build targeted campaigns and personalized content.`;

    case "analytics":
      return `## Analytics Agent Result

### Performance Metrics
- Reach
- Engagement
- CTR
- Conversion rate
- CAC
- ROAS

### Recommendation
Compare campaign performance across channels and allocate budget toward the highest-converting segments.`;

    case "recommendation":
      return `## Recommendation Agent Result

### Recommended Channels
1. Instagram
2. Google Search
3. Google Business Profile
4. WhatsApp
5. Local influencer marketing

### Priority
Start with local discovery and social engagement, then optimize based on conversion data.`;

    default:
      return generateMarketingResponse(message);
  }
}

export async function sendAgentMessage({
  agent,
  message,
  conversation_id,
}) {
  await delay();

  const text = (message || "").toLowerCase();

  if (text.includes("capital of") || text.includes("birthday")) {
    throw new ApiError(
      `This request is not appropriate for the ${agent} Agent.`,
      {
        status: 400,
        data: { agent, guardrail: "INVALID" },
      }
    );
  }

  if (agent === "seo" && !looksLikeUrl(message || "")) {
    return {
      agent,
      guardrail: "NEEDS_CLARIFICATION",
      question: "Please provide your website URL.",
    };
  }

  const conversationId = ensureConversation(conversation_id);
  const reply = generateAgentResponse(agent, message);

  const assistantMessage = appendMessages(
    conversationId,
    message,
    reply
  );

  return {
    agent,
    conversation_id: conversationId,
    message_id: assistantMessage.id,
    response: assistantMessage.content,
    guardrail: "VALID",
    status: "COMPLETED",
  };
}